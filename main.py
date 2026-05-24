import os
import asyncio
import random
from flask import Flask
from threading import Thread
import discord
from discord.ext import tasks, commands

# ========================================================
# 1. שרת FLASK פנימי חסין קריסות עבור RENDER
# ========================================================
app = Flask('')

@app.route('/')
def home():
    return "Chicago City Diamond Engine Operational"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run_flask)
    t.daemon = True
    t.start()

# ========================================================
# 2. קונפיגורציית ערוצים, רולים וקישורי באנרים (PRRP Standard)
# ========================================================
SERVER_NAME = "Chicago City Roleplay"
GUILD_ID = 1483039214793789483

LOGO_URL = "https://discordapp.com"
BANNER_URL = "https://ibb.co"

STATUS_CHANNEL_ID = 1506965475270332476       # סרבר סטטוס
WELCOME_CHANNEL_ID = 1483039215032041530      # ברוכים הבאים
GIVEAWAY_PANEL_CH = 1507022943413342328       # פנל ניהול הגרלות לצוות
GIVEAWAY_FEED_CH = 1483039216366780532        # פיד הגרלות לשחקנים
WARN_PANEL_CH = 1507023136095207515           # פנל ניהול אזהרות לצוות
WARN_FEED_CH = 1483039219336347810            # פיד אזהרות רשמי (#staff-warns)
SUGGEST_PANEL_CH = 1507020507776811068        # פנל ניהול הצעות
SUGGEST_FEED_CH = 1483039217482334253         # פיד הצעות להצבעה

# רשת ערוצי הלוגים המלאה (מנותב אוטומטית לפי קטגוריות)
LOG_TICKET = 1483039219654852612              # לוג טיקטים (Ticket-logs)
LOG_SECURITY = 1483039220284002367             # לוג אבטחה ואימות (Security-logs)
LOG_ROLE_ADD = 1507881637705420961             # לוג הוספת רול (Role-add-log)
LOG_ROLE_REMOVE = 1507881755753971872          # לוג הסרת רול (Role-remove-log)

VERIFY_ROLE_ID = 1483039214793789489          # רול אזרח מאומת
STAFF_ROLE_ID = 1483039215364345930           # רול צוות כללי לניהול טיקטים
GIVEAWAY_ROLE_ID = 1506419159414603868        # רול מנהלי הגרלות מורשים
WARN_STAFF_ROLE_ID = 1483039215393702012      # רול מנהלי אזהרות מורשים

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True 
intents.guilds = True         
intents.members = True        
intents.presences = True      

bot = commands.Bot(command_prefix="!", intents=intents, chunk_guilds_at_startup=True)
status_message = None
warnings_db = {}
# פונקציית לוגים דינמית ומעוצבת השולחת דוחות לערוצים המתאימים בשרת
async def dispatch_log(target_channel_id, title, description, color=0x010101, fields=None):
    channel = bot.get_channel(target_channel_id)
    if not channel: 
        return
    embed = discord.Embed(title=f"🛡️ AUDIT OVERVIEW | {title.upper()}", description=description, color=color)
    if fields:
        for name, value in fields.items():
            embed.add_field(name=f"🔹 {name}", value=f"```yaml\n{value}\n```", inline=True)
    embed.set_thumbnail(url=LOGO_URL)
    embed.set_footer(text="Chicago City System Security logs")
    embed.timestamp = discord.utils.utcnow()
    try: 
        await channel.send(embed=embed)
    except: 
        pass

@bot.event
async def on_message(message):
    if message.author.bot: 
        return
    await bot.process_commands(message)

