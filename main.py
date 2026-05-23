import os
import asyncio
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
    return "Chicago City Ultimate Infrastructure is Online!"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run_flask)
    t.daemon = True
    t.start()

# ========================================================
# 2. קונפיגורציה קשיחה של ערוצים ורולים (CHICAGO CITY V1)
# ========================================================
SERVER_NAME = "Chicago City Roleplay"
GUILD_ID = 1483039214793789483

# קישור הלוגו הרשמי של שיקגו סיטי
LOGO_URL = "https://discordapp.com"

# ערוצי פנלים (פרונט לקהילה)
STATUS_CHANNEL_ID = 1506965475270332476       # סרבר סטטוס
WELCOME_CHANNEL_ID = 1483039215032041530      # ערוץ ברוכים הבאים
GIVEAWAY_PANEL_CH = 1507022943413342328
GIVEAWAY_FEED_CH = 1483039216366780532
WARN_PANEL_CH = 1507023136095207515
WARN_FEED_CH = 1483039219336347810
SUGGEST_PANEL_CH = 1507020507776811068
SUGGEST_FEED_CH = 1483039217482334253

# ערוצי רשת הלוגים הרשמית (מנותב אוטומטית לפי קטגוריות)
LOG_TICKET = 1483039219654852612
LOG_CHANNEL_DELETE = 1483039219654852616
LOG_CHANNEL_CREATE = 1483039219654852617
LOG_CHANNEL_UPDATE = 1483039219923554468
LOG_BAN_ADD = 1483039219923554469
LOG_BAN_REMOVE = 1483039219923554470
LOG_MEMBER_ADD = 1483039219923554475
LOG_MEMBER_REMOVE = 1483039219923554476
LOG_SECURITY = 1483039220284002367

# ערוצי לוגים חדשים עבור ניהול רולים שביקשת
LOG_ROLE_ADD = 1507881637705420961
LOG_ROLE_REMOVE = 1507881755753971872

# הגדרות רולים מדויקות
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

# פונקציית לוגים חכמה לניתוב אוטומטי של הודעות Embed לערוצי היעד
async def dispatch_log(target_channel_id, title, description, color=0x5865F2, fields=None):
    channel = bot.get_channel(target_channel_id)
    if not channel:
        return
    embed = discord.Embed(title=title, description=description, color=color)
    if fields:
        for name, value in fields.items():
            embed.add_field(name=name, value=value, inline=True)
    embed.set_thumbnail(url=LOGO_URL)
    embed.set_footer(text="Chicago City Audit Core")
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

# לולאת הסטטיסטיקות האוטומטית לערוץ סרבר סטטוס
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
    total_staff = len(staff_role.members) if staff_role else 0
    online_staff = sum(1 for m in staff_role.members if m.status in [discord.Status.online, discord.Status.dnd, discord.Status.idle]) if staff_role else 0
    boost_count = guild.premium_subscription_count
    boost_level = guild.premium_tier

    embed = discord.Embed(
        title=f"⚫ {SERVER_NAME.upper()} | LIVE STATS",
        description="ברוכים הבאים ללוח המידע המרכזי של הרשת.\nהנתונים המוצגים מטה מסונכרנים ישירות מול ה-API של דיסקורד.\n\n**─── קהילה ותשתית ───**",
        color=0x010101 
    )
    embed.add_field(name="👥 חברי הקהילה", value=f"```md\n# Total Members : {total_members}\n* Real Humans   : {real_humans}\n* Online Users  : {online_members}\n```", inline=True)
    embed.add_field(name="🛡️ צוות ניהול", value=f"```md\n# Total Staff   : {total_staff}\n* Staff Online  : {online_staff}\n* Status        : Secured\n```", inline=True)
    embed.add_field(name="💎 שיפורי שרת (Boosts)", value=f"```⚙️ Server Boosts  : {boost_count} Boosts\n⭐ Premium Tier  : Level {boost_level}\n🔒 Firewall Core : Active```", inline=False)
    
    view = discord.ui.View()
    view.add_item(discord.ui.Button(label="🔗 Web Store", url="https://discord.com", style=discord.ButtonStyle.link))
    embed.set_thumbnail(url=LOGO_URL)
    embed.set_footer(text="⚡ Chicago City Automation Core • Auto Updates Every 60s")
    embed.timestamp = discord.utils.utcnow()

    try:
        if status_message is None:
            async for msg in channel.history(limit=5):
                if msg.author == bot.user and msg.embeds:
                    status_message = msg
                    break
        if status_message:
            await status_message.edit(embed=embed, view=view)
        else:
            status_message = await channel.send(embed=embed, view=view)
    except:
        pass
