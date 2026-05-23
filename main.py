import os
import asyncio
from flask import Flask
from threading import Thread
import discord
from discord.ext import tasks, commands

# ========================================================
# 1. שרת FLASK פנימי עבור RENDER (WEB INFRASTRUCTURE)
# ========================================================
app = Flask('')

@app.route('/')
def home():
    return "Chicago City Premium Network Core Online"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run_flask)
    t.daemon = True
    t.start()
# ========================================================
# 2. קונפיגורציה קשיחה של ערוצים ורולים (CHICAGO CITY)
# ========================================================
SERVER_NAME = "Chicago City Roleplay"
GUILD_ID = 1483039214793789483

STATUS_CHANNEL_ID = 1506965475270332476
GIVEAWAY_PANEL_CH = 1507022943413342328
GIVEAWAY_FEED_CH = 1483039216366780532
WARN_PANEL_CH = 1507023136095207515
WARN_FEED_CH = 1483039219336347810
SUGGEST_PANEL_CH = 1507020507776811068
SUGGEST_FEED_CH = 1483039217482334253

# רשת הלוגים האוטומטית והמלאה של השרת
LOG_TICKET = 1483039219654852612
LOG_CHANNEL_DELETE = 1483039219654852616
LOG_CHANNEL_CREATE = 1483039219654852617
LOG_CHANNEL_UPDATE = 1483039219923554468
LOG_BAN_ADD = 1483039219923554469
LOG_BAN_REMOVE = 1483039219923554470
LOG_ROLE_CREATE = 1483039219923554471
LOG_ROLE_DELETE = 1483039219923554472
LOG_MEMBER_ADD = 1483039219923554475
LOG_MEMBER_REMOVE = 1483039219923554476
LOG_SECURITY = 1483039220284002367

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

# פונקציית לוגים חכמה לניתוב אוטומטי לפי ערוץ היעד
async def dispatch_log(target_channel_id, title, description, color=0x5865F2, fields=None):
    channel = bot.get_channel(target_channel_id)
    if not channel:
        return
    embed = discord.Embed(title=title, description=description, color=color)
    if fields:
        for name, value in fields.items():
            embed.add_field(name=name, value=value, inline=True)
    embed.set_footer(text="Chicago City Audit System")
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
        title=f"⚫ {SERVER_NAME.upper()} | LIVE SERVER STATISTICS",
        description="ברוכים הבאים ללוח המידע המרכזי של הרשת.\nהנתונים מסונכרנים בזמן אמת מול שרתי דיסקורד.\n\n**─── קהילה ותשתית ───**",
        color=0x010101 
    )
    embed.add_field(name="👥 חברי הקהילה", value=f"```md\n# Total Members : {total_members}\n* Real Humans   : {real_humans}\n* Online Users  : {online_members}\n```", inline=True)
    embed.add_field(name="🛡️ צוות ניהול", value=f"```md\n# Total Staff   : {total_staff}\n* Staff Online  : {online_staff}\n* Status        : Secured\n```", inline=True)
    embed.add_field(name="💎 שדרוגי שרת (Server Boosts)", value=f"```⚙️ Server Boosts  : {boost_count} Boosts\n⭐ Premium Tier  : Level {boost_level}\n🔒 Firewall Core : Active```", inline=False)
    view = discord.ui.View()
    view.add_item(discord.ui.Button(label="🔗 Web Store", url="https://discord.com", style=discord.ButtonStyle.link))
    view.add_item(discord.ui.Button(label="📜 Server Rules", url="https://discord.com", style=discord.ButtonStyle.link))
    if guild.icon: embed.set_thumbnail(url=guild.icon.url)
    embed.set_footer(text="⚡ Chicago City Automation Core • Sync Active")
    embed.timestamp = discord.utils.utcnow()
    try:
        if status_message is None:
            async for msg in channel.history(limit=5):
                if msg.author == bot.user and msg.embeds:
                    status_message = msg
                    break
        if status_message: await status_message.edit(embed=embed, view=view)
        else: status_message = await channel.send(embed=embed, view=view)
    except: pass
