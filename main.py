import os
import asyncio
import discord
from flask import Flask
from threading import Thread
from discord.ext import tasks, commands

# ========================================================
# 1. שרת FLASK מובנה עבור RENDER (WEB INFRA)
# ========================================================
app = Flask('')

@app.route('/')
def home():
    return "Chicago City Diamond Core v9 Invite-Tracker Online"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run_flask)
    t.daemon = True
    t.start()

# ========================================================
# 2. קונפיגורציה קשיחה – ערוצים, רולים וקישורי באנרים
# ========================================================
SERVER_NAME = "Chicago City Roleplay"
GUILD_ID = 1483039214793789483

# שימוש בבאנר המטאלי הרשמי שלכם לכל רכיבי ה-Embed בקוד
LOGO_URL = "https://discordapp.com"
BANNER_URL = "https://discordapp.com"

STATUS_CHANNEL_ID = 1506965475270332476       # סרבר סטטוס
WELCOME_CHANNEL_ID = 1483039215032041530      # ברוכים הבאים
INVITE_TRACKER_CH = 1506417177719210194       # חדר מעקב הזמנות החדש שנתת לי!

GIVEAWAY_FEED_CH = 1483039216366780532
WARN_FEED_CH = 1483039219336347810
SUGGEST_FEED_CH = 1483039217482334253

# רשת ערוצי הלוגים הפנימית
LOG_TICKET = 1483039219654852612
LOG_SECURITY = 1483039220284002367
LOG_ROLE_ADD = 1507881637705420961
LOG_ROLE_REMOVE = 1507881755753971872

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
intents.invites = True # אינטנט הכרחי להפעלת מעקב הזמנות!

bot = commands.Bot(command_prefix="!", intents=intents, chunk_guilds_at_startup=True)
status_message = None
warnings_db = {}
invites_cache = {}

async def dispatch_log(target_id, title, description, color=0x010101, fields=None):
    channel = bot.get_channel(target_id)
    if not channel: return
    embed = discord.Embed(title=f"🛡️ {title.upper()}", description=description, color=color)
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
    
    total_members = guild.member_count
    bot_count = sum(1 for m in guild.members if m.bot)
    real_humans = total_members - bot_count
    online = sum(1 for m in guild.members if m.status in [discord.Status.online, discord.Status.dnd, discord.Status.idle] and not m.bot)
    staff = guild.get_role(STAFF_ROLE_ID)
    t_staff = len(staff.members) if staff else 0
    o_staff = sum(1 for m in staff.members if m.status in [discord.Status.online, discord.Status.dnd, discord.Status.idle]) if staff else 0

    embed = discord.Embed(title=f"⚫ {SERVER_NAME.upper()} | LIVE STATS", description="לוח המידע המרכזי של הרשת.", color=0x010101)
    embed.add_field(name="👥 חברי הקהילה", value=f"```md\n# Total Members : {total_members}\n* Real Humans   : {real_humans}\n* Online Users  : {online}\n```", inline=True)
    embed.add_field(name="🛡️ צוות ניהול", value=f"```md\n# Total Staff   : {t_staff}\n* Staff Online  : {o_staff}\n* Status        : Secured\n```", inline=True)
    embed.set_image(url=BANNER_URL)
    try:
        if status_message is None:
            async for m in channel.history(limit=5):
                if m.author == bot.user and m.embeds: status_message = m; break
        if status_message: await status_message.edit(embed=embed)
        else: status_message = await channel.send(embed=embed)
    except: pass
async def get_invites_dict(guild):
    try: return {invite.code: invite for invite in await guild.invites()}
    except: return {}

