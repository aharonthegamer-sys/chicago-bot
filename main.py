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

# מערכת אימות - עיצוב ירוק זוהר וצבעוני
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

# מערכת טיקטים ופניות צבעונית בטירוף
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
        super().__init__(placeholder="לחצו כאן ובחרו את נושא הפנייה שלכם... 🎫✨", options=options, custom_id="tk_select")

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
    if ctx.guild.icon: embed.set_image(url=ctx.guild.icon.url)
    await ctx.send(embed=embed, view=View().add_item(TicketDropdown()))
# --- מערכת הגרלות מתקדמת מבוססת פאנל וטפסים (GIVEAWAY MODAL SYSTEM) ---
class GiveawayModal(Modal):
    def __init__(self):
        super().__init__(title="🎁 יצירת הגרלה מטורפת — Chicago City 🎁")
        self.prize = TextInput(label="🎉 מה הפרס השווה של ההגרלה?", placeholder="לדוגמה: 500,000$ / רכב ספורט נדיר!", required=True)
        self.time = TextInput(label="⏱️ זמן ריצה כולל (בדקות)", placeholder="לדוגמה: 10", required=True)
        self.winners = TextInput(label="👥 כמות זוכים מוגדרת", placeholder="לדוגמה: 1", required=True)
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

        embed = discord.Embed(title="🎁 הגרלה מטורפת יצאה לדרך! ➔ CHICAGO CITY 🎉", description=f"🔥 **הפרס המטורף:** `{self.prize.value}` 🔥\n\n👥 **כמות זוכים מוגדרת:** `{winners_count} זוכים מאושרים!`\n⏱️ **זמן לסיום לפרוס:** `{duration}` דקות שלמות!\n\n🍀 **אל תפספסו את ההזדמנות! לחצו על הכפתור הירוק הזוהר למטה כדי להיכנס להגרלה ולהבטיח את המקום שלכם!** 🍀", color=discord.Color.gold())
        embed.set_footer(text="Chicago City • Luck & Rewards System 💎")
        if interaction.guild.icon: embed.set_thumbnail(url=interaction.guild.icon.url)

        view = AdvancedGiveawayView(self.prize.value, winners_count)
        msg = await public_ch.send(embed=embed, view=view)
        await interaction.followup.send(f"✅ ההגרלה המטורפת נוצרה ופורסמה בהצלחה בערוץ {public_ch.mention}! 🎉", ephemeral=True)

        await asyncio.sleep(duration * 60)
        if view.active:
            view.active = False
            await end_gv(public_ch, self.prize.value, winners_count, view.entrants, msg)

class GiveawayPanelView(View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="🎁 פתח טופס הגרלה חדשה!", style=discord.ButtonStyle.green, custom_id="gv_panel_btn")
    async def create_gv(self, interaction: discord.Interaction, button: Button):
        if interaction.guild.get_role(ROLE_STAFF) not in interaction.user.roles and not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message("❌ אין לך הרשאה לפתוח פאנל זה!", ephemeral=True)
        await interaction.response.send_modal(GiveawayModal())

class AdvancedGiveawayView(View):
    def __init__(self, prize, winners):
        super().__init__(timeout=None)
        self.prize, self.winners, self.entrants, self.active = prize, winners, [], True
    @discord.ui.button(label="🎉 להיכנס להגרלה כעת!", style=discord.ButtonStyle.green, custom_id="gv_join")
    async def join(self, interaction: discord.Interaction, b: Button):
        await interaction.response.defer(ephemeral=True)
        if not self.active: return await interaction.followup.send("❌ אוי חבל! ההגרלה הזו כבר הגיעה לסיומה!", ephemeral=True)
        if interaction.user.id in self.entrants: return await interaction.followup.send("🍀 אל תדאג, אתה כבר רשום במערכת ומחזיק בכרטיס הגרלה! בהצלחה!", ephemeral=True)
        self.entrants.append(interaction.user.id)
        await interaction.followup.send("✅ נרשמת בהצלחה מטורפת! השם שלך בפנים, שיהיה המון בהצלחה! 🍀💎", ephemeral=True)

    @discord.ui.button(label="📈 כמות המשתתפים כרגע", style=discord.ButtonStyle.grey, custom_id="gv_status")
    async def status(self, interaction: discord.Interaction, b: Button):
        await interaction.response.defer(ephemeral=True)
        await interaction.followup.send(f"📊 וואו! יש כרגע כ-`{len(self.entrants)}` משתתפים רשומים בהגרלה זו!", ephemeral=True)

    @discord.ui.button(label="⏱️ סגור הגרלה מיידית", style=discord.ButtonStyle.red, custom_id="gv_end_now")
    async def end_early(self, interaction: discord.Interaction, b: Button):
        await interaction.response.defer()
        if interaction.guild.get_role(ROLE_STAFF) not in interaction.user.roles: return
        self.active = False; await end_gv(interaction.channel, self.prize, self.winners, self.entrants, interaction.message)