# לולאת הסטטיסטיקות האוטומטית לערוץ סרבר סטטוס (מתעדכן כל 60 שניות)
@tasks.loop(seconds=60)
async def update_discord_radar():
    global status_message
    await bot.wait_until_ready()
    guild = bot.get_guild(GUILD_ID)
    channel = bot.get_channel(STATUS_CHANNEL_ID)
    if not guild or not channel: 
        return
    if len(guild.members) < guild.member_count: 
        await guild.chunk()
    
    total_members = guild.member_count
    bot_count = sum(1 for m in guild.members if m.bot)
    real_humans = total_members - bot_count
    online_members = sum(1 for m in guild.members if m.status in [discord.Status.online, discord.Status.dnd, discord.Status.idle] and not m.bot)
    staff_role = guild.get_role(STAFF_ROLE_ID)
    t_staff = len(staff_role.members) if staff_role else 0
    o_staff = sum(1 for m in staff_role.members if m.status in [discord.Status.online, discord.Status.dnd, discord.Status.idle]) if staff_role else 0

    embed = discord.Embed(
        title=f"⚫ {SERVER_NAME.upper()} | NETWORK MONITOR",
        description="ברוכים הבאים ללוח המידע המרכזי של הרשת.\nהנתונים מסונכרנים ישירות מול ה-API של דיסקורד.\n\n**─── SERVER INFRASTRUCTURE ───**",
        color=0x010101
    )
    embed.add_field(name="👥 חברי הקהילה", value=f"```md\n# Total Members : {total_members}\n* Real Humans   : {real_humans}\n* Online Users  : {online_members}\n```", inline=True)
    embed.add_field(name="🛡️ צוות ניהול", value=f"```md\n# Total Staff   : {t_staff}\n* Staff Online  : {o_staff}\n* Status        : Secured\n```", inline=True)
    embed.set_thumbnail(url=LOGO_URL)
    embed.set_footer(text="⚡ Chicago City Automation Core • Auto Updates")
    embed.timestamp = discord.utils.utcnow()
    try:
        if status_message is None:
            async for m in channel.history(limit=5):
                if m.author == bot.user and m.embeds: 
                    status_message = m
                    break
        if status_message: 
            await status_message.edit(embed=embed)
        else: 
            status_message = await channel.send(embed=embed)
    except: 
        pass

# מערכת ברוכים הבאים מעוצבת פרימיום (Welcome Screen)
@bot.event
async def on_member_join(member):
    if member.guild.id != GUILD_ID: 
        return
    channel = bot.get_channel(WELCOME_CHANNEL_ID)
    if not channel: 
        return
    embed = discord.Embed(
        title="📥 WELCOME TO CHICAGO CITY!",
        description=f"שלום רב {member.mention},\nברוך הבא לשרת הרשמי של Chicago City Roleplay!\n\n"
                    f"**📌 שלבי התאקלמות ראשוניים:**\n"
                    f"1️⃣ כנס לערוץ האימות המרכזי ולחץ על כפתור האימות.\n"
                    f"2️⃣ קרא את חוקי הקהילה בעיון רב על מנת למנוע ענישה.\n\n"
                    f"**─── NETWORK IDENTITY ───**",
        color=0x2ecc71
    )
    embed.add_field(name="👤 שם המשתמש", value=f"```{member.name}```", inline=True)
    embed.add_field(name="🆔 מספר חשבון", value=f"```{member.id}```", inline=True)
    embed.set_thumbnail(url=member.display_avatar.url)
    embed.set_image(url=BANNER_URL)
    embed.set_footer(text=f"Chicago City Member • #{member.guild.member_count}")
    embed.timestamp = discord.utils.utcnow()
    try: 
        await channel.send(embed=embed)
    except: 
        pass
# פנל אימות חשבון השולח לוגים ל-Security Logs
class VerifyView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🔑 אימות חשבון / VERIFY", style=discord.ButtonStyle.green, custom_id="verify_btn_diamond_v11")
    async def verify_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        role = interaction.guild.get_role(VERIFY_ROLE_ID)
        if not role: 
            return await interaction.response.send_message("❌ שגיאה: רול אימות חסר בשרת.", ephemeral=True)
        if role in interaction.user.roles: 
            return await interaction.response.send_message("ℹ️ המערכת זיהתה כי החשבון שלך כבר מאומת.", ephemeral=True)
        
        await interaction.user.add_roles(role)
        await interaction.response.send_message("✅ אושרת בהצלחה! ברוך הבא ל-Chicago City.", ephemeral=True)
        await dispatch_log(LOG_SECURITY, "User Verified", f"User {interaction.user.mention} verified successfully.", 0x2ecc71, {"User": interaction.user.name, "ID": str(interaction.user.id)})

