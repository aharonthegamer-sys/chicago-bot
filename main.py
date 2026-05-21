import discord
from discord.ext import commands, tasks
from discord.ui import Button, View, Select, Modal, TextInput, UserSelect
import asyncio, datetime, os, random, aiohttp, socket
from flask import Flask
from threading import Thread

app = Flask('')
@app.route('/')
def home(): return "Chicago City BOT is running 24/7!"
def run(): app.run(host='0.0.0.0', port=8080)
def keep_alive(): Thread(target=run).start()

intents = discord.Intents.default()
intents.message_content = intents.members = intents.guilds = intents.messages = intents.presences = True
intents.invites = True
bot = commands.Bot(command_prefix="!", intents=intents)

# איידיז קבועים — CHICAGO CITY
ROLE_VERIFIED = 1483039214793789489
ROLE_STAFF = 1483039215364345930
ROLE_WARN_ADMIN = 1483039215393702012 

CHANNEL_GIVEAWAY_PANEL = 1507022943413342328 
CHANNEL_GIVEAWAY_PUBLIC = 1483039216366780532 
CHANNEL_WARN_PANEL = 1507023136095207515 
CHANNEL_STAFF_WARNS_LOG = 1483039219336347810 
CHANNEL_FIVEM_STATUS = 1506965475270332476 
CHANNEL_TICKET_LOGS = 1483039219654852612
CHANNEL_INVITE_LOGS = 1506417177719210194 

FIVEM_IP_ONLY = "135.148.36.192"
FIVEM_PORT_ONLY = 30125
CFX_ID = "rmadb7p"

LOG_CHANNELS = {
    "channel_create": 1483039219654852617, "channel_delete": 1483039219654852616,
    "channel_update": 1483039219923554468, "ban": 1483039219923554469,
    "unban": 1483039219923554470, "role_create": 1483039219923554471,
    "role_delete": 1483039219923554472, "message_edit": 1483039219923554473,
    "message_delete": 1483039219923554474, "welcome_embed": 1504124994999943269,
    "security": 1483039220284002367
}

staff_warns_db, invites_cache = {}, {}
fivem_msg_id = None

async def send_log(event_name, embed):
    ch_id = LOG_CHANNELS.get(event_name)
    if ch_id:
        channel = bot.get_channel(ch_id)
        if channel: await channel.send(embed=embed)

# מערכת אימות בעיצוב נקי
class VerifyView(View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="🛡️ לחצו כאן לאימות המשתמש", style=discord.ButtonStyle.green, custom_id="verify_btn")
    async def verify_button(self, interaction: discord.Interaction, button: Button):
        await interaction.response.defer(ephemeral=True)
        role = interaction.guild.get_role(ROLE_VERIFIED)
        if role in interaction.user.roles: await interaction.followup.send("הנך כבר מאומת במערכת השרת.", ephemeral=True)
        else:
            await interaction.user.add_roles(role)
            await interaction.followup.send("תהליך האימות הושלם בהצלחה. ברוך הבא ל-Chicago City! 🎉", ephemeral=True)

@bot.command()
@commands.has_permissions(administrator=True)
async def setup_verify(ctx):
    embed = discord.Embed(title="CHICAGO CITY ➔ VERIFICATION", description="כדי לקבל גישה מלאה לאזרחי העיר, אנא לחצו על כפתור האבטחה למטה.", color=discord.Color.from_rgb(46, 204, 113))
    embed.set_footer(text="Chicago City • Secure System")
    if ctx.guild.icon: embed.set_image(url=ctx.guild.icon.url)
    await ctx.send(embed=embed, view=VerifyView())

