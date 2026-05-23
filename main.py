import discord
from discord.ext import commands, tasks
from discord.ui import Button, View, Select, Modal, TextInput, UserSelect
import asyncio, datetime, os, random, aiohttp
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
CHANNEL_SUGG_PANEL = 1507020507776811068
CHANNEL_SUGG_LOGS = 1483039217482334253

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

# מערכת אימות - עיצוב צבעוני
class VerifyView(View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="לחצו כאן לאימות מהיר! 🛡️✨", style=discord.ButtonStyle.green, custom_id="verify_btn")
    async def verify_button(self, interaction: discord.Interaction, button: Button):
        await interaction.response.defer(ephemeral=True)
        role = interaction.guild.get_role(ROLE_VERIFIED)
        if role in interaction.user.roles: await interaction.followup.send("🎉 אתה כבר רשום ומאומת בשרת, תיהנה מהעיר!", ephemeral=True)
        else:
            await interaction.user.add_roles(role)
            await interaction.followup.send("🚀 תהליך האימות הצליח! כל החדרים נפתחו עבורך, ברוך הבא ל-Chicago City! 🎉💎", ephemeral=True)

@bot.command()
@commands.has_permissions(administrator=True)
async def setup_verify(ctx):
    embed = discord.Embed(title="🛡️ שער האימות הרשמי ➔ CHICAGO CITY 🎉", description="👑 **ברוכים הבאים לשרת הרולפליי המוביל בישראל!** 👑\n\nכדי לקבל גישה מלאה לאזרחי העיר, לראות את כל חדרי הצ'אט ולהתחיל לשחק, אנא לחצו על **הכפתור הירוק הזוהר** שמופיע ממש כאן למטה! 👇✨", color=discord.Color.from_rgb(46, 204, 113))
    embed.set_footer(text="Chicago City • Secure Gateway Active")
    if ctx.guild.icon: embed.set_image(url=ctx.guild.icon.url)
    await ctx.send(embed=embed, view=VerifyView())

# מערכת טיקטים ופניות צבעונית
class TicketControls(View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="🙋‍♂️ קח טיפול!", style=discord.ButtonStyle.blurple, custom_id="tk_claim")
    async def claim(self, interaction: discord.Interaction, button: Button):
        await interaction.response.defer()
        if interaction.guild.get_role(ROLE_STAFF) not in interaction.user.roles and not interaction.user.guild_permissions.administrator: return
        await interaction.channel.send(f"🔒 🎉 **הפנייה ננעלה בטיפולו המסור והמהיר של האדמין המלך:** {interaction.user.mention} ✨")
        log_ch = bot.get_channel(CHANNEL_TICKET_LOGS)
        if log_ch: await log_ch.send(embed=discord.Embed(title="🎫 טיקט נלקח לטיפול!", description=f"🔹 **ערוץ:** {interaction.channel.mention}\n🔹 **נציג מטפל:** {interaction.user.mention}", color=discord.Color.purple()))
        button.disabled = True; await interaction.message.edit(view=self)

    @discord.ui.button(label="📝 שנה שם חדר", style=discord.ButtonStyle.grey, custom_id="tk_rename")
    async def rename(self, interaction: discord.Interaction, button: Button):
        if interaction.guild.get_role(ROLE_STAFF) not in interaction.user.roles and not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message("❌ אין לך הרשאה לבצע פעולה זו!", ephemeral=True)
        await interaction.response.send_message("⌨️ אנא הקלד את השם החדש שאתה רוצה לתת לחדר הטיקט כעת:", ephemeral=True)
        def check(m): return m.author == interaction.user and m.channel == interaction.channel
        try:
            msg = await bot.wait_for('message', check=check, timeout=30)
            await interaction.channel.edit(name=f"ticket-{msg.content}")
            await interaction.channel.send(f"✨ **שם הערוץ שונה בהצלחה רבה ל:** `ticket-{msg.content}` 🎉")
        except asyncio.TimeoutError: await interaction.channel.send("❌ הזמן הקצוב לעריכת השם פג.")

    @discord.ui.button(label="➕ הוסף חבר לטיקט", style=discord.ButtonStyle.green, custom_id="tk_add_member")
    async def add_member(self, interaction: discord.Interaction, button: Button):
        if interaction.guild.get_role(ROLE_STAFF) not in interaction.user.roles and not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message("❌ אין לך הרשאה לבצע פעולה זו!", ephemeral=True)
        await interaction.response.send_message("👤 תייג כעת בצ'אט את המשתמש שאתה רוצה להכניס לטיקט הפרטי הזה:", ephemeral=True)
        def check(m): return m.author == interaction.user and m.channel == interaction.channel
        try:
            msg = await bot.wait_for('message', check=check, timeout=30)
            if msg.mentions:
                target = msg.mentions
                await interaction.channel.set_permissions(target, read_messages=True, send_messages=True)
                await interaction.channel.send(f"🎉 **המערכת הכניסה בהצלחה את** {target.mention} **לתוך חדר התמיכה!** ✅")
            else: await interaction.channel.send("❌ שגיאה: לא תייגת משתמש תקין.")
        except asyncio.TimeoutError: pass

    @discord.ui.button(label="❌ סגור ומחק טיקט", style=discord.ButtonStyle.red, custom_id="tk_close")
    async def close(self, interaction: discord.Interaction, button: Button):
        await interaction.response.defer()
        if interaction.guild.get_role(ROLE_STAFF) not in interaction.user.roles and not interaction.user.guild_permissions.administrator: return
        await interaction.channel.send("🚧 🔥 **חדר התמיכה יימחק לחלוטין משרת הדיסקורד בעוד 5 שניות...**")
        log_ch = bot.get_channel(CHANNEL_TICKET_LOGS)
        if log_ch: await log_ch.send(embed=discord.Embed(title="❌ חדר טיקט נסגר ונמחק", description=f"🔹 **שם חדר:** `{interaction.channel.name}`\n🔹 **נסגר ע''י:** {interaction.user.mention}", color=discord.Color.red()))
        await asyncio.sleep(5); await interaction.channel.delete()