async def end_gv(channel, prize, winners, entrants, msg):
    if len(entrants) < winners: await msg.edit(embed=discord.Embed(title="🎁 תוצאות ההגרלה הגדולה ➔ CHICAGO CITY", description="😭 **ההגרלה בוטלה באופן אוטומטי עקב חוסר משתתפים רשומים!**", color=discord.Color.red()), view=None)
    else:
        w = random.sample(entrants, winners); m = ", ".join([f"<@{x}>" for x in w])
        await msg.edit(embed=discord.Embed(title="🏆 ההגרלה הגדולה הסתיימה בהצלחה מטורפת! 🎉", description=f"🏆 **הפרס המטורף שחולק:** `{prize}`\n\n👥 **הזוכים המאושרים ששיחק להם המזל:**\n👑 {m} 👑\n\n🎉 **ברכות חמות לכל הזוכים המאושרים! פנו לאחד מאנשי הצוות לקבלת הפרס שלכם!** 🎉", color=discord.Color.green()), view=None)
        await channel.send(f"🎊 **מזל טוב ענקי ומטורף לזוכים הגדולים בהגרלה על {prize}!** {m} 💎🎈")

@bot.command()
@commands.has_permissions(administrator=True)
async def setup_giveaway_panel(ctx):
    embed = discord.Embed(title="🎁 מרכז השליטה והניהול להגרלות של הצוות ➔ CHICAGO CITY 🎉", description="🚀 **שלום לכל אנשי הצוות התותחים!** 🚀\n\nרוצים לפנק את הקהילה המטורפת שלנו בפרסים, כסף או רכבים יוקרתיים בעיר?\n\n👉 **לחצו על הכפתור הירוק למטה, מלאו את פרטי הפרס והזמן בטופס וההגרלה תשוגר מיידית לתושבים!** ✨", color=discord.Color.green())
    embed.set_footer(text="Chicago City Staff Rewards System")
    await ctx.send(embed=embed, view=GiveawayPanelView())

# --- פאנל אזהרות משודרג מבוסס בחירת תיוג @ ישירה (WARN PANEL USER SELECT) ---
class StaffSelectReasonModal(Modal):
    def __init__(self, target_member):
        super().__init__(title="🚨 הזנת סיבת האזהרה לחבר הצוות 🚨")
        self.target = target_member
        self.reason = TextInput(label="📝 הקלד כאן את סיבת העונש והאזהרה", placeholder="לדוגמה: אביוז דרגות קשה / אי כבוד למנהל בכיר", required=True)
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
            embed = discord.Embed(title="🚨 רישום עונש משמעתי חמור בצוות ➔ CHICAGO CITY 🚨", color=discord.Color.red())
            embed.description = f"🔥 **שימו לב - חבר צוות עבר על חוקי המשמעת של השרת!** 🔥\n\n" \
                                f"👤 **חבר הצוות המוענש:** {self.target.mention}\n" \
                                f"🛡️ **המנהל הבכיר שהעניש:** {interaction.user.mention}\n" \
                                f"📅 **מועד רישום האירוע:** `{t}`\n\n" \
                                f"📝 **סיבת האזהרה המלאה:**\n```fix\n{self.reason.value}```\n" \
                                f"📊 **מצב תיק האזהרות האישי שלו כרגע:**\n`{'🟥' * count + '⬛' * (3 - count)}` ({count}/3 אזהרות כולל!)"
            embed.set_footer(text="Chicago City Management Secure Database")
            if interaction.guild.icon: embed.set_image(url=ctx.guild.icon.url)
                
            bars = "Core" if count > 3 else "🟥" * count + "⬛" * (3 - count)
            await log_ch.send(f"⚠️ <@&{ROLE_STAFF}> **רישום משמעת חדש עלה במערכת!**")
            await log_ch.send(embed=embed)
        await interaction.followup.send(f"✅ האזהרה נרשמה בהצלחה מטורפת ובצבעים בוהקים ל-{self.target.mention}! הרישום הועבר ללוג.", ephemeral=True)

