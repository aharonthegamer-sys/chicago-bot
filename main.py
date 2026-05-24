import os
import asyncio
import random
from flask import Flask
from threading import Thread
import discord
from discord.ext import tasks, commands

# ========================================================
# 1. שרת FLASK פנימי עבור RENDER (WEB CONSOLE)
# ========================================================
app = Flask('')

@app.route('/')
def home():
    return "Chicago City Diamond Core V6 is Live!"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run_flask)
    t.daemon = True
    t.start()
# ========================================================
# 2. קונפיגורציה קשיחה – ערוצים ורולים רשמיים
# ========================================================
SERVER_NAME = "Chicago City Roleplay"
GUILD_ID = 1483039214793789483

LOGO_URL = "https://discordapp.com"
BANNER_URL = "https://discordapp.com"

# ערוצי פנלים לקהילה ולצוות (פרונט)
STATUS_CHANNEL_ID = 1506965475270332476       # סרבר סטטוס
WELCOME_CHANNEL_ID = 1483039215032041530      # ברוכים הבאים
VERIFY_PANEL_CH = 1483039214793789489         # חדר אימות (verfiy)
TICKET_PANEL_CH = 1483039218954534966         # חדר טיקטים רשמי (tickets)

GIVEAWAY_PANEL_CH = 1507022943413342328       # פנל ניהול הגרלות
GIVEAWAY_FEED_CH = 1483039216366780532        # פיד הגרלות לשחקנים

WARN_PANEL_CH = 1507023136095207515           # פנל ניהול אזהרות
WARN_FEED_CH = 1483039219336347810            # פיד אזהרות (staff-warns)

SUGGEST_PANEL_CH = 1507020507776811068        # פנל ניהול הצעות
SUGGEST_FEED_CH = 1483039217482334253         # פיד הצעות
# רשת ערוצי הלוגים (תיעוד פנימי בלבד)
LOG_TICKET = 1483039219654852612              # Ticket-logs
LOG_CHANNEL_DELETE = 1483039219654852616       # Channel-delete-log
LOG_CHANNEL_CREATE = 1483039219654852617       # Channel-create-log
LOG_CHANNEL_UPDATE = 1483039219923554468       # Channel-update-log
LOG_BAN_ADD = 1483039219923554469              # Ban-add-log
LOG_BAN_REMOVE = 1483039219923554470           # Ban-remove-log
LOG_MEMBER_ADD = 1483039219923554475           # Member-add-log
LOG_MEMBER_REMOVE = 1483039219923554476        # Member-remove-log
LOG_SECURITY = 1483039220284002367             # Security-logs
LOG_ROLE_ADD = 1507881637705420961             # Role-add-log
LOG_ROLE_REMOVE = 1507881755753971872          # Role-remove-log

# הגדרות מזהי רולים מערכתיים
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

async def dispatch_log(target_channel_id, title, description, color=0x5865F2, fields=None):
    channel = bot.get_channel(target_channel_id)
    if not channel: return
    embed = discord.Embed(title=title, description=description, color=color)
    if fields:
        for name, value in fields.items(): embed.add_field(name=name, value=value, inline=True)
    embed.set_thumbnail(url=LOGO_URL)
    embed.set_footer(text="Chicago City Audit Core")
    embed.timestamp = discord.utils.utcnow()
    try: await channel.send(embed=embed)
    except: pass

@bot.event
async def on_message(message):
    if message.author.bot: return
    await bot.process_commands(message)