class TicketDropdown(Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="דיווח רשמי על שחקן / איש צוות סורח", emoji="🚫", value="דיווח שחקן/צוות"),
            discord.SelectOption(label="הגשת מועמדות ובחינה לצוות השרת", emoji="📝", value="בחינה לצוות"),
            discord.SelectOption(label="דיווח דחוף על באג או תקלה טכנית בעיר", emoji="🐛", value="דיווח על באג"),
            discord.SelectOption(label="שאלה כללית, עזרה מנהלתית או פנייה פתוחה", emoji="❓", value="שאלה כללית")
        ]
        super().__init__(placeholder="לחצו כאן ובחרו את נושא הפנייה שלכם... 🎫🔑", options=options, custom_id="tk_select")

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        ticket_channel = await interaction.guild.create_text_channel(name=f"ticket-{interaction.user.name}", category=interaction.channel.category)
        await ticket_channel.set_permissions(interaction.guild.default_role, read_messages=False)
        await ticket_channel.set_permissions(interaction.user, read_messages=True, send_messages=True)
        await ticket_channel.set_permissions(interaction.guild.get_role(ROLE_STAFF), read_messages=True, send_messages=True)
        await interaction.followup.send(f"🎉 הטיקט שלך נוצר בהצלחה! לחץ כאן כדי להיכנס אליו: {ticket_channel.mention}", ephemeral=True)
        
        log_ch = bot.get_channel(CHANNEL_TICKET_LOGS)
        if log_ch: await log_ch.send(embed=discord.Embed(title="➕ טיקט חדש נפתח בשרת!", description=f"🔹 **פותח הפנייה:** {interaction.user.mention}\n🔹 **נושא הטיקט:** `{self.values}`\n🔹 **חדר:** {ticket_channel.mention}", color=discord.Color.green()))
            
        embed = discord.Embed(title="🎫 מרכז הפניות והתמיכה ➔ CHICAGO CITY 💎", description=f"שלום {interaction.user.mention}! 🎉\n\nפנייתך בנושא המוגדר כמפורט: `{self.values}` נפתחה בהצלחה רבה.\n\n**אנא רשום כאן בצ'אט את כל פירוט המקרה שלך בצורה ברורה ביותר**, ואנשי צוות השרת יגיעו לסייע לך בתוך דקות ספורות! 🚀✨", color=discord.Color.from_rgb(142, 68, 173))
        embed.set_footer(text="Chicago City • Support System Desk")
        await ticket_channel.send(embed=embed, view=TicketControls())
        p = await ticket_channel.send(f"<@&{ROLE_STAFF}>"); await p.delete()

@bot.command()
@commands.has_permissions(administrator=True)
async def setup_tickets(ctx):
    embed = discord.Embed(title="🎫 מרכז התמיכה והפניות הרשמי של העיר 🎉", description="צריכים עזרה מההנהלה, רוצים לדווח על באג מציק או להגיש מועמדות לצוות? ✨\n\n**אנא פתחו את התפריט הנפתח שמופיע כאן למטה, בחרו את הנושא שלכם וחדר תמיכה פרטי ייפתח עבורכם בשנייה!** 👇💎", color=discord.Color.purple())
    embed.set_footer(text="Chicago City • Helpdesk Terminal")