class WarnUserSelect(UserSelect):
    def __init__(self, action_type):
        super().__init__(placeholder="לחצו כאן ובחרו את חבר הצוות מהרשימה... 👥✨", min_values=1, max_values=1)
        self.action_type = action_type

    async def callback(self, interaction: discord.Interaction):
        target = self.values
        if self.action_type == "add":
            await interaction.response.send_modal(StaffSelectReasonModal(target))
        elif self.action_type == "view":
            c = len(staff_warns_db.get(target.id, []))
            if c == 0: return await interaction.response.send_message(f"🟢 ✨ **איזה מלך! חבר הצוות** {target.mention} **נקי לחלוטין כמו קריסטל וללא שום אזהרות בתיק שלו!** 🎉💎", ephemeral=True)
            embed = discord.Embed(title=f"📊 גיליון המשמעת המלא של חבר הצוות: {target.name} ✨", color=discord.Color.orange())
            for i, w in enumerate(staff_warns_db[target.id], 1):
                embed.add_field(name=f"🚨 אזהרה מספר {i} ➔ בתאריך {w['date']} ⏰", value=f"🔹 **האדמין שהעניש:** <@{w['by']}>\n🔹 **סיבת העבירה:** {w['reason']}", inline=False)
            embed.set_footer(text="Chicago City Command Registry")
            await interaction.response.send_message(embed=embed, ephemeral=True)
        elif self.action_type == "remove":
            if target.id in staff_warns_db and len(staff_warns_db[target.id]) > 0:
                staff_warns_db[target.id].pop()
                await interaction.response.send_message(f"✅ **האזהרה האחרונה של חבר הצוות** {target.mention} **נמחקה בהצלחה והתיק שלו נוקה בחלקו!** 🔓🎉", ephemeral=True)
            else: await interaction.response.send_message(f"❌ שגיאה: לא נמצאו אזהרות פעילות למחיקה בתיק של {target.mention}.", ephemeral=True)

class WarnPanelView(View):
    def __init__(self): super().__init__(timeout=None)
    
    @discord.ui.button(label="⚠️ רשום אזהרה חמורה למנהל", style=discord.ButtonStyle.red, custom_id="wp_add")
    async def add_warn_btn(self, interaction: discord.Interaction, button: Button):
        if interaction.guild.get_role(ROLE_WARN_ADMIN) not in interaction.user.roles and not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message("❌ אבטחה: מיועד לדרג ניהול עליון ומורשי משמעת בלבד!", ephemeral=True)
        view = View().add_item(WarnUserSelect("add"))
        await interaction.response.send_message("⚙️ 🔥 **מערכת אבטחה:** בחרו כעת מתוך התפריט למטה את חבר הצוות שברצונכם להעניש:", view=view, ephemeral=True)

    @discord.ui.button(label="📊 לצפייה בתיק האזהרות שלו", style=discord.ButtonStyle.grey, custom_id="wp_view")
    async def view_warn_btn(self, interaction: discord.Interaction, button: Button):
        if interaction.guild.get_role(ROLE_WARN_ADMIN) not in interaction.user.roles and not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message("❌ אבטחה: מיועד לדרג ניהול עליון ומורשי משמעת בלבד!", ephemeral=True)
        view = View().add_item(WarnUserSelect("view"))
        await interaction.response.send_message("⚙️ **מערכת רישום:** בחרו חבר צוות מתוך התפריט כדי לשלוף מיידית את גיליון האזהרות שלו:", view=view, ephemeral=True)

    @discord.ui.button(label="🔓 מחק אזהרה אחרונה (Unwarn)", style=discord.ButtonStyle.green, custom_id="wp_remove")
    async def remove_warn_btn(self, interaction: discord.Interaction, button: Button):
        if interaction.guild.get_role(ROLE_WARN_ADMIN) not in interaction.user.roles and not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message("❌ אבטחה: מיועד לדרג ניהול עליון ומורשי משמעת בלבד!", ephemeral=True)
        view = View().add_item(WarnUserSelect("remove"))
        await interaction.response.send_message("⚙️ **מערכת חנינה:** בחרו חבר צוות מתוך התפריט כדי למחוק לו את האזהרה האחרונה מהתיק:", view=view, ephemeral=True)

