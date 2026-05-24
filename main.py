import os
import asyncio
import random
from flask import Flask
from threading import Thread
import discord
from discord.ext import tasks, commands

# ========================================================
# 1. שרת FLASK הרמטי עבור RENDER (WEB CONSOLE)
# ========================================================
app = Flask('')

@app.route('/')
def home():
    return "Chicago City Diamond Core v6 Online"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run_flask)
    t.daemon = True
    t.start()

# ========================================================
# 2. קונפיגורציה קשיחה ומערך ערוצים (CHICAGO CITY VIP)
# ========================================================
SERVER_NAME = "Chicago City Roleplay"
GUILD_ID = 1483039214793789483

# קישור הלוגו הקבוע והנקי שאינו נמחק לעולם
LOGO_URL = "https://ibb.co"

STATUS_CHANNEL_ID = 1506965475270332476       # סרבר סטטוס
WELCOME_CHANNEL_ID = 1483039215032041530      # חדר ברוכים הבאים
GIVEAWAY_FEED_CH = 1483039216366780532        # פיד הגרלות לשחקנים
WARN_FEED_CH = 1483039219336347810            # פיד אזהרות (#staff-warns)
SUGGEST_FEED_CH = 1483039217482334253         # פיד הצעות להצבעה

# ערוצי רשת הלוגים הבלעדית
LOG_TICKET = 1483039219654852612              # Ticket-logs
LOG_SECURITY = 1483039220284002367             # Security-logs
LOG_ROLE_ADD = 1507881637705420961             # Role-add-log
LOG_ROLE_REMOVE = 1507881755753971872          # Role-remove-log

VERIFY_ROLE_ID = 1483039214793789489
STAFF_ROLE_ID = 1483039215364345930
GIVEAWAY_ROLE_ID = 1506419159414603868
WARN_STAFF_ROLE_ID = 1483039215393702012
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True 
intents.guilds = True         
intents.members = True        
intents.presences = True      

bot = commands.Bot(command_prefix="!", intents=intents, chunk_guilds_at_startup=True)
status_message = None
warnings_db = {}

# פונקציית לוגים יוקרתית השולחת חיוויים לכל חדר לוגים בנפרד
async def dispatch_log(target_channel_id, title, description, color=0x010101, fields=None):
    channel = bot.get_channel(target_channel_id)
    if not channel: return
    embed = discord.Embed(title=f"🛡️ AUDIT | {title.upper()}", description=f"{description}\n\n**─── CORE SYSTEM DATA ───**", color=color)
    if fields:
        for name, value in fields.items():
            embed.add_field(name=f"🔹 {name}", value=f"```yaml\n{value}\n```", inline=True)
    embed.set_thumbnail(url=LOGO_URL)
    embed.set_footer(text="Chicago City Security Core")
    embed.timestamp = discord.utils.utcnow()
    try: await channel.send(embed=embed)
    except: pass

@bot.event
async def on_message(message):
    if message.author.bot: return
    await bot.process_commands(message)

# לולאת הסטטיסטיקות האוטומטית לערוץ סרבר סטטוס
@tasks.loop(seconds=60)
async def update_discord_radar():
    global status_message
    await bot.wait_until_ready()
    guild = bot.get_guild(GUILD_ID)
    channel = bot.get_channel(STATUS_CHANNEL_ID)
    if not guild or not channel: return
    if len(guild.members) < guild.member_count: await guild.chunk()
    
    total_members = guild.member_count
    bot_count = sum(1 for m in guild.members if m.bot)
    real_humans = total_members - bot_count
    online_members = sum(1 for m in guild.members if m.status in [discord.Status.online, discord.Status.dnd, discord.Status.idle] and not m.bot)
    staff = guild.get_role(STAFF_ROLE_ID)
    t_staff = len(staff.members) if staff else 0
    o_staff = sum(1 for m in staff.members if m.status in [discord.Status.online, discord.Status.dnd, discord.Status.idle]) if staff else 0
    boost_count = guild.premium_subscription_count
    boost_level = guild.premium_tier

    embed = discord.Embed(
        title=f"⚫ {SERVER_NAME.upper()} | NETWORK MONITOR", 
        description="**ברוכים הבאים למרכז הנתונים הראשי של הרשת.**\nהמידע הבא מסונכרן ישירות בזמן אמת.\n\n**─── ARCHITECTURE ───**", 
        color=0x010101
    )
    embed.add_field(name="👥 COMMUNITY INFRA", value=f"```md\n# Total Members : {total_members}\n* Real Humans   : {real_humans}\n* Online Users  : {online_members}\n```", inline=True)
    embed.add_field(name="🛡️ OPERATIONS TEAM", value=f"```md\n# Total Staff   : {t_staff}\n* Staff Online  : {o_staff}\n* Status        : Secured\n```", inline=True)
    embed.add_field(name="💎 UPGRADES & BOOSTS", value=f"```⚙️ Server Boosts  : {boost_count} Boosts\n⭐ Premium Tier  : Level {boost_level}\n🔒 Firewall Core : Active```", inline=False)
    embed.set_image(url=LOGO_URL)
    embed.set_footer(text="⚡ Chicago City Sync Engine • Updates Every 60s")
    embed.timestamp = discord.utils.utcnow()
    
    view = discord.ui.View()
    view.add_item(discord.ui.Button(label="🔗 Web Store", url="https://discord.com", style=discord.ButtonStyle.link))
    try:
        if status_message is None:
            async for m in channel.history(limit=5):
                if m.author == bot.user and m.embeds: status_message = m; break
        if status_message: await status_message.edit(embed=embed, view=view)
        else: status_message = await channel.send(embed=embed, view=view)
    except: pass