# מודאל שינוי שם טיקט לצוות
class RenameTicketModal(discord.ui.Modal, title="📝 שינוי שם הערוץ"):
    new_name = discord.ui.TextInput(label="שם ערוץ חדש (באותיות קטנות)", placeholder="support-fixed", required=True)
    async def on_submit(self, interaction: discord.Interaction):
        old = interaction.channel.name
        clean = self.new_name.value.lower().replace(" ", "-")
        await interaction.channel.edit(name=clean)
        await interaction.response.send_message(f"✅ שם הערוץ שונה בהצלחה ל: {clean}")
        await dispatch_log(LOG_TICKET, "Ticket Renamed", f"Renamed from {old} to {clean}", 0x3498db, {"Staff": interaction.user.name, "Channel": interaction.channel.name})

# מודאל הוספת משתמש לטיקט באמצעות תיוג ישיר/שם/ID
class AddMemberModal(discord.ui.Modal, title="👤 הוספת חבר לטיקט (תיוג/ID)"):
    member_input = discord.ui.TextInput(label="הזן תיוג, שם או מזהה ID של השחקן", placeholder="@Aharon", required=True)
    async def on_submit(self, interaction: discord.Interaction):
        try:
            converter = commands.MemberConverter()
            member = await converter.convert(await bot.get_context(await interaction.channel.fetch_message(interaction.channel.last_message_id)), self.member_input.value)
        except:
            clean_id = self.member_input.value.replace("<@", "").replace(">", "").replace("!", "")
            try: 
                member = interaction.guild.get_member(int(clean_id)) or await interaction.guild.fetch_member(int(clean_id))
            except: 
                member = discord.utils.get(interaction.guild.members, name=self.member_input.value)
        if member:
            await interaction.channel.set_permissions(member, read_messages=True, send_messages=True, attach_files=True)
            await interaction.response.send_message(f"✅ המשתמש {member.mention} התווסף לטיקט בהצלחה!")
            await dispatch_log(LOG_TICKET, "Member Added", f"Added {member.name} to ticket.", 0x9b59b6, {"Staff": interaction.user.name, "Ticket": interaction.channel.name})
        else: 
            await interaction.response.send_message("❌ שחקן לא נמצא בשרת, ודא שהקלט תקין.", ephemeral=True)

# כפתורי שליטה בתוך הטיקט עם הגנת צוות קשיחה
class TicketControlView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🔒 סגור טיקט / Close", style=discord.ButtonStyle.danger, custom_id="btn_close_v11")
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        staff = interaction.guild.get_role(STAFF_ROLE_ID)
        if staff not in interaction.user.roles and not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message("❌ שגיאה: כפתור זה חסום ומיועד לצוות השרת בלבד!", ephemeral=True)
        await interaction.response.send_message("🛑 הערוץ ייסגר ויימחק מהמערכת בעוד 5 שניות...")
        await dispatch_log(LOG_TICKET, "Ticket Closed", f"Ticket channel {interaction.channel.name} deleted.", 0xe74c3c, {"Staff": interaction.user.name})
        await asyncio.sleep(5)
        await interaction.channel.delete()

    @discord.ui.button(label="🙋‍♂️ קח טיפול / Claim", style=discord.ButtonStyle.success, custom_id="btn_claim_v11")
    async def claim_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        staff = interaction.guild.get_role(STAFF_ROLE_ID)
        if staff not in interaction.user.roles and not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message("❌ שגיאה: כפתור זה חסום ומיועד לצוות השרת בלבד!", ephemeral=True)
        button.disabled, button.label, button.style = True, f"בטיפול: {interaction.user.name}", discord.ButtonStyle.secondary
        await interaction.response.edit_message(view=self)
        await interaction.channel.send(embed=discord.Embed(description=f"💼 הפנייה נלקחה לטיפול של {interaction.user.mention}", color=discord.Color.green()))
        await dispatch_log(LOG_TICKET, "Ticket Claimed", f"Claimed by {interaction.user.name}", 0x2ecc71, {"Channel": interaction.channel.name})

    @discord.ui.button(label="✏️ שינוי שם", style=discord.ButtonStyle.primary, custom_id="btn_rn_v11")
    async def rename_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        staff = interaction.guild.get_role(STAFF_ROLE_ID)
        if staff not in interaction.user.roles and not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message("❌ שגיאה: כפתור זה חסום ומיועד לצוות השרת בלבד!", ephemeral=True)
        await interaction.response.send_modal(RenameTicketModal())

    @discord.ui.button(label="➕ הוסף משתמש", style=discord.ButtonStyle.secondary, custom_id="btn_add_v11")
    async def add_member(self, interaction: discord.Interaction, button: discord.ui.Button):
        staff = interaction.guild.get_role(STAFF_ROLE_ID)
        if staff not in interaction.user.roles and not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message("❌ שגיאה: כפתור זה חסום ומיועד לצוות השרת בלבד!", ephemeral=True)
        await interaction.response.send_modal(AddMemberModal())