# מערכת טיקטים משודרגת בסגנון PRRP
class TicketControls(View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="🙋‍♂️ קח טיפול", style=discord.ButtonStyle.blurple, custom_id="tk_claim")
    async def claim(self, interaction: discord.Interaction, button: Button):
        await interaction.response.defer()
        if interaction.guild.get_role(ROLE_STAFF) not in interaction.user.roles and not interaction.user.guild_permissions.administrator: return
        await interaction.channel.send(f"🔒 **הפנייה ננעלה בטיפולו הרשמי של:** {interaction.user.mention}")
        log_ch = bot.get_channel(CHANNEL_TICKET_LOGS)
        if log_ch: await log_ch.send(embed=discord.Embed(title="CHICAGO CITY ➔ TICKET CLAIMED", description=f"**חדר פנייה:** {interaction.channel.mention}\n**נציג מטפל:** {interaction.user.mention}", color=discord.Color.blue()))
        button.disabled = True; await interaction.message.edit(view=self)

    @discord.ui.button(label="📝 שנה שם", style=discord.ButtonStyle.grey, custom_id="tk_rename")
    async def rename(self, interaction: discord.Interaction, button: Button):
        if interaction.guild.get_role(ROLE_STAFF) not in interaction.user.roles and not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message("❌ אין לך הרשאה לבצע פעולה זו!", ephemeral=True)
        await interaction.response.send_message("⌨️ אנא הקלד את השם החדש לערוץ הטיקט בצ'אט:", ephemeral=True)
        def check(m): return m.author == interaction.user and m.channel == interaction.channel
        try:
            msg = await bot.wait_for('message', check=check, timeout=30)
            await interaction.channel.edit(name=f"ticket-{msg.content}")
            await interaction.channel.send(f"⚙️ **שם הערוץ שונה בהצלחה ל:** `ticket-{msg.content}`")
        except asyncio.TimeoutError: await interaction.channel.send("❌ פג הזמן הקצוב לעריכת השם.")

    @discord.ui.button(label="➕ הוסף משתמש", style=discord.ButtonStyle.green, custom_id="tk_add_member")
    async def add_member(self, interaction: discord.Interaction, button: Button):
        if interaction.guild.get_role(ROLE_STAFF) not in interaction.user.roles and not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message("❌ אין לך הרשאה לבצע פעולה זו!", ephemeral=True)
        await interaction.response.send_message("👤 אנא תייג את המשתמש שברצונך להוסיף לטיקט הנוכחי:", ephemeral=True)
        def check(m): return m.author == interaction.user and m.channel == interaction.channel
        try:
            msg = await bot.wait_for('message', check=check, timeout=30)
            if msg.mentions:
                target = msg.mentions
                await interaction.channel.set_permissions(target, read_messages=True, send_messages=True)
                await interaction.channel.send(f"✅ **המשתמש** {target.mention} **צורף בהצלחה לפנייה.**")
            else: await interaction.channel.send("❌ לא תוייג משתמש תקין. הפעולה בוטלה.")
        except asyncio.sleep: await interaction.channel.send("❌ פג הזמן הקצוב.")

    @discord.ui.button(label="❌ סגור פנייה", style=discord.ButtonStyle.red, custom_id="tk_close")
    async def close(self, interaction: discord.Interaction, button: Button):
        await interaction.response.defer()
        if interaction.guild.get_role(ROLE_STAFF) not in interaction.user.roles and not interaction.user.guild_permissions.administrator: return
        await interaction.channel.send("⚠️ **ערוץ הפנייה יימחק לצמיתות בעוד 5 שניות...**")
        log_ch = bot.get_channel(CHANNEL_TICKET_LOGS)
        if log_ch: await log_ch.send(embed=discord.Embed(title="CHICAGO CITY ➔ TICKET CLOSED", description=f"**שם חדר:** `{interaction.channel.name}`\n**נסגר על ידי:** {interaction.user.mention}", color=discord.Color.red()))
        await asyncio.sleep(5); await interaction.channel.delete()