class VerifyView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🔑 אימות חשבון / VERIFY", style=discord.ButtonStyle.green, custom_id="verify_btn_v6")
    async def verify_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        role = interaction.guild.get_role(VERIFY_ROLE_ID)
        if not role: return await interaction.response.send_message("❌ שגיאה: רול האימות לא נמצא בשרת.", ephemeral=True)
        if role in interaction.user.roles: return await interaction.response.send_message("ℹ️ המערכת זיהתה כי חשבונך כבר עבר אימות.", ephemeral=True)
        await interaction.user.add_roles(role)
        await interaction.response.send_message("✅ אושרת בהצלחה! ברוך הבא לשרת Chicago City.", ephemeral=True)
        await dispatch_log(
            target_channel_id=LOG_SECURITY,
            title="🔐 User Verification Log",
            description=f"The user {interaction.user.mention} completed system gate verification successfully.",
            color=0x2ecc71,
            fields={"User Name": interaction.user.name, "User ID": str(interaction.user.id)}
        )
class RenameTicketModal(discord.ui.Modal, title="📝 שינוי שם הערוץ"):
    new_name = discord.ui.TextInput(label="הזן שם חדש לערוץ (באותיות קטנות)", placeholder="e.g., support-fixed")
    async def on_submit(self, interaction: discord.Interaction):
        old_name = interaction.channel.name
        clean_name = self.new_name.value.lower().replace(" ", "-")
        await interaction.channel.edit(name=clean_name)
        await interaction.response.send_message(f"✅ שם הערוץ שונה בהצלחה ל: **{clean_name}**")
        await dispatch_log(LOG_TICKET, "✏️ Ticket Rename Audit", f"Ticket channel was updated.", 0x3498db, {"Old Name": old_name, "New Name": clean_name, "Staff": interaction.user.name})

class AddMemberModal(discord.ui.Modal, title="👤 הוספת חבר / נציג לטיקט"):
    member_input = discord.ui.TextInput(label="הזן שם משתמש, תיוג או מספר ID של השחקן", placeholder="e.g., @Aharon / 1483039214793789483")
    async def on_submit(self, interaction: discord.Interaction):
        try:
            converter = commands.MemberConverter()
            member = await converter.convert(await bot.get_context(interaction.message), self.member_input.value)
            if member:
                await interaction.channel.set_permissions(member, read_messages=True, send_messages=True, attach_files=True)
                await interaction.response.send_message(f"✅ המשתמש {member.mention} התווסף לחדר בהצלחה!")
                await dispatch_log(LOG_TICKET, "➕ Member Added to Ticket", f"Access granted to member.", 0x9b59b6, {"Channel": interaction.channel.name, "Added User": member.name, "Staff": interaction.user.name})
            else: await interaction.response.send_message("❌ המשתמש לא נמצא בשרת.", ephemeral=True)
        except: await interaction.response.send_message("❌ שגיאה: המערכת לא הצליחה לזהות את המשתמש לפי הקלט שסיפקת.", ephemeral=True)