# תפריט הבחירה של הטיקטים (Dropdown Selection Interface)
class TicketDropdown(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="דיווח על שחקן / צוות", value="report", emoji="🚨"),
            discord.SelectOption(label="דיווח על באג", value="bug", emoji="🐛"),
            discord.SelectOption(label="בחינה לצוות השרת", value="apply", emoji="📝"),
            discord.SelectOption(label="שאלה כללית / עזרה", value="general", emoji="❓")
        ]
        super().__init__(placeholder="🔽 בחר את קטגוריית הפנייה שלך...", options=options, custom_id="dropdown_v11")

    async def callback(self, interaction: discord.Interaction):
        category = self.values
        guild = interaction.guild
        ticket_name = f"{category}-{interaction.user.name}".lower()
        if discord.utils.get(guild.channels, name=ticket_name):
            return await interaction.response.send_message("❌ כבר יש לך פנייה פתוחה בשרת!", ephemeral=True)
        
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True, attach_files=True),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }
        channel = await guild.create_text_channel(name=ticket_name, overwrites=overwrites)
        embed = discord.Embed(
            title=f"🎫 מרכז תמיכה | קטגוריה: {category.upper()}", 
            description=f"שלום {interaction.user.mention},\nצוות הניהול קיבל את פנייתך.\nאנא פרט את המקרה כאן בצ'אט בצורה מורחבת והעלה הוכחות.", 
            color=0x5865F2
        )
        embed.set_image(url=BANNER_URL)
        await channel.send(embed=embed, view=TicketControlView())
        await interaction.response.send_message(f"✅ פנייה נוצרה בהצלחה: {channel.mention}", ephemeral=True)
        await dispatch_log(LOG_TICKET, "Ticket Opened", f"Opened by {interaction.user.name}", 0xe67e22, {"Channel": channel.name, "Category": category})

class TicketOpenView(discord.ui.View):
    def __init__(self): 
        super().__init__(timeout=None)
        self.add_item(TicketDropdown())
# מודאל יצירת הגרלה חדשה לצוות
class CreateGiveawayModal(discord.ui.Modal, title="🎁 הגרלה חדשה"):
    g_title = discord.ui.TextInput(label="מה הפרס המוגרל?")
    g_time = discord.ui.TextInput(label="זמן לסיום (בדקות בלבד)")
    async def on_submit(self, interaction: discord.Interaction):
        feed = bot.get_channel(GIVEAWAY_FEED_CH)
        embed = discord.Embed(title="🎉 GIVEAWAY OUT | הגרלה חדשה", description=f"🏆 **הפרס:** {self.g_title.value}\n⏰ **זמן לסיום:** {self.g_time.value} דקות\n👑 **יוצר:** {interaction.user.mention}", color=0x2ecc71)
        embed.set_image(url=BANNER_URL)
        msg = await feed.send(embed=embed); await msg.add_reaction("🎉")
        await interaction.response.send_message("✅ ההגרלה נוצרה בהצלחה.", ephemeral=True)