class TicketDropdown(Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="דיווח על איש צוות / שחקן", emoji="🚫", value="דיווח"),
            discord.SelectOption(label="בחינה לצוות", emoji="📝", value="בחינה לצוות"),
            discord.SelectOption(label="דיווח על באג במערכת", emoji="🐛", value="דיווח באג"),
            discord.SelectOption(label="שאלה כללית ועזרה", emoji="❓", value="שאלה כללית")
        ]
        super().__init__(placeholder="אנא בחרו את קטגוריית הפנייה... 🎫", options=options, custom_id="tk_select")

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        ticket_channel = await interaction.guild.create_text_channel(name=f"ticket-{interaction.user.name}", category=interaction.channel.category)
        await ticket_channel.set_permissions(interaction.guild.default_role, read_messages=False)
        await ticket_channel.set_permissions(interaction.user, read_messages=True, send_messages=True)
        await ticket_channel.set_permissions(interaction.guild.get_role(ROLE_STAFF), read_messages=True, send_messages=True)
        await interaction.followup.send(f"✅ הפנייה נוצרה. מעבר לערוץ: {ticket_channel.mention}", ephemeral=True)
        
        log_ch = bot.get_channel(CHANNEL_TICKET_LOGS)
        if log_ch: await log_ch.send(embed=discord.Embed(title="CHICAGO CITY ➔ TICKET CREATED", description=f"**פותח הפנייה:** {interaction.user.mention}\n**נושא:** `{self.values}`\n**חדר:** {ticket_channel.mention}", color=discord.Color.green()))
            
        embed = discord.Embed(title="CHICAGO CITY ➔ SUPPORT", description=f"שלום {interaction.user.mention},\nפנייתך בנושא `{self.values}` נפתחה בהצלחה.\nצוות הניהול יתייצב בתוך דקות ספורות.", color=discord.Color.red())
        embed.set_footer(text="Chicago City • Support Desk")
        if interaction.guild.icon: embed.set_image(url=interaction.guild.icon.url)
        await ticket_channel.send(embed=embed, view=TicketControls())
        p = await ticket_channel.send(f"<@&{ROLE_STAFF}>"); await p.delete()

@bot.command()
@commands.has_permissions(administrator=True)
async def setup_tickets(ctx):
    embed = discord.Embed(title="CHICAGO CITY ➔ SUPPORT CENTER", description="זקוקים לעזרה, נתקלתם בבאג או רוצים לדווח על שחקן?\nאנא בחרו את הנושא המתאים בתפריט למטה.", color=discord.Color.purple())
    embed.set_footer(text="Chicago City • Helpdesk")
    if ctx.guild.icon: embed.set_image(url=ctx.guild.icon.url)
    await ctx.send(embed=embed, view=View().add_item(TicketDropdown()))
# --- מערכת הגרלות מתקדמת מבוססת פאנל וטפסים (GIVEAWAY MODAL SYSTEM) ---
class GiveawayModal(Modal):
    def __init__(self):
        super().__init__(title="יצירת הגרלה חדשה — Chicago City")
        self.prize = TextInput(label="מה הפרס של ההגרלה?", placeholder="לדוגמה: 500,000$ / רכב ספורט", required=True)
        self.time = TextInput(label="זמן ריצה (בדקות)", placeholder="לדוגמה: 10", required=True)
        self.winners = TextInput(label="כמות זוכים מוגדרת", placeholder="לדוגמה: 1", required=True)
        self.add_item(self.prize)
        self.add_item(self.time)
        self.add_item(self.winners)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        try:
            duration = int(self.time.value)
            winners_count = int(self.winners.value)
        except ValueError:
            return await interaction.followup.send("❌ שגיאה: נא להזין מספרים תקינים בשדות הזמן והזוכים!", ephemeral=True)

        public_ch = bot.get_channel(CHANNEL_GIVEAWAY_PUBLIC)
        if not public_ch: return await interaction.followup.send("❌ שגיאה: ערוץ ההגרלות הציבורי לא נמצא.", ephemeral=True)

        embed = discord.Embed(title="CHICAGO CITY ➔ GIVEAWAY", color=discord.Color.gold())
        embed.description = f"┃ 🏆 **פרס הטורניר:** `{self.prize.value}`\n" \
                            f"┃ 👥 **כמות זוכים:** `{winners_count}`\n" \
                            f"┃ ⏱️ **זמן לסיום:** `{duration}` דקות\n\n" \
                            f"לחצו על כפתור התגובה למטה כדי להשתתף בהגרלה!"
        embed.set_footer(text="Chicago City • Luck System")
        if interaction.guild.icon: embed.set_thumbnail(url=interaction.guild.icon.url)

        view = AdvancedGiveawayView(self.prize.value, winners_count)
        msg = await public_ch.send(embed=embed, view=view)
        await interaction.followup.send(f"✅ ההגרלה נוצרה ופורסמה בהצלחה בערוץ {public_ch.mention}!", ephemeral=True)

        await asyncio.sleep(duration * 60)
        if view.active:
            view.active = False
            await end_gv(public_ch, self.prize.value, winners_count, view.entrants, msg)