@bot.command()
@commands.has_permissions(administrator=True)
async def setup_warn_panel(ctx):
    embed = discord.Embed(title="🚨 פאנל אבטחה ומשמעת חסוי לצוות השרת ➔ CHICAGO CITY 🚨", description="👑 **שלום לדרג הניהול הגבוה של העיר!** 👑\n\nזהו פאנל השליטה והבקרה המרכזי למשמעת ואכיפת החוקים בתוך הצוות.\n\n👉 **לחצו על הכפתורים הצבעוניים למטה כדי לרשום ווארן, לבדוק תיק אזהרות, או לתת חנינה לחבר צוות בשנייה באמצעות תפריט תיוג חכם!** ⚡✨", color=discord.Color.red())
    embed.set_footer(text="Chicago City Internal Security Administration Only")
    await ctx.send(embed=embed, view=WarnPanelView())

# מערכת הצעות מטורפת (SUGGESTIONS SYSTEM)
CHANNEL_SUGG_PANEL = 1507020507776811068
CHANNEL_SUGG_LOGS = 1483039217482334253

class SuggestionModal(Modal):
    def __init__(self):
        super().__init__(title="💡 הגשת הצעה חדשה ומטורפת לעיר! 💡")
        self.sugg = TextInput(label="📝 פרט כאן את הרעיון המשוגע שלך לשדרוג העיר", style=discord.TextStyle.paragraph, placeholder="רשום כאן את הצעתך בצורה ברורה הכוללת רכבים, מערכות וכו'...", required=True)
        self.add_item(self.sugg)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        log_ch = bot.get_channel(CHANNEL_SUGG_LOGS)
        if not log_ch: return await interaction.followup.send("❌ ערוץ הלוגים של ההצעות לא נמצא.", ephemeral=True)
        
        embed = discord.Embed(title="💡 הצעה חדשה ומטורפת עלתה לאוויר! 💡 ➔ CHICAGO CITY", color=discord.Color.blue())
        embed.description = f"🔥 **רעיון חדש ומשוגע עלה לעיר משחקן בקהילה!** 🔥\n\n```fix\n{self.sugg.value}```\n" \
                            f"🔹 **הוגש בגאווה ע''י האזרח המלך:** {interaction.user.mention}"
        embed.set_footer(text="Chicago City Suggestions • מה דעתכם?")
        if interaction.guild.icon: embed.set_thumbnail(url=interaction.guild.icon.url)
        
        msg = await log_ch.send(embed=embed)
        await msg.add_reaction("👍")
        await msg.add_reaction("👎")
        await interaction.followup.send("✅ ההצעה המטורפת שלך שודרה בהצלחה מטורפת לערוץ ההצעות של הקהילה והתווספו אליה תגובות הצבעה! תודה רבה 🎉💎", ephemeral=True)