# ========================================================
# 3. מערכת ברוכים הבאים האוטומטית (WELCOME EMBED)
# ========================================================
@bot.event
async def on_member_join(member):
    if member.guild.id != GUILD_ID: return
    channel = bot.get_channel(WELCOME_CHANNEL_ID)
    if not channel: return
    
    embed = discord.Embed(
        title=f"📥 WELCOME TO {SERVER_NAME.upper()}", 
        description=f"שלום רב {member.mention},\nברוך הבא לשרת הרשמי של **Chicago City Roleplay**!\n\n"
                    f"**📌 שלבי התחלה ראשוניים:**\n"
                    f"1️⃣ גש לערוץ האימות המרכזי ובצע אימות חשבון מהיר.\n"
                    f"2️⃣ קרא את חוקי הקהילה בעיון רב כדי להימנע מאי נעימויות.\n\n"
                    f"**─── IDENTITY IDENTITY ───**", 
        color=0x2ecc71
    )
    embed.add_field(name="👤 שם החשבון", value=f"```yaml\n{member.name}\n```", inline=True)
    embed.add_field(name="🆔 מספר זיהוי דיגיטלי", value=f"```yaml\n{member.id}\n```", inline=True)
    embed.set_thumbnail(url=member.display_avatar.url)
    embed.set_image(url=LOGO_URL)
    embed.set_footer(text=f"Chicago City Member • #{member.guild.member_count}")
    embed.timestamp = discord.utils.utcnow()
    try: await channel.send(embed=embed)
    except: pass

# ========================================================
# 4. מערכת פאנל אימות חשבון (DIAMOND VERIFY SYSTEM)
# ========================================================
class VerifyView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🔑 אימות חשבון / VERIFY", style=discord.ButtonStyle.green, custom_id="verify_btn_v9_diamond")
    async def verify_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        role = interaction.guild.get_role(VERIFY_ROLE_ID)
        if not role: return await interaction.response.send_message("❌ הגדרת רול האימות נכשלה, פנה להנהלה.", ephemeral=True)
        if role in interaction.user.roles: return await interaction.response.send_message("ℹ️ המערכת זיהתה כי החשבון שלך כבר מאומת!", ephemeral=True)
        
        await interaction.user.add_roles(role)
        await interaction.response.send_message("✅ האימות בוצע בהצלחה! ברוך הבא לשרת Chicago City.", ephemeral=True)
        await dispatch_log(LOG_SECURITY, "User Verified", f"User {interaction.user.mention} passed the verification gate.", 0x2ecc71, {"User": interaction.user.name, "ID": str(interaction.user.id)})
# ========================================================
# 5. מערכת מודאלים (חלונות קופצים) לניהול הטיקטים
# ========================================================
class RenameTicketModal(discord.ui.Modal, title="📝 שינוי שם הערוץ"):
    new_name = discord.ui.TextInput(label="הזן שם חדש לערוץ (באותיות קטנות בלבד)", placeholder="support-fixed", required=True)
    async def on_submit(self, interaction: discord.Interaction):
        old = interaction.channel.name
        clean = self.new_name.value.lower().replace(" ", "-")
        await interaction.channel.edit(name=clean)
        await interaction.response.send_message(f"✅ שם הערוץ שונה בהצלחה ל: **{clean}**")
        await dispatch_log(LOG_TICKET, "Ticket Renamed", f"Renamed from {old} to {clean}", 0x3498db, {"Staff": interaction.user.name})