class GiveawayPanelView(View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="🎁 צור הגרלה חדשה", style=discord.ButtonStyle.green, custom_id="gv_panel_btn")
    async def create_gv(self, interaction: discord.Interaction, button: Button):
        if interaction.guild.get_role(ROLE_STAFF) not in interaction.user.roles and not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message("❌ אין לך הרשאה לפתוח פאנל זה!", ephemeral=True)
        await interaction.response.send_modal(GiveawayModal())

class AdvancedGiveawayView(View):
    def __init__(self, prize, winners):
        super().__init__(timeout=None)
        self.prize, self.winners, self.entrants, self.active = prize, winners, [], True
    @discord.ui.button(label="🎉 הצטרף להגרלה", style=discord.ButtonStyle.green, custom_id="gv_join")
    async def join(self, interaction: discord.Interaction, b: Button):
        await interaction.response.defer(ephemeral=True)
        if not self.active: return await interaction.followup.send("❌ ההגרלה כבר הגיעה לסיומה!", ephemeral=True)
        if interaction.user.id in self.entrants: return await interaction.followup.send("הנך כבר רשום במערכת ההגרלה! 🍀", ephemeral=True)
        self.entrants.append(interaction.user.id)
        await interaction.followup.send("✅ נרשמת בהצלחה! בהצלחה בהגרלה.", ephemeral=True)

    @discord.ui.button(label="📈 משתתפים", style=discord.ButtonStyle.grey, custom_id="gv_status")
    async def status(self, interaction: discord.Interaction, b: Button):
        await interaction.response.defer(ephemeral=True)
        await interaction.followup.send(f"כמות המשתתפים הרשומים כרגע: `{len(self.entrants)}`", ephemeral=True)

    @discord.ui.button(label="⏱️ סגור כעת", style=discord.ButtonStyle.red, custom_id="gv_end_now")
    async def end_early(self, interaction: discord.Interaction, b: Button):
        await interaction.response.defer()
        if interaction.guild.get_role(ROLE_STAFF) not in interaction.user.roles: return
        self.active = False; await end_gv(interaction.channel, self.prize, self.winners, self.entrants, interaction.message)

async def end_gv(channel, prize, winners, entrants, msg):
    if len(entrants) < winners: await msg.edit(embed=discord.Embed(title="CHICAGO CITY ➔ GIVEAWAY", description="ההגרלה בוטלה באופן אוטומטי עקב חוסר משתתפים.", color=discord.Color.red()), view=None)
    else:
        w = random.sample(entrants, winners); m = ", ".join([f"<@{x}>" for x in w])
        await msg.edit(embed=discord.Embed(title="CHICAGO CITY ➔ GIVEAWAY ENDED", description=f"🏆 **הפרס המנצח:** `{prize}`\n👥 **הזוכים המאושרים:** {m}", color=discord.Color.green()), view=None)
        await channel.send(f"🎉 **מזל טוב לזוכים בהגרלה על {prize}!** {m}")

@bot.command()
@commands.has_permissions(administrator=True)
async def setup_giveaway_panel(ctx):
    embed = discord.Embed(title="CHICAGO CITY ➔ GIVEAWAY DASHBOARD", description="מערכת ניהול ויצירת ההגרלות הרשמית של הצוות.\nלחצו על הכפתור למטה כדי לפתוח את טופס ההגרלה החדש.", color=discord.Color.green())
    embed.set_footer(text="Chicago City Staff Console")
    await ctx.send(embed=embed, view=GiveawayPanelView())