@tasks.loop(seconds=60)
async def update_discord_radar():
    global status_message
    await bot.wait_until_ready()
    guild = bot.get_guild(GUILD_ID)
    channel = bot.get_channel(STATUS_CHANNEL_ID)
    if not guild or not channel: return
    if len(guild.members) < guild.member_count: await guild.chunk()
    
    total = guild.member_count
    bots = sum(1 for m in guild.members if m.bot)
    online = sum(1 for m in guild.members if m.status in [discord.Status.online, discord.Status.dnd, discord.Status.idle] and not m.bot)
    staff_role = guild.get_role(STAFF_ROLE_ID)
    t_staff = len(staff_role.members) if staff_role else 0
    o_staff = sum(1 for m in staff_role.members if m.status in [discord.Status.online, discord.Status.dnd, discord.Status.idle]) if staff_role else 0

    embed = discord.Embed(title=f"⚫ {SERVER_NAME.upper()} | LIVE STATS", description="Live statistics panel. Data updates every 60 seconds.", color=0x010101)
    embed.add_field(name="Community Members", value=f"```md\n# Total Members : {total}\n* Real Humans   : {total-bots}\n* Online Users  : {online}\n```", inline=True)
    embed.add_field(name="Staff Status", value=f"```md\n# Total Staff   : {t_staff}\n* Staff Online  : {o_staff}\n* Status        : Secured\n```", inline=True)
    embed.add_field(name="Server Upgrades", value=f"```Server Boosts  : {guild.premium_subscription_count} Boosts\nBoost Level    : Level {guild.premium_tier}\nAnti-Raid Core : Active```", inline=False)
    view = discord.ui.View()
    view.add_item(discord.ui.Button(label="Web Store", url="https://discord.com", style=discord.ButtonStyle.link))
    embed.set_image(url=BANNER_URL)
    try:
        if status_message is None:
            async for msg in channel.history(limit=5):
                if msg.author == bot.user and msg.embeds: status_message = msg; break
        if status_message: await status_message.edit(embed=embed, view=view)
        else: status_message = await channel.send(embed=embed, view=view)
    except: pass

@bot.event
async def on_member_join(member):
    if member.guild.id != GUILD_ID: return
    channel = bot.get_channel(WELCOME_CHANNEL_ID)
    if not channel: return
    embed = discord.Embed(title="📥 WELCOME TO CHICAGO CITY!", description=f"שלום רב {member.mention},\nברוך הבא לשרת הרשמי של Chicago City Roleplay!\n\nאנא בצע אימות חשבון בערוץ האימות וקרא את חוקי הקהילה.", color=0x2ecc71)
    embed.add_field(name="User Info", value=f"Name: {member.name}\nID: {member.id}", inline=True)
    embed.set_thumbnail(url=member.display_avatar.url)
    embed.set_image(url=BANNER_URL)
    try: await channel.send(embed=embed)
    except: pass
    await dispatch_log(LOG_MEMBER_ADD, "Member Joined", f"{member.mention} registered to database.", 0x2ecc71, {"User": member.name, "ID": str(member.id)})
class VerifyView(discord.ui.View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="🔑 אימות חשבון / VERIFY", style=discord.ButtonStyle.green, custom_id="verify_btn_v9_diamond")
    async def verify_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        role = interaction.guild.get_role(VERIFY_ROLE_ID)
        if not role: return await interaction.response.send_message("Role missing.", ephemeral=True)
        if role in interaction.user.roles: return await interaction.response.send_message("Already verified.", ephemeral=True)
        await interaction.user.add_roles(role)
        await interaction.response.send_message("Successfully verified! Welcome.", ephemeral=True)
        await dispatch_log(LOG_SECURITY, "User Verified", f"{interaction.user.mention} verified.", 0x2ecc71, {"Name": interaction.user.name, "ID": str(interaction.user.id)})

class RenameTicketModal(discord.ui.Modal, title="📝 שינוי שם הערוץ"):
    new_name = discord.ui.TextInput(label="הזן שם חדש לערוץ", placeholder="support-fixed", required=True)
    async def on_submit(self, interaction: discord.Interaction):
        old = interaction.channel.name; clean = self.new_name.value.lower().replace(" ", "-")
        await interaction.channel.edit(name=clean)
        await interaction.response.send_message(f"✅ שם הערוץ שונה ל: {clean}")
        await dispatch_log(LOG_TICKET, "Ticket Renamed", f"Staff {interaction.user.mention} renamed ticket.", 0x3498db, {"Old": old, "New": clean})

class AddMemberModal(discord.ui.Modal, title="👤 הוספת חבר לטיקט"):
    member_input = discord.ui.TextInput(label="הזן תיוג, שם משתמש או מספר ID", placeholder="@Aharon / 1483039214793789483", required=True)
    async def on_submit(self, interaction: discord.Interaction):
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
            await dispatch_log(LOG_TICKET, "Member Added", f"{interaction.user.name} added {member.name}", 0x9b59b6)
        else: await interaction.response.send_message("❌ שחקן לא נמצא.", ephemeral=True)