class AddMemberModal(discord.ui.Modal, title="👤 הוספת חבר לטיקט (תיוג / שם / ID)"):
    member_input = discord.ui.TextInput(label="הזן תיוג, שם משתמש או מספר ID של השחקן", placeholder="e.g., @Aharon / 1483039214793789483", required=True)
    async def on_submit(self, interaction: discord.Interaction):
        # מנגנון המרה חסין ומודרני המפענח תיוגים ישירים מהצ'אט
        try:
            converter = commands.MemberConverter()
            member = await converter.convert(await bot.get_context(await interaction.channel.fetch_message(interaction.channel.last_message_id)), self.member_input.value)
        except:
            clean_id = self.member_input.value.replace("<@", "").replace(">", "").replace("!", "")
            try: member = interaction.guild.get_member(int(clean_id)) or await interaction.guild.fetch_member(int(clean_id))
            except: member = discord.utils.get(interaction.guild.members, name=self.member_input.value)
        
        if member:
            await interaction.channel.set_permissions(member, read_messages=True, send_messages=True, attach_files=True)
            await interaction.response.send_message(f"✅ המשתמש {member.mention} התווסף לטיקט בהצלחה!")
            await dispatch_log(LOG_TICKET, "Member Added", f"Added member {member.name} to ticket channel.", 0x9b59b6, {"Staff": interaction.user.name, "Added Target": member.name})
        else:
            await interaction.response.send_message("❌ המערכת לא הצליחה לזהות שחקן כזה, ודא שהקלט תקין.", ephemeral=True)
# ========================================================
# 6. פאנל כפתורי השליטה בתוך הטיקט (STAFF CONTROL)
# ========================================================
class TicketControlView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🔒 סגור טיקט / Close", style=discord.ButtonStyle.danger, custom_id="btn_close_v9_diamond")
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        staff = interaction.guild.get_role(STAFF_ROLE_ID)
        if staff not in interaction.user.roles and not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message("❌ שגיאה: כפתור זה נעול ומיועד לצוות השרת בלבד!", ephemeral=True)
        await interaction.response.send_message("🛑 הערוץ ייסגר ויימחק מהשרת בעוד 5 שניות...")
        await dispatch_log(LOG_TICKET, "Ticket Closed", f"Ticket channel **{interaction.channel.name}** was deleted.", 0xe74c3c, {"Closed By": interaction.user.name})
        await asyncio.sleep(5); await interaction.channel.delete()

    @discord.ui.button(label="🙋‍♂️ קח טיפול / Claim", style=discord.ButtonStyle.success, custom_id="btn_claim_v9_diamond")
    async def claim_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        staff = interaction.guild.get_role(STAFF_ROLE_ID)
        if staff not in interaction.user.roles and not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message("❌ שגיאה: כפתור זה נעול ומיועד לצוות השרת בלבד!", ephemeral=True)
        button.disabled, button.label, button.style = True, f"בטיפול: {interaction.user.name}", discord.ButtonStyle.secondary
        await interaction.response.edit_message(view=self)
        await interaction.channel.send(embed=discord.Embed(description=f"💼 הפנייה נלקחה תחת טיפולו הבלעדי של {interaction.user.mention}", color=discord.Color.green()))
        await dispatch_log(LOG_TICKET, "Ticket Claimed", f"Ticket claimed by staff {interaction.user.name}", 0x2ecc71, {"Staff Member": interaction.user.name})

    @discord.ui.button(label="✏️ שינוי שם", style=discord.ButtonStyle.primary, custom_id="btn_rn_v9_diamond")
    async def rename_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        staff = interaction.guild.get_role(STAFF_ROLE_ID)
        if staff not in interaction.user.roles and not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message("❌ שגיאה: כפתור זה נעול ומיועד לצוות השרת בלבד!", ephemeral=True)
        await interaction.response.send_modal(RenameTicketModal())

    @discord.ui.button(label="➕ הוסף משתמש", style=discord.ButtonStyle.secondary, custom_id="btn_add_v9_diamond")
    async def add_member(self, interaction: discord.Interaction, button: discord.ui.Button):
        staff = interaction.guild.get_role(STAFF_ROLE_ID)
        if staff not in interaction.user.roles and not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message("❌ שגיאה: כפתור זה נעול ומיועד לצוות השרת בלבד!", ephemeral=True)
        await interaction.response.send_modal(AddMemberModal())