class TicketControlView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🔒 סגור פנייה / Close", style=discord.ButtonStyle.danger, custom_id="btn_close_v6")
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("🛑 הפנייה תיסגר ותימחק מהמערכת בעוד 5 שניות...")
        await dispatch_log(LOG_TICKET, "🔒 Ticket Closed & Purged", f"Ticket channel deleted from cluster.", 0xe74c3c, {"Closed By": interaction.user.name, "Channel": interaction.channel.name})
        await asyncio.sleep(5)
        await interaction.channel.delete()

    @discord.ui.button(label="🙋‍♂️ קח טיפול / Claim", style=discord.ButtonStyle.success, custom_id="btn_claim_v6")
    async def claim_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        staff_role = interaction.guild.get_role(STAFF_ROLE_ID)
        if staff_role not in interaction.user.roles and not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message("❌ שגיאה: אין לך הרשאות צוות לקחת טיפול על פנייה זו.", ephemeral=True)
        button.disabled, button.label, button.style = True, f"בטיפול של: {interaction.user.name}", discord.ButtonStyle.secondary
        await interaction.response.edit_message(view=self)
        embed = discord.Embed(description=f"💼 איש הצוות {interaction.user.mention} לקח את הפנייה תחת חסותו.", color=discord.Color.green())
        await interaction.channel.send(embed=embed)
        await dispatch_log(LOG_TICKET, "💼 Ticket Case Claimed", f"Staff took management control.", 0x2ecc71, {"Ticket": interaction.channel.name, "Staff Member": interaction.user.name})

    @discord.ui.button(label="✏️ שינוי שם", style=discord.ButtonStyle.primary, custom_id="btn_rn_v6")
    async def rename_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        staff_role = interaction.guild.get_role(STAFF_ROLE_ID)
        if staff_role not in interaction.user.roles and not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message("❌ פעולה חסומה.", ephemeral=True)
        await interaction.response.send_modal(RenameTicketModal())

    @discord.ui.button(label="➕ הוסף משתמש", style=discord.ButtonStyle.secondary, custom_id="btn_add_v6")
    async def add_member(self, interaction: discord.Interaction, button: discord.ui.Button):
        staff_role = interaction.guild.get_role(STAFF_ROLE_ID)
        if staff_role not in interaction.user.roles and not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message("❌ פעולה חסומה.", ephemeral=True)
        await interaction.response.send_modal(AddMemberModal())
class TicketDropdown(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="דיווח על שחקן / צוות", description="Report a player or staff member infraction", value="report", emoji="🚨"),
            discord.SelectOption(label="דיווח על באג", description="Report a technical server core bug", value="bug", emoji="🐛"),
            discord.SelectOption(label="בחינה לצוות השרת", description="Apply for an official staff position", value="apply", emoji="📝"),
            discord.SelectOption(label="שאלה כללית / עזרה", description="General question or network assistance", value="general", emoji="❓")
        ]
        super().__init__(placeholder="🔽 בחר את קטגוריית הפנייה שלך...", min_values=1, max_values=1, options=options, custom_id="dropdown_v6")

    async def callback(self, interaction: discord.Interaction):
        category = self.values
        guild = interaction.guild
        category_titles = {"report": "Report Player/Staff", "bug": "Bug Report", "apply": "Staff Application", "general": "General Help"}
        ticket_prefix = {"report": "report", "bug": "bug", "apply": "apply", "general": "help"}
        ticket_name = f"{ticket_prefix[category]}-{interaction.user.name}".lower()
        if discord.utils.get(guild.channels, name=ticket_name):
            return await interaction.response.send_message("❌ שגיאה: כבר קיימת פנייה פתוחה תחת שמך במערכת.", ephemeral=True)
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True, attach_files=True),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }
        channel = await guild.create_text_channel(name=ticket_name, overwrites=overwrites)
        embed = discord.Embed(
            title=f"🎫 פנייה חדשה | קטגוריה: {category_titles[category]}",
            description=f"שלום רב {interaction.user.mention},\nצוות הניהול קיבל את פנייתך ויתפנה אליך בהקדם.\n\n**📋 כיצד להתקדם?**\nאנא פרט וספק את כל ההוכחות/מידע הרלוונטי כאן בצ'אט.",
            color=0x5865F2
        )
        embed.add_field(name="👤 פותח הפנייה", value=interaction.user.mention, inline=True)
        embed.add_field(name="🛠️ פאנל ניהול", value="אנשי צוות, השתמשו בכפתורים מטה לניהול המקרה.", inline=True)
        embed.set_footer(text="Chicago City System Support Core")
        embed.timestamp = discord.utils.utcnow()
        await channel.send(embed=embed, view=TicketControlView())
        await interaction.response.send_message(f"✅ פנייתך נוצרה בהצלחה בחדר: {channel.mention}", ephemeral=True)
        await dispatch_log(LOG_TICKET, "📩 Support Ticket Opened", f"New ticket registered in core database cluster.", 0xe67e22, {"Category": category_titles[category], "User": interaction.user.name, "Channel": channel.name})