@bot.event
async def on_member_join(member):
    if member.guild.id != GUILD_ID:
        return
    channel = bot.get_channel(WELCOME_CHANNEL_ID)
    if not channel:
        return
        
    embed = discord.Embed(
        title="📥 ברוכים הבאים ל-CHICAGO CITY!",
        description=f"שלום רב {member.mention},\nברוך הבא לשרת הרשמי של Chicago City Roleplay!\n\n"
                    f"**📌 כיצד להתחיל?**\n"
                    f"1. כנס לערוץ האימות המרכזי ובצע אימות חשבון.\n"
                    f"2. קרא את חוקי הקהילה בעיון רב.\n\n"
                    f"**─── נתוני הצטרפות ───**",
        color=0x2ecc71
    )
    embed.add_field(name="👤 שם המשתמש", value=f"```{member.name}```", inline=True)
    embed.add_field(name="🆔 מספר חשבון", value=f"```{member.id}```", inline=True)
    
    # הצגת תמונת הפרופיל של המשתמש מצד ימין (Thumbnail)
    embed.set_thumbnail(url=member.display_avatar.url)
    # הצגת תמונת הלוגו הגדולה של שיקגו סיטי למטה
    embed.set_image(url=LOGO_URL)
    
    embed.set_footer(text=f"Chicago City Member #{member.guild.member_count}")
    embed.timestamp = discord.utils.utcnow()
    
    try:
        await channel.send(embed=embed)
    except:
        pass
        
    # שליחת דוח אוטומטי לחדר Member-add-log
    await dispatch_log(
        target_channel_id=LOG_MEMBER_ADD,
        title="📥 Member Joined Server",
        description=f"{member.mention} registered to the network database.",
        color=0x2ecc71,
        fields={"Account": member.name, "Account ID": str(member.id)}
    )
class VerifyView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🔑 אימות חשבון / VERIFY", style=discord.ButtonStyle.green, custom_id="verify_btn_v6_final")
    async def verify_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        role = interaction.guild.get_role(VERIFY_ROLE_ID)
        if not role: 
            return await interaction.response.send_message("❌ הגדרת רול האימות נכשלה, פנה למנהל.", ephemeral=True)
        
        if role in interaction.user.roles: 
            return await interaction.response.send_message("ℹ️ החשבון שלך כבר מאומת במערכת שלנו!", ephemeral=True)
        
        await interaction.user.add_roles(role)
        await interaction.response.send_message("✅ האימות בוצע בהצלחה! ברוך הבא לשרת Chicago City.", ephemeral=True)
        
        await dispatch_log(
            target_channel_id=LOG_SECURITY,
            title="🔐 New User Verified",
            description=f"The user {interaction.user.mention} completed verification successfully.",
            color=0x2ecc71,
            fields={"User Name": interaction.user.name, "User ID": str(interaction.user.id)}
        )
class RenameTicketModal(discord.ui.Modal, title="📝 שינוי שם הערוץ"):
    new_name = discord.ui.TextInput(label="הזן שם חדש לערוץ (באותיות קטנות)", placeholder="support-fixed", required=True)

    async def on_submit(self, interaction: discord.Interaction):
        old_name = interaction.channel.name
        clean_name = self.new_name.value.lower().replace(" ", "-")
        await interaction.channel.edit(name=clean_name)
        await interaction.response.send_message(f"✅ שם הערוץ שונה בהצלחה ל: {clean_name}")
        
        await dispatch_log(
            target_channel_id=LOG_TICKET,
            title="✏— Ticket Renamed",
            description=f"Staff {interaction.user.mention} renamed a support ticket channel.",
            color=0x3498db,
            fields={"Old Name": old_name, "New Name": clean_name, "Staff": interaction.user.name}
        )