# ========================================================
# 7. תפריט הבחירה של הטיקטים (TICKET DROPDOWN INTERFACE)
# ========================================================
class TicketDropdown(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="דיווח על שחקן / צוות", description="Report a player or staff", emoji="🚨", value="report"),
            discord.SelectOption(label="דיווח על באג", description="Report a technical server bug", emoji="🐛", value="bug"),
            discord.SelectOption(label="בחינה לצוות השרת", description="Apply for a staff position", emoji="📝", value="apply"),
            discord.SelectOption(label="שאלה כללית / עזרה", description="General assistance or help", emoji="❓", value="general")
        ]
        super().__init__(placeholder="🔽 בחר את קטגוריית הפנייה שלך...", options=options, custom_id="dropdown_v9_diamond")

    async def callback(self, interaction: discord.Interaction):
        category = self.values[0]
        guild = interaction.guild
        category_titles = {"report": "Report Player/Staff", "bug": "Bug Report", "apply": "Staff Application", "general": "General Help"}
        ticket_prefix = {"report": "report", "bug": "bug", "apply": "apply", "general": "help"}
        ticket_name = f"{ticket_prefix[category]}-{interaction.user.name}".lower()
        
        if discord.utils.get(guild.channels, name=ticket_name):
            return await interaction.response.send_message("❌ כבר זיהינו פנייה פתוחה ופעילה שלך במערכת!", ephemeral=True)
        
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True, attach_files=True),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }
        channel = await guild.create_text_channel(name=ticket_name, overwrites=overwrites)
        
        # בניית הודעת פרימיום מעוצבת לתוך הטיקט שנפתח בלייב ללא קריסות
        embed = discord.Embed(
            title=f"🎫 מרכז פניות | קטגוריה: {category_titles[category]}", 
            description=f"שלום רב {interaction.user.mention},\nצוות הרשת קיבל את פנייתך ויתפנה אליך בהקדם המרבי.\n\n**📋 כיצד להתקדם?**\nאנא פרט וספק את כל המידע וההוכחות הרלוונטיות כאן בצ'אט.\n\n**─── SUPPORT DETAILS ───**", 
            color=0x5865F2
        )
        embed.add_field(name="👤 פותח הפנייה", value=interaction.user.mention, inline=True)
        embed.add_field(name="🛠️ פאנל שליטה", value="אנשי צוות, השתמשו בכפתורים לניהול.", inline=True)
        embed.set_image(url=LOGO_URL)
        embed.set_footer(text="Chicago City Network Support Core")
        embed.timestamp = discord.utils.utcnow()
        
        await channel.send(embed=embed, view=TicketControlView())
        await interaction.response.send_message(f"✅ חדר הפנייה שלך נוצר בהצלחה: {channel.mention}", ephemeral=True)
        await dispatch_log(LOG_TICKET, "Ticket Opened", f"User {interaction.user.name} initialized a ticket channel.", 0xe67e22, {"Category": category_titles[category], "Channel": channel.name})

class TicketOpenView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(TicketDropdown())
# ========================================================
# 11. מערכת לוגי רולים חכמה המזהה את האחראי (Audit Log)
# ========================================================
@bot.event
async def on_member_update(before, after):
    if before.guild.id != GUILD_ID: 
        return
    guild = after.guild
    
    # מקרה א': הוספת רול למשתמש בשרת
    if len(before.roles) < len(after.roles):
        new_role = next(role for role in after.roles if role not in before.roles)
        enforcer = "Unknown (API / Owner)"
        await asyncio.sleep(1) # המתנה קלה לסנכרון ה-Audit Logs בדיסקורד
        try:
            async for entry in guild.audit_logs(action=discord.AuditLogAction.member_role_update, limit=3):
                if entry.target.id == after.id:
                    enforcer = entry.user.mention
                    break
        except: 
            pass
        await dispatch_log(
            target_channel_id=LOG_ROLE_ADD,
            title="Role Allocated",
            description=f"למשתמש {after.mention} הוענק רול חדש בשרת.\n\n👑 **האחראי לביצוע:** {enforcer}",
            color=0x2ecc71,
            fields={"שם הרול": new_role.name, "מזהה רול": str(new_role.id), "שם המשתמש": after.name}
        )
    
    # מקרה ב': הורדת רול ממשתמש בשרת
    elif len(before.roles) > len(after.roles):
        removed_role = next(role for role in before.roles if role not in after.roles)
        enforcer = "Unknown (API / Owner)"
        await asyncio.sleep(1)
        try:
            async for entry in guild.audit_logs(action=discord.AuditLogAction.member_role_update, limit=3):
                if entry.target.id == after.id:
                    enforcer = entry.user.mention
                    break
        except: 
            pass
        await dispatch_log(
            target_channel_id=LOG_ROLE_REMOVE,
            title="Role Revoked",
            description=f"למשתמש {after.mention} הוסר או נמחק רול מהחשבון.\n\n👑 **האחראי לביצוע:** {enforcer}",
            color=0xe74c3c,
            fields={"שם הרול": removed_role.name, "מזהה רול": str(removed_role.id), "שם המשתמש": after.name}
        )