class TicketOpenView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(TicketDropdown())
class CreateGiveawayModal(discord.ui.Modal, title="🎁 יצירת הגרלה חדשה לשרת"):
    g_title = discord.ui.TextInput(label="מה הפרס של ההגרלה?")
    g_time = discord.ui.TextInput(label="זמן ההגרלה (בדקות בלבד)")
    async def on_submit(self, interaction: discord.Interaction):
        feed = bot.get_channel(GIVEAWAY_FEED_CH)
        embed = discord.Embed(title="🎉 הגרלה חדשה יצאה לדרך! | GIVEAWAY", description=f"**🎁 הפרס המוגרל:**\n```{self.g_title.value}```\n⏰ **זמן לסיום:** {self.g_time.value} דקות\n👑 **יוצר ההגרלה:** {interaction.user.mention}\n\nלחצו 🎉 למטה להשתתפות!", color=0x2ecc71)
        embed.set_footer(text="Chicago City Giveaway System")
        embed.timestamp = discord.utils.utcnow()
        msg = await feed.send(embed=embed)
        await msg.add_reaction("🎉")
        await interaction.response.send_message("✅ ההגרלה נוצרה בהצלחה!", ephemeral=True)

class GiveawayPanelView(discord.ui.View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="🎁 פתח הגרלה חדשה לשחקנים", style=discord.ButtonStyle.green, custom_id="g_panel_v6")
    async def open_g(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.guild.get_role(GIVEAWAY_ROLE_ID) not in interaction.user.roles and not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message("❌ פעולה חסומה.", ephemeral=True)
        await interaction.response.send_modal(CreateGiveawayModal())

class IssueWarnModal(discord.ui.Modal, title="🛡️ רישום אזהרה למשתמש"):
    u_id = discord.ui.TextInput(label="הזן מספר ID של השחקן")
    u_reason = discord.ui.TextInput(label="סיבת האזהרה")
    async def on_submit(self, interaction: discord.Interaction):
        feed = bot.get_channel(WARN_FEED_CH)
        try:
            member = interaction.guild.get_member(int(self.u_id.value)) or await interaction.guild.fetch_member(int(self.u_id.value))
            if member.id not in warnings_db: warnings_db[member.id] = []
            warnings_db[member.id].append(self.u_reason.value)
            embed = discord.Embed(title="🚨 רישום עונש | אזהרה רשמית לצוות", color=0xe67e22)
            embed.add_field(name="👤 משתמש שנאזן", value=member.mention, inline=True)
            embed.add_field(name="👮 האוכף", value=interaction.user.mention, inline=True)
            embed.add_field(name="📝 סיבת האזהרה", value=f"```{self.u_reason.value}```", inline=False)
            embed.add_field(name="📊 סך הכל אזהרות", value=f"`{len(warnings_db[member.id])}`", inline=False)
            embed.set_footer(text="Chicago City Moderation Core")
            embed.timestamp = discord.utils.utcnow()
            await feed.send(embed=embed)
            await interaction.response.send_message("✅ האזהרה נרשמה ותועדה בהצלחה!", ephemeral=True)
        except: await interaction.response.send_message("❌ ID לא תקין.", ephemeral=True)

class WarnPanelView(discord.ui.View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="⚠️ רשום אזהרה למנהל", style=discord.ButtonStyle.danger, custom_id="w_panel_v6")
    async def issue_w(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.guild.get_role(WARN_STAFF_ROLE_ID) not in interaction.user.roles and not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message("❌ פעולה חסומה.", ephemeral=True)
        await interaction.response.send_modal(IssueWarnModal())

class CreateSuggestionModal(discord.ui.Modal, title="💡 הגשת הצעה חדשה לעיר"):
    s_text = discord.ui.TextInput(label="פרט את ההצעה שלך בשלמותה", style=discord.TextStyle.paragraph)
    async def on_submit(self, interaction: discord.Interaction):
        feed = bot.get_channel(SUGGEST_FEED_CH)
        embed = discord.Embed(title="💡 הצעה חדשה מהקהילה", description=f"```{self.s_text.value}```", color=0xf1c40f)
        embed.set_author(name=interaction.user.name, icon_url=interaction.user.display_avatar.url)
        embed.add_field(name="📊 מדד הצבעות", value="הצביעו באמצעות האימוג'ים המופיעים מטה:", inline=False)
        embed.set_footer(text="Chicago City Suggestion Core")
        embed.timestamp = discord.utils.utcnow()
        msg = await feed.send(embed=embed)
        await msg.add_reaction("✅")
        await msg.add_reaction("❌")
        await interaction.response.send_message("✅ ההצעה שלך הוגשה בהצלחה!", ephemeral=True)

class SuggestionsPanelView(discord.ui.View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="🗳️ לחצו כאן והגישו הצעה חדשה לעיר", style=discord.ButtonStyle.primary, custom_id="s_panel_v6")
    async def open_s(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.guild.get_role(VERIFY_ROLE_ID) not in interaction.user.roles and not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message("❌ עליך לעבור אימות תחילה.", ephemeral=True)
        await interaction.response.send_modal(CreateSuggestionModal())
@bot.command()
@commands.has_permissions(administrator=True)
async def setup_all_panels(ctx):
    await ctx.message.delete()
    g_ch = bot.get_channel(GIVEAWAY_PANEL_CH)
    if g_ch: await g_ch.send(embed=discord.Embed(title="🎁 מרכז ניהול הגרלות השחקנים של הצוות", description="מערכת ליצירת הגרלות מעוצבות בשניות בצורה קלה.\n\nלחצו על הכפתור למטה כדי לפתוח את טופס יצירת ההגרלה המהיר!", color=0x2ecc71), view=GiveawayPanelView())
    w_ch = bot.get_channel(WARN_PANEL_CH)
    if w_ch: await w_ch.send(embed=discord.Embed(title="⚠️ פנל פיקוח ומשמעת הצוות", description="מרכז שליטה ואבטחה חסוי לניהול, בדיקה ורישום משמעת בצוות השרת.\n\n**🚨 רק דרג ניהול עליון מורשה לבצע שינויים או מחיקות!**", color=0xe67e22), view=WarnPanelView())
    s_ch = bot.get_channel(SUGGEST_PANEL_CH)
    if s_ch: await s_ch.send(embed=discord.Embed(title="💎 תיבת הרעיונות וההצעות של CHICAGO CITY", description="יש לכם רעיון משוגע ומטורף לשדרוג חווית המשחק בעיר?\n\nלחצו על הכפתור הכחול למטה, מלאו את הטופס שייפתח ויאללה - ההצעה שלכם עולה ישירות לקהילה!", color=0xf1c40f), view=SuggestionsPanelView())

@bot.command()
@commands.has_permissions(administrator=True)
async def setup_verify(ctx):
    await ctx.message.delete()
    await ctx.send(embed=discord.Embed(title="🔐 מערכת אימות | CHICAGO CITY", description="על מנת לקבל גישה מלאה לשרת, אנא לחץ על כפתור האימות המופיע מטה.\n\n**⚠️ שים לב:**\nבלחיצה אתה מאשר שקראת והסכמת לחוקי הקהילה.", color=0x2ecc71), view=VerifyView())

@bot.command()
@commands.has_permissions(administrator=True)
async def setup_tickets(ctx):
    await ctx.message.delete()
    await ctx.send(embed=discord.Embed(title="🎫 מרכז תמיכה ופניות | CHICAGO CITY", description="צריך עזרה? השתמש בתפריט הבחירה המופיע מטה, בחר את הקטגוריה המתאימה וחדר אישי ייפתח עבורך.", color=0x3498db), view=TicketOpenView())
# ========================================================
# 10. מערכת האזנה אוטומטית לאירועי שרת (AUDIT LOG LISTENERS)
# ========================================================
@bot.event
async def on_guild_channel_create(channel):
    await dispatch_log(LOG_CHANNEL_CREATE, "🟢 Channel Created", f"A new channel has been established in the guild cluster.", 0x2ecc71, {"Name": channel.name, "ID": str(channel.id), "Type": str(channel.type)})

@bot.event
async def on_guild_channel_delete(channel):
    await dispatch_log(LOG_CHANNEL_DELETE, "🔴 Channel Deleted", f"A channel layout has been removed from the server database architecture.", 0xe74c3c, {"Name": channel.name, "ID": str(channel.id)})

@bot.event
async def on_guild_channel_update(before, after):
    if before.name != after.name:
        await dispatch_log(LOG_CHANNEL_UPDATE, "✏️ Channel Renamed", f"Channel parameters modified smoothly.", 0x3498db, {"Old Name": before.name, "New Name": after.name, "ID": str(after.id)})

@bot.event
async def on_member_ban(guild, user):
    await dispatch_log(LOG_BAN_ADD, "🔨 Member Banned", f"An infrastructure enforcement ban has been registered against a player.", 0xe74c3c, {"Account": user.name, "ID": str(user.id)})

@bot.event
async def on_member_unban(guild, user):
    await dispatch_log(LOG_BAN_REMOVE, "🔓 Member Unbanned", f"A systemic enforcement pardon has been processed.", 0x2ecc71, {"Account": user.name, "ID": str(user.id)})

@bot.event
async def on_guild_role_create(role):
    await dispatch_log(LOG_ROLE_CREATE, "🎨 Role Created", f"A new permission tier group has been structured.", 0x2ecc71, {"Role Name": role.name, "ID": str(role.id)})

@bot.event
async def on_guild_role_delete(role):
    await dispatch_log(LOG_ROLE_DELETE, "🗑️ Role Removed", f"A permission mapping group tier has been wiped completely.", 0xe74c3c, {"Role Name": role.name, "ID": str(role.id)})

@bot.event
async def on_member_join(member):
    await dispatch_log(LOG_MEMBER_ADD, "📥 User Joined Server", f"A new civilian profile has initialized a secure server session connection.", 0x2ecc71, {"User": member.name, "ID": str(member.id)})

@bot.event
async def on_member_remove(member):
    await dispatch_log(LOG_MEMBER_REMOVE, "📤 User Left Server", f"A network connection session has been severed from the data matrix cluster.", 0xe74c3c, {"User": member.name, "ID": str(member.id)})
# ========================================================
# 12. סנכרון כפתורים קבועים והפעלה רשמית
# ========================================================
@bot.event
async def on_connect():
    # שומר על כל הכפתורים והדרופדאונים פעילים גם אחרי ריסטארט ב-Render
    bot.add_view(VerifyView())
    bot.add_view(TicketOpenView())
    bot.add_view(TicketControlView())
    bot.add_view(GiveawayPanelView())
    bot.add_view(WarnPanelView())
    bot.add_view(SuggestionsPanelView())


@bot.event
async def on_ready():
    print("====================================")
    print(f"CHICAGO PREMIUM ENGINE ONLINE: {bot.user.name.upper()}")
    print("ALL LOG SYSTEM INTEGRATIONS ACTIVE")
    print("====================================")
    
    # הסרת סטטוס ה-Watching מהביו לחלוטין כפי שביקשת
    await bot.change_presence(activity=None)
    
    # הפעלת לולאת הסטטיסטיקות האוטומטית בחדר הסטטוס
    if not update_discord_radar.is_running():
        update_discord_radar.start()


if __name__ == "__main__":
    keep_alive()
    
    token = os.getenv("DISCORD_TOKEN")
    
    if token:
        bot.run(token)
    else:
        print("CRITICAL ERROR: DISCORD_TOKEN environment variable is missing!")