class AddMemberModal(discord.ui.Modal, title="👤 הוספת חבר לטיקט (תיוג / שם / ID)"):
    member_input = discord.ui.TextInput(label="הזן תיוג, שם משתמש או מספר ID של השחקן", placeholder="e.g., @Aharon / aharon_user / 1483039214793789483", required=True)

    async def on_submit(self, interaction: discord.Interaction):
        # המרת קלט חכמה מכל סוגי הקלטים האפשריים (תיוגים, שמות, מזהים)
        try:
            converter = commands.MemberConverter()
            member = await converter.convert(await bot.get_context(interaction.message if interaction.message else await bot.get_context(await interaction.channel.fetch_message(interaction.channel.last_message_id))), self.member_input.value)
        except:
            # ניסיון חילוץ ידני אם התיוג נכשל להמיר אסינכרונית
            clean_id = self.member_input.value.replace("<@", "").replace(">", "").replace("!", "")
            try:
                member = interaction.guild.get_member(int(clean_id)) or await interaction.guild.fetch_member(int(clean_id))
            except:
                member = discord.utils.get(interaction.guild.members, name=self.member_input.value)
        
        if member:
            await interaction.channel.set_permissions(member, read_messages=True, send_messages=True, attach_files=True)
            await interaction.response.send_message(f"✅ המשתמש {member.mention} התווסף לטיקט בהצלחה!")
            
            await dispatch_log(
                target_channel_id=LOG_TICKET,
                title="➕ Member Added to Ticket",
                description=f"Staff {interaction.user.mention} added a member to a ticket.",
                color=0x9b59b6,
                fields={"Ticket Channel": interaction.channel.name, "Added User": member.name, "Staff": interaction.user.name}
            )
        else:
            await interaction.response.send_message("❌ המערכת לא הצליחה לזהות שחקן כזה בשרת, ודא שהקלט תקין.", ephemeral=True)

class TicketControlView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🔒 סגור טיקט / Close", style=discord.ButtonStyle.danger, custom_id="btn_close_t_v6")
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("🛑 הערוץ יימחק לחלוטין מהמערכת בעוד 5 שניות...")
        await dispatch_log(
            target_channel_id=LOG_TICKET,
            title="🔒 Ticket Closed",
            description=f"Ticket channel **{interaction.channel.name}** was officially closed.",
            color=0xe74c3c,
            fields={"Closed By": interaction.user.name, "Channel": interaction.channel.name}
        )
        await asyncio.sleep(5)
        await interaction.channel.delete()

    @discord.ui.button(label="🙋‍♂️ קח טיפול / Claim", style=discord.ButtonStyle.success, custom_id="btn_claim_t_v6")
    async def claim_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        staff_role = interaction.guild.get_role(STAFF_ROLE_ID)
        if staff_role not in interaction.user.roles and not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message("❌ רק חברי צוות מורשים לקחת טיפול!", ephemeral=True)
        
        button.disabled = True
        button.label = f"Claimed by: {interaction.user.name}"
        button.style = discord.ButtonStyle.secondary
        await interaction.response.edit_message(view=self)
        
        embed = discord.Embed(description=f"💼 הפנייה נלקחה תחת טיפולו הבלעדי של איש הצוות {interaction.user.mention}", color=discord.Color.green())
        await interaction.channel.send(embed=embed)
        
        await dispatch_log(
            target_channel_id=LOG_TICKET,
            title="💼 Ticket Claimed",
            description=f"Staff {interaction.user.mention} claimed a ticket under control.",
            color=0x2ecc71,
            fields={"Ticket": interaction.channel.name, "Staff Member": interaction.user.name}
        )

    @discord.ui.button(label="✏️ שינוי שם", style=discord.ButtonStyle.primary, custom_id="btn_rename_t_v6")
    async def rename_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        staff_role = interaction.guild.get_role(STAFF_ROLE_ID)
        if staff_role not in interaction.user.roles and not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message("❌ אין לך הרשאה מתאימה לביצוע פעולה זו.", ephemeral=True)
        await interaction.response.send_modal(RenameTicketModal())

    @discord.ui.button(label="➕ הוסף משתמש", style=discord.ButtonStyle.secondary, custom_id="btn_add_m_t_v6")
    async def add_member(self, interaction: discord.Interaction, button: discord.ui.Button):
        staff_role = interaction.guild.get_role(STAFF_ROLE_ID)
        if staff_role not in interaction.user.roles and not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message("❌ אין לך הרשאה מתאימה לביצוע פעולה זו.", ephemeral=True)
        await interaction.response.send_modal(AddMemberModal())