@bot.event
async def on_member_join(member):
    if member.guild.id != GUILD_ID: return
    
    # 1. שליחת הודעת ברוכים הבאים קלאסית לערוץ welcome
    w_channel = bot.get_channel(WELCOME_CHANNEL_ID)
    if w_channel:
        w_embed = discord.Embed(title="📥 WELCOME TO CHICAGO CITY!", description=f"שלום רב {member.mention},\nברוך הבא לשרת הרשמי של Chicago City Roleplay!\n\nאנא כנס לערוץ האימות ועבור אימות חשבון כדי לקבל גישה.", color=0x2ecc71)
        w_embed.set_thumbnail(url=member.display_avatar.url)
        w_embed.set_image(url=BANNER_URL)
        try: await w_channel.send(embed=w_embed)
        except: pass

    # 2. מנגנון מעקב הזמנות חכם ושליחת אמבד מפואר לערוץ שביקשת
    track_channel = bot.get_channel(INVITE_TRACKER_CH)
    if not track_channel: return
    
    guild = member.guild
    inviter_text = "לא ידוע / קישור ישיר"
    uses_count = 0
    
    old_invites = invites_cache.get(guild.id, {})
    new_invites = await get_invites_dict(guild)
    invites_cache[guild.id] = new_invites
    
    for code, invite in new_invites.items():
        if code in old_invites and invite.uses > old_invites[code].uses:
            inviter_text = invite.inviter.mention
            uses_count = invite.uses
            break

    embed = discord.Embed(
        title="📥 הצטרפות חדשה - מעקב הזמנות",
        description=f"המשתמש {member.mention} נכנס לשרת.\n\n"
                    f"👑 **הוזמן על ידי:** {inviter_text}\n"
                    f"📊 **סך הכל הזמנות שלו:** `{uses_count}`\n\n"
                    f"**─── NETWORK DATABASE ───**",
        color=0x2ecc71
    )
    embed.add_field(name="🆔 מספר מזהה (ID)", value=f"`{member.id}`", inline=False)
    embed.set_image(url=BANNER_URL)
    embed.set_footer(text=f"Chicago City Member • #{guild.member_count}")
    embed.timestamp = discord.utils.utcnow()
    
    try: await track_channel.send(embed=embed)
    except: pass

class VerifyView(discord.ui.View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="🔑 אימות חשבון / VERIFY", style=discord.ButtonStyle.green, custom_id="verify_btn_diamond_v15")
    async def verify_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        role = interaction.guild.get_role(VERIFY_ROLE_ID)
        if not role: return await interaction.response.send_message("❌ רול אימות חסר.", ephemeral=True)
        if role in interaction.user.roles: return await interaction.response.send_message("ℹ️ אתה כבר מאומת.", ephemeral=True)
        await interaction.user.add_roles(role)
        await interaction.response.send_message("✅ אושרת בהצלחה!", ephemeral=True)
        await dispatch_log(LOG_SECURITY, "User Verified", f"User {interaction.user.mention} verified.", 0x2ecc71, {"User": interaction.user.name, "ID": str(interaction.user.id)})
class RenameTicketModal(discord.ui.Modal, title="📝 שינוי שם הערוץ"):
    new_name = discord.ui.TextInput(label="שם ערוץ חדש", placeholder="support-fixed", required=True)
    async def on_submit(self, interaction: discord.Interaction):
        clean = self.new_name.value.lower().replace(" ", "-")
        await interaction.channel.edit(name=clean)
        await interaction.response.send_message(f"✅ שם הערוץ שונה ל: {clean}")

class AddMemberModal(discord.ui.Modal, title="👤 הוספת חבר לטיקט"):
    member_input = discord.ui.TextInput(label="תייג את המשתמש או הזן מזהה ID", placeholder="@Aharon / 1483039214793789483", required=True)
    async def on_submit(self, interaction: discord.Interaction):
        guild = interaction.guild
        member = None
        raw_input = self.member_input.value.strip()
        clean_id = raw_input.replace("<@", "").replace(">", "").replace("!", "")
        try: member = guild.get_member(int(clean_id)) or await guild.fetch_member(int(clean_id))
        except: member = discord.utils.get(guild.members, name=raw_input)
            
        if member:
            await interaction.channel.set_permissions(member, read_messages=True, send_messages=True, attach_files=True)
            await interaction.response.send_message(f"✅ המשתמש {member.mention} התווסף לטיקט בהצלחה!")
            await dispatch_log(LOG_TICKET, "Member Added", f"Added {member.name}", 0x9b59b6, {"Staff": interaction.user.name})
        else: await interaction.response.send_message("❌ המערכת לא זיהתה את המשתמש.", ephemeral=True)