# --- פאנל אזהרות משודרג מבוסס בחירת תיוג @ ישירה (WARN PANEL USER SELECT) ---
class StaffSelectReasonModal(Modal):
    def __init__(self, target_member):
        super().__init__(title="סיבת האזהרה — Chicago City")
        self.target = target_member
        self.reason = TextInput(label="אנא הקלד את סיבת האזהרה", placeholder="לדוגמה: חוסר כבוד / אביוז דרגות", required=True)
        self.add_item(self.reason)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        tid = self.target.id
        if tid not in staff_warns_db: staff_warns_db[tid] = []
        t = datetime.datetime.now().strftime("%d/%m/%Y | %H:%M")
        staff_warns_db[tid].append({"reason": self.reason.value, "by": interaction.user.id, "date": t})
        count = len(staff_warns_db[tid])

        log_ch = bot.get_channel(CHANNEL_STAFF_WARNS_LOG)
        if log_ch:
            embed = discord.Embed(title="CHICAGO CITY ➔ STAFF MANAGEMENT", color=discord.Color.red())
            embed.description = f"🚨 **רישום אזהרה משמעתית לחבר צוות**\n\n" \
                                f"┃ 👤 **העובד המוזהר:** {self.target.mention}\n" \
                                f"┃ 🛡️ **האדמין המעניש:** {interaction.user.mention}\n" \
                                f"┃ 📅 **מועד הרישום:** `{t}`\n" \
                                f"┃ 📝 **סיבת האירוע:**\n```fix\n{self.reason.value}```\n" \
                                f"┃ 📊 **תיק אזהרות אישי:** `{'🟥' * count + '⬛' * (3 - count)}` ({count}/3 אזהרות)"
            embed.set_footer(text="Chicago City Control Database")
            if interaction.guild.icon: embed.set_image(url=interaction.guild.icon.url)
            await log_ch.send(embed=embed)
        await interaction.followup.send(f"✅ האזהרה נרשמה בהצלחה ל-{self.target.mention}!", ephemeral=True)

class WarnUserSelect(UserSelect):
    def __init__(self, action_type):
        super().__init__(placeholder="אנא בחרו חבר צוות מהרשימה... 👤", min_values=1, max_values=1)
        self.action_type = action_type

    async def callback(self, interaction: discord.Interaction):
        target = self.values[0]
        if self.action_type == "add":
            await interaction.response.send_modal(StaffSelectReasonModal(target))
        elif self.action_type == "view":
            c = len(staff_warns_db.get(target.id, []))
            if c == 0: return await interaction.response.send_message(f"🟢 העובד {target.mention} נקי לחלוטין וללא אזהרות רשומות.", ephemeral=True)
            embed = discord.Embed(title=f"CHICAGO CITY ➔ WARN DOSSIER ({target.name})", color=discord.Color.orange())
            for i, w in enumerate(staff_warns_db[target.id], 1):
                embed.add_field(name=f"🚨 אזהרה {i} ➔ {w['date']}", value=f"• רשם: <@{w['by']}>\n• סיבה: {w['reason']}", inline=False)
            embed.set_footer(text="Chicago City Registry")
            await interaction.response.send_message(embed=embed, ephemeral=True)
        elif self.action_type == "remove":
            if target.id in staff_warns_db and len(staff_warns_db[target.id]) > 0:
                staff_warns_db[target.id].pop()
                await interaction.response.send_message(f"✅ האזהרה האחרונה של {target.mention} נמחקה מהתיק לצמיתות.", ephemeral=True)
            else: await interaction.response.send_message(f"❌ לא נמצאו אזהרות פעילות למחיקה עבור {target.mention}.", ephemeral=True)