class TicketDropdown(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="דיווח על שחקן / צוות", description="Report a player or a staff member", emoji="🚨", value="report"),
            discord.SelectOption(label="דיווח על באג", description="Report a technical server bug", emoji="🐛", value="bug"),
            discord.SelectOption(label="בחינה לצוות השרת", description="Apply for a staff position", emoji="📝", value="apply"),
            discord.SelectOption(label="שאלה כללית / עזרה", description="General question or assistance", emoji="❓", value="general")
        ]
        super().__init__(placeholder="🔽 בחר את קטגוריית הפנייה שלך...", min_values=1, max_values=1, options=options, custom_id="ticket_dropdown_v6_final")

    async def callback(self, interaction: discord.Interaction):
        category = self.values
        guild = interaction.guild
        category_titles = {"report": "Report Player/Staff", "bug": "Bug Report", "apply": "Staff Application", "general": "General Help"}
        ticket_prefix = {"report": "report", "bug": "bug", "apply": "apply", "general": "help"}
        ticket_name = f"{ticket_prefix[category]}-{interaction.user.name}".lower()
        
        existing_channel = discord.utils.get(guild.channels, name=ticket_name)
        if existing_channel:
            return await interaction.response.send_message(f"❌ כבר יש לך פנייה פתוחה במערכת: {existing_channel.mention}", ephemeral=True)
        
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True, attach_files=True),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }
        channel = await guild.create_text_channel(name=ticket_name, overwrites=overwrites)
        
        embed = discord.Embed(
            title=f"🎫 מרכז תמיכה | קטגוריה: {category_titles[category]}",
            description=f"שלום רב {interaction.user.mention},\nצוות הניהול קיבל את פנייתך ויתפנה אליך בהקדם.\n\n**📋 כיצד להתקדם?**\nאנא פרט וספק את כל ההוכחות/מידע הרלוונטי כאן בצ'אט על מנת שנוכל לטפל בך במהירות.",
            color=0x5865F2
        )
        embed.add_field(name="👤 פותח הפנייה", value=interaction.user.mention, inline=True)
        embed.add_field(name="🛠️ פאנל ניהול", value="אנשי צוות, השתמשו בכפתורים מטה לניהול המקרה.", inline=True)
        embed.set_thumbnail(url=LOGO_URL)
        embed.set_footer(text=f"Chicago City Network Support Core")
        embed.timestamp = discord.utils.utcnow()
        
        await channel.send(embed=embed, view=TicketControlView())
        await interaction.response.send_message(f"✅ הפנייה שלך נוצרה בהצלחה בחדר: {channel.mention}", ephemeral=True)
        
        await dispatch_log(
            target_channel_id=LOG_TICKET,
            title="📩 New Ticket Opened",
            description=f"User {interaction.user.mention} opened a support ticket.",
            color=0xe67e22,
            fields={"Category": category_titles[category], "Channel": channel.mention, "User": interaction.user.name}
        )

class TicketOpenView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(TicketDropdown())
class CreateGiveawayModal(discord.ui.Modal, title="🎁 יצירת הגרלה חדשה לשרת"):
    g_title = discord.ui.TextInput(label="מה הפרס של ההגרלה?", placeholder="e.g., 500K Cash / Premium Car", required=True)
    g_time = discord.ui.TextInput(label="זמן ההגרלה (בדקות בלבד)", placeholder="e.g., 60", required=True)

    async def on_submit(self, interaction: discord.Interaction):
        feed_channel = bot.get_channel(GIVEAWAY_FEED_CH)
        if not feed_channel: return await interaction.response.send_message("❌ ערוץ פיד ההגרלות לא נמצא.", ephemeral=True)
        embed = discord.Embed(title=f"🎉 הגרלה חדשה יצאה לדרך! | GIVEAWAY", description=f"**🎁 הפרס המוגרל:**\n```{self.g_title.value}```\n⏰ **זמן לסיום:** {self.g_time.value} דקות\n👑 **יוצר ההגרלה:** {interaction.user.mention}\n\nלחצו על האימוג'י 🎉 למטה כדי להיכנס להגרלה ולהשתתף!", color=0x2ecc71)
        embed.set_thumbnail(url=LOGO_URL)
        msg = await feed_channel.send(embed=embed)
        await msg.add_reaction("🎉")
        await interaction.response.send_message(f"✅ ההגרלה נוצרה ונשלחה ל: {feed_channel.mention}", ephemeral=True)