class TicketControlView(discord.ui.View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="🔒 Close", style=discord.ButtonStyle.danger, custom_id="btn_close_v15")
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        staff = interaction.guild.get_role(STAFF_ROLE_ID)
        if staff not in interaction.user.roles and not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message("❌ חסום לצוות!", ephemeral=True)
        await interaction.response.send_message("🛑 הערוץ ייסגר בעוד 5 שניות...")
        await dispatch_log(LOG_TICKET, "Ticket Closed", f"{interaction.channel.name} deleted.", 0xe74c3c, {"Staff": interaction.user.name})
        await asyncio.sleep(5); await interaction.channel.delete()

    @discord.ui.button(label="🙋‍♂️ Claim", style=discord.ButtonStyle.success, custom_id="btn_claim_v15")
    async def claim_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        staff = interaction.guild.get_role(STAFF_ROLE_ID)
        if staff not in interaction.user.roles and not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message("❌ חסום לצוות!", ephemeral=True)
        button.disabled, button.label, button.style = True, f"בטיפול: {interaction.user.name}", discord.ButtonStyle.secondary
        await interaction.response.edit_message(view=self)
        await interaction.channel.send(embed=discord.Embed(description=f"💼 הפנייה נלקחה לטיפול של {interaction.user.mention}", color=discord.Color.green()))

    @discord.ui.button(label="✏️ שינוי שם", style=discord.ButtonStyle.primary, custom_id="btn_rn_v15")
    async def rename_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        staff = interaction.guild.get_role(STAFF_ROLE_ID)
        if staff not in interaction.user.roles and not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message("❌ חסום לצוות!", ephemeral=True)
        await interaction.response.send_modal(RenameTicketModal())

    @discord.ui.button(label="➕ הוסף משתמש", style=discord.ButtonStyle.secondary, custom_id="btn_add_v15")
    async def add_member(self, interaction: discord.Interaction, button: discord.ui.Button):
        staff = interaction.guild.get_role(STAFF_ROLE_ID)
        if staff not in interaction.user.roles and not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message("❌ חסום לצוות!", ephemeral=True)
        await interaction.response.send_modal(AddMemberModal())

class TicketDropdown(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="דיווח על שחקן / צוות", value="report", emoji="🚨"),
            discord.SelectOption(label="דיווח על באג", value="bug", emoji="🐛"),
            discord.SelectOption(label="בחינה לצוות השרת", value="apply", emoji="📝"),
            discord.SelectOption(label="שאלה כללית / עזרה", value="general", emoji="❓")
        ]
        super().__init__(placeholder="🔽 בחר את קטגוריית הפנייה שלך...", options=options, custom_id="dropdown_v15")

    async def callback(self, interaction: discord.Interaction):
        category = self.values
        guild = interaction.guild
        ticket_name = f"{category}-{interaction.user.name}".lower()
        if discord.utils.get(guild.channels, name=ticket_name):
            return await interaction.response.send_message("❌ כבר יש לך פנייה פתוחה!", ephemeral=True)
        
        staff_role = guild.get_role(STAFF_ROLE_ID)
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True, attach_files=True),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }
        if staff_role: overwrites[staff_role] = discord.PermissionOverwrite(read_messages=True, send_messages=True, attach_files=True)
        
        channel = await guild.create_text_channel(name=ticket_name, overwrites=overwrites)
        embed = discord.Embed(title=f"🎫 מרכז תמיכה | קטגוריה: {category.upper()}", description=f"שלום {interaction.user.mention},\nפרט את המקרה כאן בצ'אט בצורה מורחבת.", color=0x5865F2)
        embed.set_image(url=BANNER_URL)
        await channel.send(embed=embed, view=TicketControlView())
        await interaction.response.send_message(f"✅ פנייה נוצרה: {channel.mention}", ephemeral=True)
        await dispatch_log(LOG_TICKET, "Ticket Opened", f"Opened by {interaction.user.name}", 0xe67e22, {"Channel": channel.name})