# --- מערכת הגרלות צבעונית מבוססת פאנל וטפסים (GIVEAWAY MODAL SYSTEM) ---
class GiveawayModal(Modal):
    def __init__(self):
        super().__init__(title="🎉 יצירת הגרלה חדשה - Chicago City")
        self.prize = TextInput(label="🎁 מה הפרס המטורף של ההגרלה?", placeholder="לדוגמה: רכב ספורט יוקרתי / 1,000,000$", required=True)
        self.time = TextInput(label="⏱️ זמן ריצה כולל (בדקות)", placeholder="לדוגמה: 15", required=True)
        self.winners = TextInput(label="👥 כמות זוכים מאושרים", placeholder="לדוגמה: 1", required=True)
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

        embed = discord.Embed(title="🎁 הגרלה מטורפת יצאה לדרך! ➔ CHICAGO CITY 🎉", color=discord.Color.gold())
        embed.description = f"🔥 **משתמשים יקרים, יש לכם הזדמנות לזכות בפרס מטורף!** 🔥\n\n" \
                            f"✨ **הפרס המנצח:** `{self.prize.value}`\n" \
                            f"👥 **כמות זוכים:** `{winners_count}`\n" \
                            f"⏱️ **זמן נותר לחגיגה:** `{duration}` דקות\n\n" \
                            f"🎉 **לחצו על הכפתור הירוק למטה כדי להיכנס להגרלה ולהבטיח את מקומכם!** 👇🏆"
        embed.set_footer(text="Chicago City • Luck & Giveaways")
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
    @discord.ui.button(label="🎁 פתח הגרלה חדשה לשחקנים", style=discord.ButtonStyle.green, custom_id="gv_panel_btn")
    async def create_gv(self, interaction: discord.Interaction, button: Button):
        if interaction.guild.get_role(ROLE_STAFF) not in interaction.user.roles and not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message("❌ אין לך הרשאה לפתוח פאנל זה!", ephemeral=True)
        await interaction.response.send_modal(GiveawayModal())

class AdvancedGiveawayView(View):
    def __init__(self, prize, winners):
        super().__init__(timeout=None)
        self.prize, self.winners, self.entrants, self.active = prize, winners, [], True
    @discord.ui.button(label="🎉 הצטרף להגרלה!", style=discord.ButtonStyle.green, custom_id="gv_join")
    async def join(self, interaction: discord.Interaction, b: Button):
        await interaction.response.defer(ephemeral=True)
        if not self.active: return await interaction.followup.send("❌ ההגרלה כבר הגיעה לסיומה!", ephemeral=True)
        if interaction.user.id in self.entrants: return await interaction.followup.send("אתה כבר רשום במערכת ההגרלה הזו! 🍀", ephemeral=True)
        self.entrants.append(interaction.user.id)
        await interaction.followup.send("✅ נרשמת בהצלחה! המערכת נעלה את השם שלך בתיבת המזל.🍀", ephemeral=True)

    @discord.ui.button(label="📈 כמות רשומים", style=discord.ButtonStyle.grey, custom_id="gv_status")
    async def status(self, interaction: discord.Interaction, b: Button):
        await interaction.response.defer(ephemeral=True)
        await interaction.followup.send(f"📊 יש כרגע `{len(self.entrants)}` משתתפים רשומים בהגרלה זו.", ephemeral=True)

    @discord.ui.button(label="⏱️ סגור הגרלה כעת", style=discord.ButtonStyle.red, custom_id="gv_end_now")
    async def end_early(self, interaction: discord.Interaction, b: Button):
        await interaction.response.defer()
        if interaction.guild.get_role(ROLE_STAFF) not in interaction.user.roles: return
        self.active = False; await end_gv(interaction.channel, self.prize, self.winners, self.entrants, interaction.message)

async def end_gv(channel, prize, winners, entrants, msg):
    if len(entrants) < winners: await msg.edit(embed=discord.Embed(title="🌈 CHICAGO CITY ➔ GIVEAWAY", description="❌ ההגרלה בוטלה באופן אוטומטי עקב חוסר משתתפים בשרת.", color=discord.Color.red()), view=None)
    else:
        w = random.sample(entrants, winners); m = ", ".join([f"<@{x}>" for x in w])
        await msg.edit(embed=discord.Embed(title="🏆 ההגרלה הסתיימה רשמית! 🎉", description=f"✨ **הפרס המטורף שחולק:** `{prize}`\n\n👥 **הזוכים המאושרים שגרפו את הפרס:**\n{m}\n\n👑 ברכות לזוכים! פנו לצוות לקבלת הפרס.", color=discord.Color.green()), view=None)
        await channel.send(f"🎉 💎 **מזל טוב ענקי לזוכים המאושרים בהגרלה על {prize}!** {m}")