class WarnPanelView(View):
    def __init__(self): super().__init__(timeout=None)
    
    @discord.ui.button(label="⚠️ רשום אזהרה למנהל", style=discord.ButtonStyle.red, custom_id="wp_add")
    async def add_warn_btn(self, interaction: discord.Interaction, button: Button):
        if interaction.guild.get_role(ROLE_WARN_ADMIN) not in interaction.user.roles and not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message("❌ אבטחה: פעולה זו מיועדת לדרג ניהול עליון בלבד!", ephemeral=True)
        view = View().add_item(WarnUserSelect("add"))
        await interaction.response.send_message("⚙️ בחרו את המנהל שברצונכם להעניש מהרשימה:", view=view, ephemeral=True)

    @discord.ui.button(label="📊 כמות ווארנים בתיק", style=discord.ButtonStyle.grey, custom_id="wp_view")
    async def view_warn_btn(self, interaction: discord.Interaction, button: Button):
        if interaction.guild.get_role(ROLE_WARN_ADMIN) not in interaction.user.roles and not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message("❌ אבטחה: פעולה זו מיועדת לדרג ניהול עליון בלבד!", ephemeral=True)
        view = View().add_item(WarnUserSelect("view"))
        await interaction.response.send_message("⚙️ בחרו חבר צוות כדי לצפות בגיליון המשמעת שלו:", view=view, ephemeral=True)

    @discord.ui.button(label="🔓 מחק אזהרה (Unwarn)", style=discord.ButtonStyle.green, custom_id="wp_remove")
    async def remove_warn_btn(self, interaction: discord.Interaction, button: Button):
        if interaction.guild.get_role(ROLE_WARN_ADMIN) not in interaction.user.roles and not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message("❌ אבטחה: פעולה זו מיועדת לדרג ניהול עליון בלבד!", ephemeral=True)
        view = View().add_item(WarnUserSelect("remove"))
        await interaction.response.send_message("⚙️ בחרו חבר צוות כדי לבטל לו את האזהרה האחרונה:", view=view, ephemeral=True)

@bot.command()
@commands.has_permissions(administrator=True)
async def setup_warn_panel(ctx):
    embed = discord.Embed(title="CHICAGO CITY ➔ WARNING SYSTEM CONTROL", description="פאנל אבטחה חסוי לניהול, בדיקה וסנכרון משמעת בצוות השרת.\nרק דרג ניהול עליון מורשה לבצע שינויים או לבצע רישומים.", color=discord.Color.red())
    embed.set_footer(text="Chicago City Internal Management Only")
    await ctx.send(embed=embed, view=WarnPanelView())

# מערכת הצעות מטורפת (SUGGESTIONS SYSTEM)
CHANNEL_SUGG_PANEL = 1507020507776811068
CHANNEL_SUGG_LOGS = 1483039217482334253

class SuggestionModal(Modal):
    def __init__(self):
        super().__init__(title="הגשת הצעה חדשה — Chicago City")
        self.sugg = TextInput(label="פרט את ההצעה שלך לעיר", style=discord.TextStyle.paragraph, placeholder="רשום כאן את הצעתך בצורה ברורה...", required=True)
        self.add_item(self.sugg)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        log_ch = bot.get_channel(CHANNEL_SUGG_LOGS)
        if not log_ch: return await interaction.followup.send("❌ ערוץ הלוגים של ההצעות לא נמצא.", ephemeral=True)
        
        embed = discord.Embed(title="CHICAGO CITY ➔ SUGGESTION FEED", color=discord.Color.blue())
        embed.description = f"💡 **הצעה חדשה הוגשה לשדרוג השרת!**\n\n```fix\n{self.sugg.value}```\n" \
                            f"┃ 👤 **הוגש על ידי:** {interaction.user.mention}"
        embed.set_footer(text="Chicago City • Feedback System")
        if interaction.guild.icon: embed.set_thumbnail(url=interaction.guild.icon.url)
        
        msg = await log_ch.send(embed=embed)
        await msg.add_reaction("👍")
        await msg.add_reaction("👎")
        await interaction.followup.send("✅ ההצעה שלך נשלחה בהצלחה לערוץ ההצעות ונוספו לה תגובות! תודה 🎉", ephemeral=True)