class TicketControlView(discord.ui.View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="🔒 סגור טיקט / Close", style=discord.ButtonStyle.danger, custom_id="btn_close_t_v9")
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        staff_role = interaction.guild.get_role(STAFF_ROLE_ID)
        if staff_role not in interaction.user.roles and not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message("❌ כפתור זה מיועד לצוות השרת בלבד!", ephemeral=True)
        await interaction.response.send_message("🛑 הערוץ יימחק בעוד 5 שניות...")
        await dispatch_log(LOG_TICKET, "Ticket Closed", f"**{interaction.channel.name}** closed.", 0xe74c3c, {"Closed By": interaction.user.name})
        await asyncio.sleep(5); await interaction.channel.delete()

    @discord.ui.button(label="🙋‍♂️ קח טיפול / Claim", style=discord.ButtonStyle.success, custom_id="btn_claim_t_v9")
    async def claim_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        staff_role = interaction.guild.get_role(STAFF_ROLE_ID)
        if staff_role not in interaction.user.roles and not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message("❌ כפתור זה מיועד לצוות השרת בלבד!", ephemeral=True)
        button.disabled, button.label, button.style = True, f"Claimed by: {interaction.user.name}", discord.ButtonStyle.secondary
        await interaction.response.edit_message(view=self)
        await interaction.channel.send(embed=discord.Embed(description=f"💼 פנייה בטיפול של {interaction.user.mention}", color=discord.Color.green()))
        await dispatch_log(LOG_TICKET, "Ticket Claimed", f"Claimed by {interaction.user.name}", 0x2ecc71)

    @discord.ui.button(label="✏️ שינוי שם", style=discord.ButtonStyle.primary, custom_id="btn_rename_t_v9")
    async def rename_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.guild.get_role(STAFF_ROLE_ID) not in interaction.user.roles and not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message("❌ מיועד לצוות בלבד!", ephemeral=True)
        await interaction.response.send_modal(RenameTicketModal())

    @discord.ui.button(label="➕ הוסף משתמש", style=discord.ButtonStyle.secondary, custom_id="btn_add_m_t_v9")
    async def add_member(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.guild.get_role(STAFF_ROLE_ID) not in interaction.user.roles and not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message("❌ מיועד לצוות בלבד!", ephemeral=True)
        await interaction.response.send_modal(AddMemberModal())

class TicketDropdown(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="דיווח על שחקן / צוות", description="Report player/staff", emoji="🚨", value="report"),
            discord.SelectOption(label="דיווח על באג", description="Report a server bug", emoji="🐛", value="bug"),
            discord.SelectOption(label="בחינה לצוות השרת", description="Apply for staff", emoji="📝", value="apply"),
            discord.SelectOption(label="שאלה כללית / עזרה", description="General help", emoji="❓", value="general")
        ]
        super().__init__(placeholder="🔽 בחר את קטגוריית הפנייה שלך...", options=options, custom_id="ticket_dropdown_v9_auto")

    async def callback(self, interaction: discord.Interaction):
        category = self.values
        guild = interaction.guild; ticket_name = f"{category}-{interaction.user.name}".lower()
        if discord.utils.get(guild.channels, name=ticket_name): return await interaction.response.send_message("❌ כבר יש לך פנייה פתוחה!", ephemeral=True)
        overwrites = {guild.default_role: discord.PermissionOverwrite(read_messages=False), interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True, attach_files=True), guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)}
        channel = await guild.create_text_channel(name=ticket_name, overwrites=overwrites)
        embed = discord.Embed(title=f"🎫 מרכז תמיכה | קטגוריה: {category.upper()}", description=f"שלום {interaction.user.mention},\nפרט את המקרה כאן בצ'אט בצורה מורחבת והעלה הוכחות.", color=0x5865F2)
        embed.set_image(url=BANNER_URL)
        await channel.send(embed=embed, view=TicketControlView())
        await interaction.response.send_message(f"✅ פנייה נוצרה: {channel.mention}", ephemeral=True)
        await dispatch_log(LOG_TICKET, "New Ticket Opened", f"Opened by {interaction.user.name}", 0xe67e22, {"Channel": channel.name})

class TicketOpenView(discord.ui.View):
    def __init__(self): super().__init__(timeout=None); self.add_item(TicketDropdown())