class GiveawayPanelView(discord.ui.View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="🎁 פתח הגרלה חדשה לשחקנים", style=discord.ButtonStyle.green, custom_id="btn_create_g_v6")
    async def open_giveaway_modal(self, interaction: discord.Interaction, button: discord.ui.Button):
        g_role = interaction.guild.get_role(GIVEAWAY_ROLE_ID)
        if g_role not in interaction.user.roles and not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message("❌ הרשאה זו חסומה עבורך!", ephemeral=True)
        await interaction.response.send_modal(CreateGiveawayModal())

class IssueWarnModal(discord.ui.Modal, title="Warn"):
    u_id = discord.ui.TextInput(label="User ID")
    u_reason = discord.ui.TextInput(label="Reason")
    async def on_submit(self, interaction: discord.Interaction):
        feed_channel = bot.get_channel(WARN_FEED_CH)
        try:
            member = interaction.guild.get_member(int(self.u_id.value)) or await interaction.guild.fetch_member(int(self.u_id.value))
            if member.id not in warnings_db: warnings_db[member.id] = []
            warnings_db[member.id].append(self.u_reason.value)
            embed = discord.Embed(title="🚨 רישום עונש | אזהרה רשמית לצוות", color=0xe67e22)
            embed.add_field(name="👤 משתמש שנאזן", value=member.mention, inline=True)
            embed.add_field(name="📝 סיבה", value=f"```{self.u_reason.value}```", inline=False)
            embed.set_thumbnail(url=LOGO_URL)
            await feed_channel.send(embed=embed)
            await interaction.response.send_message("✅ האזהרה נרשמה בהצלחה.", ephemeral=True)
        except: await interaction.response.send_message("❌ ID לא תקין.", ephemeral=True)

class WarnPanelView(discord.ui.View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="⚠️ רשום אזהרה למנהל", style=discord.ButtonStyle.danger, custom_id="btn_warn_v6")
    async def issue_warn_click(self, interaction: discord.Interaction, button: discord.ui.Button):
        w_role = interaction.guild.get_role(WARN_STAFF_ROLE_ID)
        if w_role not in interaction.user.roles and not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message("❌ פעולה חסומה!", ephemeral=True)
        await interaction.response.send_modal(IssueWarnModal())

class CreateSuggestionModal(discord.ui.Modal, title="Suggestion"):
    s_text = discord.ui.TextInput(label="Suggestion Text", style=discord.TextStyle.paragraph)
    async def on_submit(self, interaction: discord.Interaction):
        feed_channel = bot.get_channel(SUGGEST_FEED_CH)
        embed = discord.Embed(title="💡 הצעה חדשה מהקהילה", description=f"```{self.s_text.value}```", color=0xf1c40f)
        embed.set_thumbnail(url=LOGO_URL)
        msg = await feed_channel.send(embed=embed)
        await msg.add_reaction("✅")
        await msg.add_reaction("❌")
        await interaction.response.send_message("✅ ההצעה הוגשה בהצלחה.", ephemeral=True)

class SuggestionsPanelView(discord.ui.View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="🗳️ לחצו כאן והגישו הצעה חדשה לעיר", style=discord.ButtonStyle.primary, custom_id="btn_suggest_v6")
    async def open_suggest_modal(self, interaction: discord.Interaction, button: discord.ui.Button):
        m_role = interaction.guild.get_role(VERIFY_ROLE_ID)
        if m_role not in interaction.user.roles and not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message("❌ עליך לעבור אימות לפני שתוכל להגיש הצעה!", ephemeral=True)
        await interaction.response.send_modal(CreateSuggestionModal())