class SuggestionPanelView(View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="💡 לחצו להגשת הצעה חדשה", style=discord.ButtonStyle.blurple, custom_id="sugg_panel_btn")
    async def add_sugg(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_modal(SuggestionModal())

@bot.command()
@commands.has_permissions(administrator=True)
async def setup_suggestions(ctx):
    embed = discord.Embed(title="CHICAGO CITY ➔ CITY SUGGESTIONS", description="יש לכם רעיון מטורף לשדרוג העיר, הצעה לרכב חדש או מערכת שווה?\nלחצו על הכפתור הכחול למטה כדי לפתוח את טופס ההצעות הרשמי.", color=discord.Color.blue())
    embed.set_footer(text="Chicago City • Community Power")
    if ctx.guild.icon: embed.set_image(url=ctx.guild.icon.url)
    await ctx.send(embed=embed, view=SuggestionPanelView())

# פקודת say לצוות
@bot.command()
@commands.has_permissions(administrator=True)
async def say(ctx, channel: discord.TextChannel, em: str, *, content: str):
    embed = discord.Embed(description=content, color=discord.Color.blue()); embed.set_footer(text="Chicago City")
    await channel.send(embed=embed); await ctx.send("✅ ההכרזה נשלחה!")

# לוגים אוטומטיים
@bot.event
async def on_guild_channel_create(c): await send_log("channel_create", discord.Embed(title="Chicago City", description=f"🟢 ערוץ נוצר: {c.name}", color=discord.Color.green()))
@bot.event
async def on_guild_channel_delete(c): await send_log("channel_delete", discord.Embed(title="Chicago City", description=f"🔴 ערוץ נמחק: {c.name}", color=discord.Color.red()))
@bot.event
async def on_message_edit(b, a):
    if b.author.bot or b.content == a.content: return
    await send_log("message_edit", discord.Embed(title="Chicago City", description=f"📝 הודעה נערכה ע''י {b.author.mention}\nחדר: {b.channel.mention}\nישן: {b.content}\nחדש: {a.content}", color=discord.Color.gold()))
@bot.event
async def on_message_delete(m):
    if m.author.bot: return
    await send_log("message_delete", discord.Embed(title="Chicago City", description=f"🗑️ הודעה נמחקה ע''י {m.author.mention}\nחדר: {m.channel.mention}\nתוכן: {m.content}", color=discord.Color.red()))

# --- מנוע ה-INVITE TRACKER המטורף והמשודרג ברמת PRRP (PREMIUM AVATAR TRACKER) ---
async def fetch_invites(guild):
    try: return {invite.code: invite for invite in await guild.invites()}
    except: return {}

@bot.event
async def on_guild_join(guild):
    invites_cache[guild.id] = await fetch_invites(guild)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user.name}")
    for guild in bot.guilds: invites_cache[guild.id] = await fetch_invites(guild)
    if not update_fivem_status.is_running(): update_fivem_status.start()

@bot.event
async def on_member_join(member):
    # שולח וולקם כרגיל
    w_ch = bot.get_channel(LOG_CHANNELS["welcome_embed"])
    if w_ch:
        embed = discord.Embed(title="CHICAGO CITY ➔ WELCOME", description=f"💎 ברוך הבא לעיר, {member.name}! 💎\nאנא כנסו לערוץ האבטחה והשלימו את האימות: <#{ROLE_VERIFIED}> 🛡️", color=discord.Color.red())
        embed.set_thumbnail(url=member.display_avatar.url); embed.set_footer(text="Chicago City Administration")
        if member.guild.icon: embed.set_image(url=member.guild.icon.url)
        await w_ch.send(embed=embed)

    log_ch = bot.get_channel(CHANNEL_INVITE_LOGS)
    if not log_ch: return
    
    old_invites = invites_cache.get(member.guild.id, {})
    new_invites = await fetch_invites(member.guild)
    invites_cache[member.guild.id] = new_invites
    
    inviter_str, code_str, total_str = "לא ידוע / קישור ישיר 🔗", "לא ידוע 🔒", "0"
    
    for code in old_invites:
        if code in new_invites and old_invites[code].uses < new_invites[code].uses:
            inviter = old_invites[code].inviter
            inviter_str = inviter.mention
            code_str = f"`{code}`"
            total_uses = sum(inv.uses for inv in new_invites.values() if inv.inviter and inv.inviter.id == inviter.id)
            total_str = f"`{total_uses}`"
            break
            
    # עיצוב מטורף ברמה הכי גבוהה של פרטיזן/PRRP - נקי, יוקרתי, קריא ומושלם!
    embed = discord.Embed(title="📥 NETWORK ➔ NEW CONNECTION", color=discord.Color.from_rgb(155, 89, 182))
    embed.description = f"**👤 אזרח חדש נקלט בשערי העיר:** {member.mention}\n" \
                        f"**🆔 מזהה רשת אישי:** `{member.id}`\n" \
                        f"━︎━︎━︎━︎━︎━︎━︎━︎━︎━︎━︎━︎━︎━︎━︎━︎━︎━︎━︎━︎━︎\n" \
                        f"**🤝 גורם מזמין:** {inviter_str}\n" \
                        f"**📊 תיק הזמנות כולל:** `{total_str} אזרחים` בעיר\n" \
                        f"**🔑 מפתח קוד בשימוש:** {code_str}"
    
    embed.set_footer(text="Chicago City • Premium Tracker Engine")
    # שאיבה והצגה דינמית של תמונת הפרופיל האישית (Avatar) של השחקן שנכנס בצד ימין (Thumbnail)!
    embed.set_thumbnail(url=member.display_avatar.url)
    await log_ch.send(embed=embed)