# ========================================================
# 12. פקודות הקמה וניהול ידניות (ADMIN COMMANDS)
# ========================================================
@bot.command()
@commands.has_permissions(administrator=True)
async def setup_verify(ctx):
    await ctx.message.delete()
    embed = discord.Embed(
        title=f"🔐 מערכת אימות חשבון | {SERVER_NAME.upper()}",
        description="על מנת לקבל גישה מלאה לכל ערוצי השרת ולוודא שאינך בוט, אנא לחץ על כפתור האימות המופיע מטה.\n\n"
                    "**⚠️ דגש חשוב:**\nבלחיצה על הכפתור אתה מאשר שקראת והסכמת לחוקי הקהילה ותנאי השימוש.",
        color=0x2ecc71
    )
    embed.set_image(url=BANNER_URL)
    await ctx.send(embed=embed, view=VerifyView())

@bot.command()
@commands.has_permissions(administrator=True)
async def setup_tickets(ctx):
    await ctx.message.delete()
    embed = discord.Embed(
        title=f"🎫 מרכז תמיכה ופניות | {SERVER_NAME.upper()}",
        description="צריך עזרה? נתקלת בבעיה או שברצונך לפתוח פנייה רשמית לצוות השרת?\n"
                    "השתמש בתפריט הבחירה המופיע מטה, בחר את הקטגוריה המתאימה ביותר למקרה שלך, וחדר אישי ייפתח עבורך מול צוות השרת.",
        color=0x3498db
    )
    embed.set_image(url=BANNER_URL)
    await ctx.send(embed=embed, view=TicketOpenView())

@bot.command()
@commands.has_permissions(administrator=True)
async def setup_all_panels(ctx):
    await ctx.message.delete()
    g_ch = bot.get_channel(GIVEAWAY_PANEL_CH)
    if g_ch:
        embed = discord.Embed(title="🎁 מרכז ניהול הגרלות השחקנים", description="לחצו למטה לפתיחת טופס ההגרלה המהיר!", color=0x2ecc71)
        embed.set_image(url=BANNER_URL)
        await g_ch.send(embed=embed, view=GiveawayPanelView())
        
    w_ch = bot.get_channel(WARN_PANEL_CH)
    if w_ch:
        embed = discord.Embed(title="⚠️ פנל פיקוח ומשמעת הצוות", description="מרכז שליטה חסוי לרישום משמעת בצוות השרת.\n\n**🚨 רק דרג ניהול עליון מורשה ללחוץ!**", color=0xe67e22)
        embed.set_image(url=BANNER_URL)
        await w_ch.send(embed=embed, view=WarnPanelView())
        
    s_ch = bot.get_channel(SUGGEST_PANEL_CH)
    if s_ch:
        embed = discord.Embed(title="💎 תיבת הרעיונות וההצעות", description="לחצו למטה, מלאו את הטופס וההצעה שלכם עולה ישירות לקהילה!", color=0xf1c40f)
        embed.set_image(url=BANNER_URL)
        await s_ch.send(embed=embed, view=SuggestionsPanelView())

# ========================================================
# 13. רישום אינטראקציות והתנעת מערכת הבוט (Main Run)
# ========================================================
@bot.event
async def on_connect():
    # רישום קבוע בזיכרון של דיסקורד למניעת שגיאת Interaction failed
    bot.add_view(VerifyView())
    bot.add_view(TicketOpenView())
    bot.add_view(TicketControlView())
    bot.add_view(GiveawayPanelView())
    bot.add_view(WarnPanelView())
    bot.add_view(SuggestionsPanelView())

@bot.event
async def on_ready():
    print("====================================")
    print("CHICAGO CITY DIAMOND CORE SECURED")
    print("====================================")
    await bot.change_presence(activity=None)
    if not update_discord_radar.is_running(): 
        update_discord_radar.start()

if __name__ == "__main__":
    keep_alive()
    token = os.getenv("DISCORD_TOKEN")
    if token: 
        bot.run(token)