@bot.command()
@commands.has_permissions(administrator=True)
async def setup_giveaway_panel(ctx):
    embed = discord.Embed(title="🎁 מרכז ניהול ההגרלות הרשמי של הצוות 🎉", description="שלום חברי צוות יקרים! ✨\nמערכת זו מיועדת ליצירת הגרלות מעוצבות בצורה קלה.\n\n**לחצו על הכפתור הירוק למטה כדי לפתוח את טופס יצירת ההגרלה המהיר!** 👇💎", color=discord.Color.green())
    embed.set_footer(text="Chicago City Staff Console • Color Edition")
    await ctx.send(embed=embed, view=GiveawayPanelView())

# --- פאנל אזהרות ---
class StaffSelectReasonModal(Modal):
    def __init__(self, target_member):
        super().__init__(title="🚨 הזנת סיבת אזהרה - משמעת")
        self.target = target_member
        self.reason = TextInput(label="רשום כאן את סיבת האזהרה המלאה", placeholder="חוסר כבוד / אביוז דרגות", required=True)
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
            embed = discord.Embed(title="🚨 רישום משמעת חמור בצוות! ➔ CHICAGO CITY 💥", color=discord.Color.red())
            embed.description = f"💥 **אזהרה רשמית נרשמה בתיק האישי של חבר צוות!** 💥\n\n👤 **חבר הצוות שנענש:** {self.target.mention}\n🛡️ **האדמין המעניש מההנהלה:** {interaction.user.mention}\n📅 **מועד ומילוי האירוע:** `{t}`\n\n📝 **סיבת האזהרה בתיק:**\n```fix\n{self.reason.value}```\n📊 **מצב תיק אזהרות עדכני:** `{'🟥' * count + '⬛' * (3 - count)}` ({count}/3 אזהרות)"
            embed.set_thumbnail(url=self.target.display_avatar.url)
            await log_ch.send(embed=embed)
        await interaction.followup.send(f"✅ האזהרה נרשמה בהצלחה רבה ל-{self.target.mention} והלוג שודר לערוץ!", ephemeral=True)

class WarnUserSelect(UserSelect):
    def __init__(self, action_type):
        super().__init__(placeholder="אנא לחצו ובחרו חבר צוות מהרשימה... 👤✨", min_values=1, max_values=1)
        self.action_type = action_type

    async def callback(self, interaction: discord.Interaction):
        target = self.values[0]
        if self.action_type == "add":
            await interaction.response.send_modal(StaffSelectReasonModal(target))
        elif self.action_type == "view":
            c = len(staff_warns_db.get(target.id, []))
            if c == 0: return await interaction.response.send_message(f"🟢 ✨ **חבר הצוות המלך** {target.mention} **נקי לחלוטין ללא שום אזהרות בתיק האישי!** 🎉", ephemeral=True)
            embed = discord.Embed(title=f"📊 גיליון אזהרות צוות רשמי ➔ {target.name} 🚨", color=discord.Color.orange())
            for i, w in enumerate(staff_warns_db[target.id], 1):
                embed.add_field(name=f"🚨 אזהרה מספר {i} ➔ בתאריך {w['date']}", value=f"🔹 **רשם והעניש:** <@{w['by']}>\n🔹 **הסיבה הרשומה:** {w['reason']}", inline=False)
            await interaction.response.send_message(embed=embed, ephemeral=True)
        elif self.action_type == "remove":
            if target.id in staff_warns_db and len(staff_warns_db[target.id]) > 0:
                staff_warns_db[target.id].pop()
                await interaction.response.send_message(f"✅ **האזהרה האחרונה של חבר הצוות** {target.mention} **נמחקה מהתיק בהצלחה!** 🔓", ephemeral=True)
            else: await interaction.response.send_message(f"❌ ל-{target.mention} אין שום אזהרות פעילות שניתן למחוק.", ephemeral=True)

class WarnPanelView(View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="⚠️ רשום אזהרה למנהל", style=discord.ButtonStyle.red, custom_id="wp_add")
    async def add_warn_btn(self, interaction: discord.Interaction, button: Button):
        if interaction.guild.get_role(ROLE_WARN_ADMIN) not in interaction.user.roles and not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message("❌ אבטחה: מיועד לדרג ניהול עליון בלבד!", ephemeral=True)
        view = View().add_item(WarnUserSelect("add"))
        await interaction.response.send_message("⚙️ **בחרו מתוך רשימת חברי הצוות מטה את המנהל שברצונכם להזהיר:**", view=view, ephemeral=True)

    @discord.ui.button(label="📊 כמות ווארנים בתיק", style=discord.ButtonStyle.grey, custom_id="wp_view")
    async def view_warn_btn(self, interaction: discord.Interaction, button: Button):