class FiveMConnectView(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(discord.ui.Button(label="התחברות ישירה לעיר 🚀", style=discord.ButtonStyle.link, url="https://cfx.re"))

# משימת הסטטוס המאוחדת ברמת עילית
@tasks.loop(minutes=2)
async def update_fivem_status():
    global fivem_msg_id
    ch = bot.get_channel(CHANNEL_FIVEM_STATUS)
    if not ch: return
    
    guild = ch.guild
    total_dc_members = guild.member_count
    online_dc_users = sum(1 for m in guild.members if m.status != discord.Status.offline and not m.bot)
    staff_role = guild.get_role(ROLE_STAFF)
    staff_dc_online = sum(1 for m in staff_role.members if m.status != discord.Status.offline and not m.bot) if staff_role else 0

    status_str, players_str, staff_str, color = "🔴 מנותק (Offline)", "0 / 0", "0 מחוברים", discord.Color.red()
    
    headers = {"User-Agent": "Mozilla/5.0"}
    async with aiohttp.ClientSession(headers=headers) as session:
        try:
            async with session.get(f"https://fivem.net{CFX_ID}", timeout=5) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    server_data = data.get("Data", {})
                    status_str = "🟢 מקוון (Online)"
                    color = discord.Color.green()
                    players_list = server_data.get("players", [])
                    players_str = f"{len(players_list)} / {server_data.get('sv_maxclients', 64)}"
                    fivem_identifiers = []
                    for player in players_list:
                        for identifier in player.get('identifiers', []):
                            if identifier.startswith('discord:'):
                                fivem_identifiers.append(int(identifier.replace('discord:', '')))
                    staff_game_count = sum(1 for m in staff_role.members if m.id in fivem_identifiers) if staff_role else 0
                    staff_str = f"{staff_game_count} אנשי צוות בעיר"
        except: pass

    # עיצוב טבלת הסטטוסים המרוכזת ברמת יוקרה עולמית!
    embed = discord.Embed(title="CHICAGO CITY ➔ LIVE MONITORING", color=color, timestamp=datetime.datetime.utcnow())
    embed.add_field(name="🎮 FIVEM STATUS", value=f"```ansi\n• סטטוס השרת: {status_str}\n• שחקנים בעיר: {players_str}\n• צוות בעיר: {staff_str}```", inline=False)
    embed.add_field(name="💬 DISCORD STATUS", value=f"```ansi\n• סך הכל תושבים: {total_dc_members} אזרחים\n• אזרחים אונליין: {online_dc_users} מחוברים\n• אנשי צוות זמינים: {staff_dc_online} אונליין```", inline=False)
    embed.set_footer(text="Chicago City • Live Statistics Network")
    if guild.icon: embed.set_thumbnail(url=guild.icon.url)

    try:
        if fivem_msg_id is None:
            async for m in ch.history(limit=5):
                if m.author == bot.user and m.embeds and m.embeds.title == "CHICAGO CITY ➔ LIVE MONITORING":
                    fivem_msg_id = m.id; await m.edit(embed=embed, view=FiveMConnectView()); return
            msg = await ch.send(embed=embed, view=FiveMConnectView())
            fivem_msg_id = msg.id
        else:
            msg = await ch.fetch_message(fivem_msg_id)
            await msg.edit(embed=embed, view=FiveMConnectView())
    except: fivem_msg_id = None

keep_alive()
bot.run(os.environ['DISCORD_TOKEN'])