class SuggestionPanelView(View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="💡 לחצו כאן להגשת הצעה חדשה ומשוגעת לעיר!", style=discord.ButtonStyle.blurple, custom_id="sugg_panel_btn")
    async def add_sugg(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_modal(SuggestionModal())

@bot.command()
@commands.has_permissions(administrator=True)
async def setup_suggestions(ctx):
    embed = discord.Embed(title="💡 מרכז ההצעות והרעיונות הרשמי של הקהילה ➔ CHICAGO CITY 💎", description="יש לכם רעיון מטורף ומשוגע לשדרוג חווית המשחק בעיר, הצעה לרכב ספורט חדש או מערכת סקריפטים שווה? 🚀✨\n\n**אנא לחצו על הכפתור הכחול הזוהר שמופיע כאן למטה, מלאו את הטופס הדיגיטלי והרעיון שלכם ישוגר מיידית להצבעת הקהילה!** 👇🎈", color=discord.Color.blue())
    embed.set_footer(text="Chicago City Suggestions • Community Power")
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

# --- מנוע ה-INVITE TRACKER המטורף והמשודרג ברמת צבעוניות ואיכות מטורפת (PREMIUM AVATAR TRACKER) ---
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
        embed = discord.Embed(title="🎉 ברוך הבא לעולם של CHICAGO CITY רולפליי! ➔ WELCOME 💎", description=f"💎 **תושב חדש ומלך נחת בשערי העיר, תעשו לו המון כבוד!** 💎\n\n👤 **הכירו את:** {member.mention}\n\n🛡️ **שלב ראשון וקריטי:** אנא כנסו מיידית לערוץ האבטחה והשלימו את תהליך האימות לקבלת גישה מלאה: <#{ROLE_VERIFIED}> ✨", color=discord.Color.red())
        embed.set_thumbnail(url=member.display_avatar.url); embed.set_footer(text="Chicago City Server Administration System")
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
            
    # עיצוב מטורף, עשיר בצבעים ואימוג'ים בסטייל משוגע!
    embed = discord.Embed(title="📥 מערכת מעקב הזמנות אוטומטית ➔ NEW USER JOINED 🎉", color=discord.Color.from_rgb(155, 89, 182))
    embed.description = f"🌟 **אזרח חדש ומטורף נקלט כעת בשערי העיר!** 🌟\n\n" \
                        f"🔹 **שם המשתמש:** {member.mention}\n" \
                        f"🔹 **מזהה דיסקורד רשמי:** `{member.id}`\n" \
                        f"━︎━︎━︎━︎━︎━︎━︎━︎━︎━︎━︎━︎━︎━︎━︎━︎━︎━︎━︎━︎━︎\n" \
                        f"🤝 **הגורם שהזמין אותו לעיר:** {inviter_str}\n" \
                        f"📊 **תיק ההזמנות הכולל שלו כרגע:** `{total_str} אזרחים` מחוברים!\n" \
                        f"🔑 **קוד הקישור שבו הוא השתמש:** {code_str}"
    
    embed.set_footer(text="Chicago City • Premium Color Tracker Engine 💎")
    # שאיבה והצגה דינמית של תמונת הפרופיל האישית (Avatar) של השחקן שנכנס בצד ימין (Thumbnail)!
    embed.set_thumbnail(url=member.display_avatar.url)
    await log_ch.send(embed=embed)

class FiveMConnectView(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(discord.ui.Button(label="התחברות מהירה לעיר! 🚀✨", style=discord.ButtonStyle.link, url="https://cfx.re"))

# משימת הסטטוס המאוחדת ברמת צבעוניות ויוקרה
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

    # עיצוב טבלת הסטטוסים המרוכזת ברמת יוקרה עשירה בצבעים ואימוג'ים!
    embed = discord.Embed(title="🎮 מערכת הניטור והסטטוס החי ➔ CHICAGO CITY 🎉", color=color, timestamp=datetime.datetime.utcnow())
    embed.add_field(name="🕹️ FIVEM GAME SERVER STATUS", value=f"```ansi\n[2;32m• סטטוס השרת כעת: {status_str}[0m\n[2;34m• שחקנים מחוברים בעיר: {players_str} שחקנים[0m\n[2;35m• אנשי צוות בתוך העיר: {staff_str}[0m```", inline=False)
    embed.add_field(name="💬 DISCORD SERVER STATUS", value=f"```ansi\n[2;36m• סך הכל תושבים רשומים: {total_dc_members} אזרחים[0m\n[2;33m• אזרחים מחוברים כעת: {online_dc_users} אונליין[0m\n[2;32m• אנשי צוות זמינים בדיסקורד: {staff_dc_online} מנהלים[0m```", inline=False)
    embed.set_footer(text="Chicago City • Live Real-time Statistics Network 📊")
    if guild.icon: embed.set_thumbnail(url=guild.icon.url)

    try:
        if fivem_msg_id is None:
            async for m in ch.history(limit=5):
                if m.author == bot.user and m.embeds and m.embeds.title == "🎮 מערכת הניטור והסטטוס החי ➔ CHICAGO CITY 🎉":
                    fivem_msg_id = m.id; await m.edit(embed=embed, view=FiveMConnectView()); return
            msg = await ch.send(embed=embed, view=FiveMConnectView())
            fivem_msg_id = msg.id
        else:
            msg = await ch.fetch_message(fivem_msg_id)
            await msg.edit(embed=embed, view=FiveMConnectView())
    except: fivem_msg_id = None

keep_alive()
bot.run(os.environ['DISCORD_TOKEN'])