class CreateGiveawayModal(discord.ui.Modal, title="🎁 יצירת הגרלה חדשה לשרת"):
    g_title = discord.ui.TextInput(label="מה הפרס?")
    g_time = discord.ui.TextInput(label="זמן (בדקות)")
    async def on_submit(self, interaction: discord.Interaction):
        feed = bot.get_channel(GIVEAWAY_FEED_CH)
        embed = discord.Embed(title="🎉 GIVEAWAY", description=f"**פרס:** {self.g_title.value}\n**זמן:** {self.g_time.value}m", color=0x2ecc71)
        embed.set_image(url=BANNER_URL)
        msg = await feed.send(embed=embed); await msg.add_reaction("🎉")
        await interaction.response.send_message("✅ הגרלה נוצרה.", ephemeral=True)

class GiveawayPanelView(discord.ui.View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="🎁 פתח הגרלה חדשה לשחקנים", style=discord.ButtonStyle.green, custom_id="btn_g_v9_auto")
    async def open_g(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.guild.get_role(GIVEAWAY_ROLE_ID) not in interaction.user.roles and not interaction.user.guild_permissions.administrator: return await interaction.response.send_message("❌ חסום!", ephemeral=True)
        await interaction.response.send_modal(CreateGiveawayModal())

class IssueWarnModal(discord.ui.Modal, title="Warn"):
    u_id = discord.ui.TextInput(label="ID")
    u_reason = discord.ui.TextInput(label="Reason")
    async def on_submit(self, interaction: discord.Interaction):
        feed = bot.get_channel(WARN_FEED_CH)
        try:
            member = interaction.guild.get_member(int(self.u_id.value)) or await interaction.guild.fetch_member(int(self.u_id.value))
            if member.id not in warnings_db: warnings_db[member.id] = []
            warnings_db[member.id].append(self.u_reason.value)
            embed = discord.Embed(title="🚨 WARNING", description=f"User: {member.mention}\nReason: {self.u_reason.value}", color=0xe67e22).set_image(url=BANNER_URL)
            await feed.send(embed=embed); await interaction.response.send_message("✅ אזהרה רשומה.", ephemeral=True)
        except: await interaction.response.send_message("❌ ID פגום.", ephemeral=True)

class CheckWarnModal(discord.ui.Modal, title="📋 בדיקת אזהרות"):
    u_id = discord.ui.TextInput(label="ID")
    async def on_submit(self, interaction: discord.Interaction):
        try:
            uid = int(self.u_id.value); count = len(warnings_db.get(uid, []))
            await interaction.response.send_message(f"📋 למשתמש יש כעת `{count}` אזהרות.", ephemeral=True)
        except: await interaction.response.send_message("❌ שגיאה.", ephemeral=True)

class RemoveWarnModal(discord.ui.Modal, title="🗑️ מחיקת אזהרה"):
    u_id = discord.ui.TextInput(label="ID")
    async def on_submit(self, interaction: discord.Interaction):
        try:
            uid = int(self.u_id.value)
            if uid in warnings_db and warnings_db[uid]: warnings_db[uid].pop(); await interaction.response.send_message("✅ נמחק.", ephemeral=True)
            else: await interaction.response.send_message("❌ אין ווארנים.", ephemeral=True)
        except: await interaction.response.send_message("❌ שגיאה.", ephemeral=True)

class WarnPanelView(discord.ui.View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="⚠️ רשום אזהרה", style=discord.ButtonStyle.danger, custom_id="w1_v9")
    async def w1(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.guild.get_role(WARN_STAFF_ROLE_ID) not in interaction.user.roles and not interaction.user.guild_permissions.administrator: return await interaction.response.send_message("❌ חסום!", ephemeral=True)
        await interaction.response.send_modal(IssueWarnModal())
    @discord.ui.button(label="📋 כמות בתיק", style=discord.ButtonStyle.secondary, custom_id="w2_v9")
    async def w2(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.guild.get_role(WARN_STAFF_ROLE_ID) not in interaction.user.roles and not interaction.user.guild_permissions.administrator: return await interaction.response.send_message("❌ חסום!", ephemeral=True)
        await interaction.response.send_modal(CheckWarnModal())
    @discord.ui.button(label="🟢 מחק אזהרה", style=discord.ButtonStyle.success, custom_id="w3_v9")
    async def w3(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.guild.get_role(WARN_STAFF_ROLE_ID) not in interaction.user.roles and not interaction.user.guild_permissions.administrator: return await interaction.response.send_message("❌ חסום!", ephemeral=True)
        await interaction.response.send_modal(RemoveWarnModal())

class CreateSuggestionModal(discord.ui.Modal, title="Suggestion"):
    s_text = discord.ui.TextInput(label="Suggestion", style=discord.TextStyle.paragraph)
    async def on_submit(self, interaction: discord.Interaction):
        feed = bot.get_channel(SUGGEST_FEED_CH)
        embed = discord.Embed(title="💡 SUGGESTION", description=f"```{self.s_text.value}```", color=0xf1c40f).set_image(url=BANNER_URL)
        msg = await feed.send(embed=embed); await msg.add_reaction("✅"); await msg.add_reaction("❌")
        await interaction.response.send_message("✅ הוגש.", ephemeral=True)

class SuggestionsPanelView(discord.ui.View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="🗳️ הגש הצעה", style=discord.ButtonStyle.primary, custom_id="btn_s_v9_auto")
    async def open_s(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.guild.get_role(VERIFY_ROLE_ID) not in interaction.user.roles and not interaction.user.guild_permissions.administrator: return await interaction.response.send_message("❌ תתאמת קודם!", ephemeral=True)
        await interaction.response.send_modal(CreateSuggestionModal())
@bot.event
async def on_member_update(before, after):
    if before.guild.id != GUILD_ID: return
    guild = after.guild
    if len(before.roles) < len(after.roles):
        new_role = next(role for role in after.roles if role not in before.roles)
        enforcer = "Unknown"
        await asyncio.sleep(1)
        try:
            async for entry in guild.audit_logs(action=discord.AuditLogAction.member_role_update, limit=3):
                if entry.target.id == after.id: enforcer = entry.user.mention; break
        except: pass
        await dispatch_log(LOG_ROLE_ADD, "Role Added", f"למשתמש {after.mention} הוענק רול.\n👑 **אחראי:** {enforcer}", 0x2ecc71, {"רול": new_role.name, "מזהה": str(new_role.id)})
    elif len(before.roles) > len(after.roles):
        removed_role = next(role for role in before.roles if role not in after.roles)
        enforcer = "Unknown"
        await asyncio.sleep(1)
        try:
            async for entry in guild.audit_logs(action=discord.AuditLogAction.member_role_update, limit=3):
                if entry.target.id == after.id: enforcer = entry.user.mention; break
        except: pass
        await dispatch_log(LOG_ROLE_REMOVE, "Role Removed", f"למשתמש {after.mention} הוסר רול.\n👑 **אחראי:** {enforcer}", 0xe74c3c, {"רול": removed_role.name, "מזהה": str(removed_role.id)})
async def run_automatic_setup():
    await bot.wait_until_ready()
    pairs = [(VERIFY_PANEL_CH, "🔐 מערכת אימות | CHICAGO CITY", VerifyView(), 0x2ecc71), (TICKET_PANEL_CH, "🎫 מרכז תמיכה | CHICAGO CITY", TicketOpenView(), 0x3498db), (GIVEAWAY_PANEL_CH, "🎁 מרכז הגרלות צוות", GiveawayPanelView(), 0x2ecc71), (WARN_PANEL_CH, "⚠️ פנל פיקוח משמעת", WarnPanelView(), 0xe67e22), (SUGGEST_PANEL_CH, "💎 תיבת הצעות ורעיונות", SuggestionsPanelView(), 0xf1c40f)]
    for ch_id, title, view_obj, col in pairs:
        ch = bot.get_channel(ch_id)
        if ch:
            try: await ch.purge(limit=10)
            except: pass
            await ch.send(embed=discord.Embed(title=title, color=col).set_image(url=BANNER_URL), view=view_obj)

@bot.event
async def on_connect():
    bot.add_view(VerifyView()); bot.add_view(TicketOpenView()); bot.add_view(TicketControlView())
    bot.add_view(GiveawayPanelView()); bot.add_view(WarnPanelView()); bot.add_view(SuggestionsPanelView())

@bot.event
async def on_ready():
    print("================================"); print("CHICAGO ENGINE SECURED & LIVE"); print("================================")
    await bot.change_presence(activity=None)
    if not update_discord_radar.is_running(): update_discord_radar.start()
    bot.loop.create_task(run_automatic_setup())

if __name__ == "__main__":
    keep_alive()
    token = os.getenv("DISCORD_TOKEN")
    if token: bot.run(token)