class GiveawayPanelView(discord.ui.View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="🎁 פתח הגרלה חדשה לשחקנים", style=discord.ButtonStyle.green, custom_id="g_p_v11")
    async def open_g(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.guild.get_role(GIVEAWAY_ROLE_ID) not in interaction.user.roles and not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message("❌ שגיאה: פעולה זו מיועדת לצוות הגרלות בלבד!", ephemeral=True)
        await interaction.response.send_modal(CreateGiveawayModal())

# מודאל רישום אזהרה למשתמש
class IssueWarnModal(discord.ui.Modal, title="Warn User"):
    u_id = discord.ui.TextInput(label="מספר ID של השחקן")
    u_reason = discord.ui.TextInput(label="סיבת האזהרה")
    async def on_submit(self, interaction: discord.Interaction):
        feed = bot.get_channel(WARN_FEED_CH)
        try:
            member = interaction.guild.get_member(int(self.u_id.value)) or await interaction.guild.fetch_member(int(self.u_id.value))
            if member.id not in warnings_db: warnings_db[member.id] = []
            warnings_db[member.id].append(self.u_reason.value)
            embed = discord.Embed(title="🚨 WARNING RECORDED", description=f"👤 **שחקן:** {member.mention}\n📝 **סיבה:** {self.u_reason.value}\n👮 **האוכף:** {interaction.user.mention}\n📊 **סך הכל אזהרות:** `{len(warnings_db[member.id])}`", color=0xe67e22)
            embed.set_image(url=BANNER_URL)
            await feed.send(embed=embed); await interaction.response.send_message("✅ האזהרה נרשמה בתיק המשמעת.", ephemeral=True)
        except: await interaction.response.send_message("❌ שגיאה: מספר ה-ID אינו תקין.", ephemeral=True)

# מודאל בדיקת היסטוריית אזהרות
class CheckWarnModal(discord.ui.Modal, title="📋 בדיקת כמות ואזהרים"):
    u_id = discord.ui.TextInput(label="הזן מזהה ID של השחקן")
    async def on_submit(self, interaction: discord.Interaction):
        try:
            member = interaction.guild.get_member(int(self.u_id.value)) or await interaction.guild.fetch_member(int(self.u_id.value))
            warns = warnings_db.get(member.id, [])
            if not warns: return await interaction.response.send_message(f"🟢 השחקן {member.name} נקי מאזהרות.", ephemeral=True)
            await interaction.response.send_message(f"📋 לשחקן {member.mention} יש כעת `{len(warns)}` אזהרות בתיק המשמעת שלו.", ephemeral=True)
        except: await interaction.response.send_message("❌ שחקן לא נמצא.", ephemeral=True)

# מודאל מחיקת אזהרה מתיק
class RemoveWarnModal(discord.ui.Modal, title="🗑️ מחיקת אזהרה מתיק"):
    u_id = discord.ui.TextInput(label="הזן מזהה ID של השחקן")
    async def on_submit(self, interaction: discord.Interaction):
        try:
            uid = int(self.u_id.value)
            if uid in warnings_db and warnings_db[uid]:
                warnings_db[uid].pop()
                await interaction.response.send_message("✅ אזהרה אחרונה נמחקה מתיק המשתמש בהצלחה.", ephemeral=True)
            else: await interaction.response.send_message("❌ אין אזהרות רשומות למשתמש זה.", ephemeral=True)
        except: await interaction.response.send_message("❌ ID שגוי.", ephemeral=True)

class WarnPanelView(discord.ui.View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="⚠️ רשום אזהרה למנהל", style=discord.ButtonStyle.danger, custom_id="btn_w_v11")
    async def issue_w(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.guild.get_role(WARN_STAFF_ROLE_ID) not in interaction.user.roles and not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message("❌ שגיאה: פעולה זו מיועדת להנהלה עליונה בלבד!", ephemeral=True)
        await interaction.response.send_modal(IssueWarnModal())

    @discord.ui.button(label="📋 כמות ואזהרים בתיק", style=discord.ButtonStyle.secondary, custom_id="btn_cw_v11")
    async def check_w(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.guild.get_role(WARN_STAFF_ROLE_ID) not in interaction.user.roles and not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message("❌ שגיאה: פעולה זו מיועדת להנהלה עליונה בלבד!", ephemeral=True)
        await interaction.response.send_modal(CheckWarnModal())

    @discord.ui.button(label="🟢 מחק אזהרה (Unwarn)", style=discord.ButtonStyle.success, custom_id="btn_rw_v11")
    async def remove_w(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.guild.get_role(WARN_STAFF_ROLE_ID) not in interaction.user.roles and not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message("❌ שגיאה: פעולה זו מיועדת להנהלה עליונה בלבד!", ephemeral=True)
        await interaction.response.send_modal(RemoveWarnModal())

# מודאל הגשת הצעה לתיבת רעיונות
class CreateSuggestionModal(discord.ui.Modal, title="Suggestion"):
    s_text = discord.ui.TextInput(label="פרט את תוכן ההצעה שלך כאן", style=discord.TextStyle.paragraph)
    async def on_submit(self, interaction: discord.Interaction):
        feed = bot.get_channel(SUGGEST_FEED_CH)
        embed = discord.Embed(title="💡 הצעה חדשה מהקהילה | SUGGESTION", description=self.s_text.value, color=0xf1c40f)
        embed.set_author(name=interaction.user.name, icon_url=interaction.user.display_avatar.url)
        embed.set_image(url=BANNER_URL)
        msg = await feed.send(embed=embed); await msg.add_reaction("✅"); await msg.add_reaction("❌")
        await interaction.response.send_message("✅ ההצעה שלך הוגשה בהצלחה והועברה להצבעת הקהילה.", ephemeral=True)

class SuggestionsPanelView(discord.ui.View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="🗳️ לחצו כאן והגישו הצעה חדשה לעיר", style=discord.ButtonStyle.primary, custom_id="btn_s_v11")
    async def open_s(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.guild.get_role(VERIFY_ROLE_ID) not in interaction.user.roles and not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message("❌ שגיאה: עליך לעבור אימות (Verify) לפני שתוכל להגיש הצעה!", ephemeral=True)
        await interaction.response.send_modal(CreateSuggestionModal())

# מערכת לוגי רולים אוטומטית המזהה את האחראי לביצוע הפעולה מתוך ה-Audit Logs
@bot.event
async def on_member_update(before, after):
    if before.guild.id != GUILD_ID: return
    guild = after.guild
    if len(before.roles) < len(after.roles):
        new_role = next(role for role in after.roles if role not in before.roles)
        enforcer = "Unknown (API)"
        await asyncio.sleep(1)
        try:
            async for entry in guild.audit_logs(action=discord.AuditLogAction.member_role_update, limit=3):
                if entry.target.id == after.id: enforcer = entry.user.mention; break
        except: pass
        await dispatch_log(LOG_ROLE_ADD, "Role Added", f"למשתמש {after.mention} הוענק רול.\n👑 הוענק על ידי: {enforcer}", 0x2ecc71, {"רול": new_role.name, "ID": str(new_role.id)})
    elif len(before.roles) > len(after.roles):
        rem_role = next(role for role in before.roles if role not in after.roles)
        enforcer = "Unknown (API)"
        await asyncio.sleep(1)
        try:
            async for entry in guild.audit_logs(action=discord.AuditLogAction.member_role_update, limit=3):
                if entry.target.id == after.id: enforcer = entry.user.mention; break
        except: pass
        await dispatch_log(LOG_ROLE_REMOVE, "Role Removed", f"למשתמש {after.mention} הוסר רול.\n👑 הוסר על ידי: {enforcer}", 0xe74c3c, {"רול": rem_role.name, "ID": str(rem_role.id)})

# פקודות הקמה ידניות חסינות המונעות קריסות של חוסר הרשאות
@bot.command()
@commands.has_permissions(administrator=True)
async def setup_verify(ctx):
    try: await ctx.message.delete()
    except: pass
    embed = discord.Embed(title="🔐 מערכת אימות | CHICAGO CITY", description="לחץ על כפתור האימות מטה לקבלת גישה מלאה לכל ערוצי השרת.", color=0x2ecc71)
    embed.set_image(url=BANNER_URL)
    await ctx.send(embed=embed, view=VerifyView())

@bot.command()
@commands.has_permissions(administrator=