class TicketOpenView(discord.ui.View):
    def __init__(self): super().__init__(timeout=None); self.add_item(TicketDropdown())
class CreateGiveawayModal(discord.ui.Modal, title="🎁 הגרלה חדשה"):
    g_title = discord.ui.TextInput(label="מה הפרס?")
    g_time = discord.ui.TextInput(label="זמן בדקות")
    async def on_submit(self, interaction: discord.Interaction):
        feed = bot.get_channel(GIVEAWAY_FEED_CH)
        embed = discord.Embed(title="🎉 GIVEAWAY OUT!", description=f"🏆 פרס: {self.g_title.value}\n⏰ זמן: {self.g_time.value} דקות", color=0x2ecc71)
        embed.set_image(url=BANNER_URL)
        msg = await feed.send(embed=embed); await msg.add_reaction("🎉")
        await interaction.response.send_message("✅ הגרלה נוצרה.", ephemeral=True)

class GiveawayPanelView(discord.ui.View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="🎁 פתח הגרלה חדשה לשחקנים", style=discord.ButtonStyle.green, custom_id="g_p_v15")
    async def open_g(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.guild.get_role(GIVEAWAY_ROLE_ID) not in interaction.user.roles and not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message("❌ פעולה חסומה!", ephemeral=True)
        await interaction.response.send_modal(CreateGiveawayModal())

class IssueWarnModal(discord.ui.Modal, title="Warn User"):
    u_id = discord.ui.TextInput(label="User ID")
    u_reason = discord.ui.TextInput(label="Reason")
    async def on_submit(self, interaction: discord.Interaction):
        feed = bot.get_channel(WARN_FEED_CH)
        try:
            member = interaction.guild.get_member(int(self.u_id.value)) or await interaction.guild.fetch_member(int(self.u_id.value))
            if member.id not in warnings_db: warnings_db[member.id] = []
            warnings_db[member.id].append(self.u_reason.value)
            embed = discord.Embed(title="🚨 WARNING RECORDED", description=f"👤 שחקן: {member.mention}\n📝 סיבה: {self.u_reason.value}", color=0xe67e22)
            embed.set_image(url=BANNER_URL)
            await feed.send(embed=embed); await interaction.response.send_message("✅ אזהרה נרשמה.", ephemeral=True)
        except: await interaction.response.send_message("❌ ID פגום.", ephemeral=True)

class WarnPanelView(discord.ui.View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="⚠️ רשום אזהרה למנהל", style=discord.ButtonStyle.danger, custom_id="w_p_v15")
    async def issue_w(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.guild.get_role(WARN_STAFF_ROLE_ID) not in interaction.user.roles and not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message("❌ פעולה חסומה!", ephemeral=True)
        await interaction.response.send_modal(IssueWarnModal())

class CreateSuggestionModal(discord.ui.Modal, title="Suggestion"):
    s_text = discord.ui.TextInput(label="תוכן ההצעה", style=discord.TextStyle.paragraph)
    async def on_submit(self, interaction: discord.Interaction):
        feed = bot.get_channel(SUGGEST_FEED_CH)
        embed = discord.Embed(title="💡 NEW SUGGESTION", description=self.s_text.value, color=0xf1c40f)
        embed.set_image(url=BANNER_URL)
        msg = await feed.send(embed=embed); await msg.add_reaction("✅"); await msg.add_reaction("❌")
        await interaction.response.send_message("✅ הצעה הוגשה.", ephemeral=True)

class SuggestionsPanelView(discord.ui.View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="🗳️ לחצו כאן והגישו הצעה חדשה לעיר", style=discord.ButtonStyle.primary, custom_id="s_p_v15")
    async def open_s(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.guild.get_role(VERIFY_ROLE_ID) not in interaction.user.roles and not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message("❌ עליך להתאמת קודם!", ephemeral=True)
        await interaction.response.send_modal(CreateSuggestionModal())

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
        await dispatch_log(LOG_ROLE_ADD, "Role Added", f"למשתמש {after.mention} הוענק רול.\n👑 עונק על ידי: {enforcer}", 0x2ecc71, {"רול": new_role.name, "ID": str(new_role.id)})
    elif len(before.roles) > len(after.roles):
        rem_role = next(role for role in before.roles if role not in after.roles)
        enforcer = "Unknown (API)"
        await asyncio.sleep(1)
        try:
            async for entry in guild.audit_logs(action=discord.AuditLogAction.member_role_update, limit=3):
                if entry.target.id == after.id: enforcer = entry.user.mention; break
        except: pass
        await dispatch_log(LOG_ROLE_REMOVE, "Role Removed", f"למשתמש {after.mention} הוסר רול.\n👑 הוסר על ידי: {enforcer}", 0xe74c3c, {"רול": rem_role.name, "ID": str(rem_role.id)})

@bot.command()
@commands.has_permissions(administrator=True)
async def setup_verify(ctx):
    try: await ctx.message.delete()
    except: pass
    embed = discord.Embed(title="🔐 מערכת אימות | CHICAGO CITY", description="לחץ על כפתור האימות מטה לקבלת גישה מלאה לשרת.", color=0x2ecc71)
    embed.set_image(url=BANNER_URL)
    await ctx.send(embed=embed, view=VerifyView())

@bot.command()
@commands.has_permissions(administrator=True)
async def setup_tickets(ctx):
    try: await ctx.message.delete()
    except: pass
    embed = discord.Embed(title="🎫 מרכז תמיכה ופניות | CHICAGO CITY", description="בחר את הקטגוריה המתאימה בתפריט הבחירה מטה לפתיחת פנייה.", color=0x3498db)
    embed.set_image(url=BANNER_URL)
    await ctx.send(embed=embed, view=TicketOpenView())

@bot.command()
@commands.has_permissions(administrator=True)
async def setup_all_panels(ctx):
    try: await ctx.message.delete()
    except: pass
    g_ch = bot.get_channel(1507022943413342328)
    if g_ch: await g_ch.send(embed=discord.Embed(title="🎁 מרכז ניהול הגרלות השחקנים", description="לחצו למטה לפתיחת טופס ההגרלה המהיר!", color=0x2ecc71).set_image(url=BANNER_URL), view=GiveawayPanelView())
    w_ch = bot.get_channel(1507023136095207515)
    if w_ch: await w_ch.send(embed=discord.Embed(title="⚠️ פנל פיקוח ומשמעת הצוות", description="מרכז שליטה חסוי לרישום משמעת בצוות השרת.", color=0xe67e22).set_image(url=BANNER_URL), view=WarnPanelView())
    s_ch = bot.get_channel(1507020507776811068)
    if s_ch: await s_ch.send(embed=discord.Embed(title="💎 תיבת הרעיונות וההצעות של CHICAGO CITY", description="לחצו למטה, מלאו את הטופס וההצעה שלכם עולה ישירות לקהילה!", color=0xf1c40f).set_image(url=BANNER_URL), view=SuggestionsPanelView())

@bot.event
async def on_connect():
    bot.add_view(VerifyView()); bot.add_view(TicketOpenView()); bot.add_view(TicketControlView())
    bot.add_view(GiveawayPanelView()); bot.add_view(WarnPanelView()); bot.add_view(SuggestionsPanelView())

@bot.event
async def on_ready():
    print("====================================")
    print("CHICAGO CITY DIAMOND CORE ONLINE")
    print("====================================")
    await bot.change_presence(activity=None)
    guild = bot.get_guild(GUILD_ID)
    if guild: invites_cache[guild.id] = await get_invites_dict(guild)
    if not update_discord_radar.is_running(): update_discord_radar.start()

if __name__ == "__main__":
    keep_alive()
    token = os.getenv("DISCORD_TOKEN")
    if token: bot.run(token)