# --- מערכת לוגי רולים אוטומטית (Role Add & Remove Audit Logger) ---
@bot.event
async def on_member_update(before, after):
    if before.guild.id != GUILD_ID: return
    if len(before.roles) < len(after.roles):
        new_role = next(role for role in after.roles if role not in before.roles)
        await dispatch_log(LOG_ROLE_ADD, "➕ רול חדש התווסף למשתמש", f"למשתמש {after.mention} הוענק רול חדש במערכת.", 0x2ecc71, {"שם הרול": new_role.name, "מזהה רול": str(new_role.id), "על ידי": "Audit Core Check"})
    elif len(before.roles) > len(after.roles):
        removed_role = next(role for role in before.roles if role not in after.roles)
        await dispatch_log(LOG_ROLE_REMOVE, "🗑️ רול הוסר ממשתמש במערכת", f"למשתמש {after.mention} הוסר או נמחק רול מהחשבון.", 0xe74c3c, {"שם הרול": removed_role.name, "מזהה רול": str(removed_role.id), "על ידי": "Audit Core Check"})

@bot.command()
@commands.has_permissions(administrator=True)
async def setup_all_panels(ctx):
    await ctx.message.delete()
    g_channel = bot.get_channel(GIVEAWAY_PANEL_CH)
    if g_channel:
        embed = discord.Embed(title="🎁 מרכז ניהול הגרלות השחקנים של הצוות", description="לחצו על הכפתור הירוק למטה כדי לפתוח את טופס יצירת ההגרלה המהיר!", color=0x2ecc71)
        embed.set_thumbnail(url=LOGO_URL)
        await g_channel.send(embed=embed, view=GiveawayPanelView())
    w_channel = bot.get_channel(WARN_PANEL_CH)
    if w_channel:
        embed = discord.Embed(title="⚠️ פנל פיקוח ומשמעת הצוות", description="מרכז שליטה ואבטחה חסוי לניהול, בדיקה ורישום משמעת בצוות השרת.\n\n**🚨 רק דרג ניהול עליון מורשה ללחוץ על הכפתורים!**", color=0xe67e22)
        embed.set_thumbnail(url=LOGO_URL)
        await w_channel.send(embed=embed, view=WarnPanelView())
    s_channel = bot.get_channel(SUGGEST_PANEL_CH)
    if s_channel:
        embed = discord.Embed(title="💎 תיבת הרעיונות וההצעות של CHICAGO CITY", description="לחצו על הכפתור הכחול למטה, מלאו את הטופס שייפתח ויאללה - ההצעה שלכם עולה ישירות לקהילה!", color=0xf1c40f)
        embed.set_thumbnail(url=LOGO_URL)
        await s_channel.send(embed=embed, view=SuggestionsPanelView())

@bot.command()
@commands.has_permissions(administrator=True)
async def setup_verify(ctx):
    await ctx.message.delete()
    embed = discord.Embed(title="🔐 מערכת אימות | CHICAGO CITY", description="על מנת לקבל גישה מלאה לשרת, אנא לחץ על כפתור האימות המופיע מטה.\n\n**⚠️ שים לב:**\nבלחיצה אתה מאשר שקראת והסכמת לחוקי הקהילה.", color=0x2ecc71)
    embed.set_thumbnail(url=LOGO_URL)
    await ctx.send(embed=embed, view=VerifyView())

@bot.command()
@commands.has_permissions(administrator=True)
async def setup_tickets(ctx):
    await ctx.message.delete()
    embed = discord.Embed(title="🎫 מרכז תמיכה ופניות | CHICAGO CITY", description="צריך עזרה? השתמש בתפריט הבחירה המופיע מטה, בחר את הקטגוריה המתאימה וחדר אישי ייפתח עבורך.", color=0x3498db)
    embed.set_thumbnail(url=LOGO_URL)
    await ctx.send(embed=embed, view=TicketOpenView())

@bot.event
async def on_connect():
    bot.add_view(VerifyView())
    bot.add_view(TicketOpenView())
    bot.add_view(TicketControlView())
    bot.add_view(GiveawayPanelView())
    bot.add_view(WarnPanelView())
    bot.add_view(SuggestionsPanelView())

@bot.event
async def on_ready():
    print("====================================")
    print(f"CHICAGO PREMIUM ENGINE OPERATIONAL")
    print("====================================")
    await bot.change_presence(activity=None)
    if not update_discord_radar.is_running(): update_discord_radar.start()

if __name__ == "__main__":
    keep_alive()
    token = os.getenv("DISCORD_TOKEN")
    if token: bot.run(token)
