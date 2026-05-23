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
    return "Chicago City Diamond Automation Core v3 is Online!"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run_flask)
    t.daemon = True
    t.start()

# ========================================================
# 2. קונפיגורציה קשיחה ומעודכנת – ניתוב ערוצים סופי
# ========================================================
SERVER_NAME = "Chicago City Roleplay"
GUILD_ID = 1483039214793789483

LOGO_URL = "https://discordapp.com"
BANNER_URL = "https://discordapp.com"

# ערוצי פנלים לקהילה ולצוות - מתוקן ומסודר לפי הקישורים המדויקים שלך!
STATUS_CHANNEL_ID = 1506965475270332476       # חדר סרבר סטטוס
WELCOME_CHANNEL_ID = 1483039215032041530      # חדר ברוכים הבאים
VERIFY_PANEL_CH = 1483039214793789489         # חדר אימות (✔️-verfiy)
TICKET_PANEL_CH = 1483039218954534966         # חדר טיקטים רשמי (חדש ומבודד!)

GIVEAWAY_PANEL_CH = 1507022943413342328       # פנל ניהול הגרלות לצוות
GIVEAWAY_FEED_CH = 1483039216366780532        # פיד הגרלות לשחקנים

WARN_PANEL_CH = 1507023136095207515           # פנל ניהול אזהרות לצוות
WARN_FEED_CH = 1483039219336347810            # פיד אזהרות רשמי (#staff-warns)

SUGGEST_PANEL_CH = 1507020507776811068        # פנל ניהול הצעות
SUGGEST_FEED_CH = 1483039217482334253         # פיד הצעות להצבעה

# רשת ערוצי הלוגים הרשמית (תיעוד פנימי)
LOG_TICKET = 1483039219654852612              # לוג טיקטים (🎫-Ticket-logs)
LOG_CHANNEL_DELETE = 1483039219654852616       # לוג mחיקת חדרים
LOG_CHANNEL_CREATE = 1483039219654852617       # לוג יצירת חדרים
LOG_CHANNEL_UPDATE = 1483039219923554468       # לוג עדכון חדרים
LOG_BAN_ADD = 1483039219923554469              # לוג באנים
LOG_BAN_REMOVE = 1483039219923554470           # לוג הסרת באנים
LOG_MEMBER_ADD = 1483039219923554475           # לוג כניסת חברים
LOG_MEMBER_REMOVE = 1483039219923554476        # לוג עזיבת חברים
LOG_SECURITY = 1483039220284002367             # לוג אבטחה ואימות
LOG_ROLE_ADD = 1507881637705420961             # לוג הוספת רול
LOG_ROLE_REMOVE = 1507881755753971872          # לוג הסרת רול

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
    if member.guild.id != GUILD_ID: return
    channel = bot.get_channel(WELCOME_CHANNEL_ID)
    if not channel: return
        
    embed = discord.Embed(
        title="📥 WELCOME TO CHICAGO CITY!",
        description=f"שלום רב {member.mention},\nברוך הבא לשרת הרשמי של Chicago City Roleplay!\n\n"
                    f"**📌 כיצד להתחיל?**\n"
                    f"1. החשבון שלך מועבר כעת לאימות אוטומטי בערוץ האימות.\n"
                    f"2. קרא את חוקי הקהילה בעיון רב על מנת למנוע ענישה.\n\n"
                    f"**─── נתוני הצטרפות ───**",
        color=0x2ecc71
    )
    embed.add_field(name="👤 שם המשתמש", value=f"```{member.name}```", inline=True)
    embed.add_field(name="🆔 מספר חשבון", value=f"```{member.id}```", inline=True)
    
    embed.set_thumbnail(url=member.display_avatar.url)
    embed.set_image(url=BANNER_URL)
    embed.set_footer(text=f"Chicago City Member #{member.guild.member_count}")
    embed.timestamp = discord.utils.utcnow()
    
    try: await channel.send(embed=embed)
    except: pass
        
    await dispatch_log(LOG_MEMBER_ADD, "Member Joined", f"{member.mention} registered to database.", 0x2ecc71, {"Account": member.name, "ID": str(member.id)})
class VerifyView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🔑 אימות חשבון / VERIFY", style=discord.ButtonStyle.green, custom_id="verify_btn_v8_final")
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
            title="User Verified",
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
        await dispatch_log(LOG_TICKET, "Ticket Renamed", f"Staff {interaction.user.mention} renamed ticket.", 0x3498db, {"Old": old_name, "New": clean_name})

class AddMemberModal(discord.ui.Modal, title="👤 הוספת חבר לטיקט (תיוג / שם / ID)"):
    member_input = discord.ui.TextInput(label="הזן תיוג, שם משתמש או מספר ID של השחקן", placeholder="e.g., @Aharon / 1483039214793789483", required=True)

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
        else:
            await interaction.response.send_message("❌ שחקן לא נמצא.", ephemeral=True)

class TicketControlView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🔒 סגור טיקט / Close", style=discord.ButtonStyle.danger, custom_id="btn_close_t_v8")
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        staff_role = interaction.guild.get_role(STAFF_ROLE_ID)
        if staff_role not in interaction.user.roles and not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message("❌ אבטחה: כפתור זה חסום עבורך ונועד לצוות השרת בלבד!", ephemeral=True)
            
        await interaction.response.send_message("🛑 הערוץ יימחק בעוד 5 שניות...")
        await dispatch_log(LOG_TICKET, "Ticket Closed", f"**{interaction.channel.name}** closed.", 0xe74c3c, {"Closed By": interaction.user.name})
        await asyncio.sleep(5)
        await interaction.channel.delete()

    @discord.ui.button(label="🙋‍♂️ קח טיפול / Claim", style=discord.ButtonStyle.success, custom_id="btn_claim_t_v8")
    async def claim_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        staff_role = interaction.guild.get_role(STAFF_ROLE_ID)
        if staff_role not in interaction.user.roles and not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message("❌ אבטחה: כפתור זה חסום עבורך ונועד לצוות השרת בלבד!", ephemeral=True)
            
        button.disabled, button.label, button.style = True, f"Claimed by: {interaction.user.name}", discord.ButtonStyle.secondary
        await interaction.response.edit_message(view=self)
        await interaction.channel.send(embed=discord.Embed(description=f"💼 פנייה בטיפול של {interaction.user.mention}", color=discord.Color.green()))
        await dispatch_log(LOG_TICKET, "Ticket Claimed", f"Claimed by {interaction.user.name}", 0x2ecc71)

    @discord.ui.button(label="✏️ שינוי שם", style=discord.ButtonStyle.primary, custom_id="btn_rename_t_v8")
    async def rename_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        staff_role = interaction.guild.get_role(STAFF_ROLE_ID)
        if staff_role not in interaction.user.roles and not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message("❌ אבטחה: כפתור זה חסום עבורך ונועד לצוות השרת בלבד!", ephemeral=True)
        await interaction.response.send_modal(RenameTicketModal())

    @discord.ui.button(label="➕ הוסף משתמש", style=discord.ButtonStyle.secondary, custom_id="btn_add_m_t_v8")
    async def add_member(self, interaction: discord.Interaction, button: discord.ui.Button):
        staff_role = interaction.guild.get_role(STAFF_ROLE_ID)
        if staff_role not in interaction.user.roles and not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message("❌ אבטחה: כפתור זה חסום עבורך ונועד לצוות השרת בלבד!", ephemeral=True)
        await interaction.response.send_modal(AddMemberModal())

class TicketDropdown(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="דיווח על שחקן / צוות", description="Report a player or staff", emoji="🚨", value="report"),
            discord.SelectOption(label="דיווח על באג", description="Report a server bug", emoji="🐛", value="bug"),
            discord.SelectOption(label="בחינה לצוות השרת", description="Apply for staff", emoji="📝", value="apply"),
            discord.SelectOption(label="שאלה כללית / עזרה", description="General help", emoji="❓", value="general")
        ]
        super().__init__(placeholder="🔽 בחר את קטגוריית הפנייה שלך...", options=options, custom_id="ticket_dropdown_v8_auto")

    async def callback(self, interaction: discord.Interaction):
        category = self.values
        guild = interaction.guild
        ticket_name = f"{category}-{interaction.user.name}".lower()
        if discord.utils.get(guild.channels, name=ticket_name):
            return await interaction.response.send_message("❌ כבר יש לך פנייה פתוחה!", ephemeral=True)
        
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True, attach_files=True),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }
        channel = await guild.create_text_channel(name=ticket_name, overwrites=overwrites)
        embed = discord.Embed(title=f"🎫 מרכז תמיכה | קטגוריה: {category.upper()}", description=f"שלום {interaction.user.mention},\nפרט את המקרה כאן בצ'אט בצורה מורחבת והעלה הוכחות.", color=0x5865F2)
        embed.set_image(url=BANNER_URL)
        await channel.send(embed=embed, view=TicketControlView())
        await interaction.response.send_message(f"✅ פנייה נוצרה: {channel.mention}", ephemeral=True)
        await dispatch_log(LOG_TICKET, "New Ticket Opened", f"Opened by {interaction.user.name}", 0xe67e22, {"Channel": channel.name})

class TicketOpenView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(TicketDropdown())
class GiveawayControlView(discord.ui.View):
    def __init__(self, prize):
        super().__init__(timeout=None)
        self.prize = prize

    @discord.ui.button(label="🔒 סגור הגרלה / Close", style=discord.ButtonStyle.danger, custom_id="btn_close_giveaway_feed")
    async def close_giveaway(self, interaction: discord.Interaction, button: discord.ui.Button):
        g_role = interaction.guild.get_role(GIVEAWAY_ROLE_ID)
        if g_role not in interaction.user.roles and not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message("❌ אבטחה: כפתור זה חסום עבורך ונועד למנהלי הגרלות בלבד!", ephemeral=True)

        message = interaction.message
        reactions = message.reactions
        entrants = []
        for rx in reactions:
            if str(rx.emoji) == "🎉":
                users = [user async for user in rx.users() if not user.bot]
                entrants.extend(users)
                break

        if not entrants:
            embed = discord.Embed(title="🎁 הגרלה הסתיימה", description=f"**הפרס:** {self.prize}\n\n❌ לא נרשמו מספיק משתתפים להגרלה.", color=0xe74c3c)
            embed.set_image(url=BANNER_URL)
            await message.edit(embed=embed, view=None)
            return await interaction.response.send_message("✅ ההגרלה נסגרה ללא זוכה.", ephemeral=True)

        winner = random.choice(entrants)
        embed = discord.Embed(title="🎉 הגרלה הסתיימה! | WINNER", description=f"**🎁 הפרס המוגרל:** {self.prize}\n\n👑 **הזוכה המאושר:** {winner.mention}\n\nכל הכבוד לזוכה! פנה לצוות לקבלת הפרס.", color=0x9b59b6)
        embed.set_image(url=BANNER_URL)
        await message.edit(embed=embed, view=self)
        await interaction.channel.send(f"🎉 **מזל טוב {winner.mention}! זכית ב: {self.prize}**")
        await interaction.response.send_message("✅ ההגרלה הסתיימה והזוכה הוכרז!", ephemeral=True)

    @discord.ui.button(label="🎲 הגרל מחדש / Reroll", style=discord.ButtonStyle.primary, custom_id="btn_reroll_giveaway_feed")
    async def reroll_giveaway(self, interaction: discord.Interaction, button: discord.ui.Button):
        g_role = interaction.guild.get_role(GIVEAWAY_ROLE_ID)
        if g_role not in interaction.user.roles and not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message("❌ אבטחה: כפתור זה חסום עבורך ונועד למנהלי הגרלות בלבד!", ephemeral=True)

        message = interaction.message
        reactions = message.reactions
        entrants = []
        for rx in reactions:
            if str(rx.emoji) == "🎉":
                users = [user async for user in rx.users() if not user.bot]
                entrants.extend(users)
                break

        if not entrants:
            return await interaction.response.send_message("❌ אין משתתפים לביצוע הגרלה מחדש.", ephemeral=True)

        winner = random.choice(entrants)
        await interaction.channel.send(f"🎲 **REROLL:** הזוכה החדש בפרס **{self.prize}** הוא: {winner.mention}! מזל טוב!")
        await interaction.response.send_message("✅ הגרלה מחדש בוצעה בהצלחה!", ephemeral=True)

class CreateGiveawayModal(discord.ui.Modal, title="🎁 יצירת הגרלה חדשה לשרת"):
    g_title = discord.ui.TextInput(label="מה הפרס של ההגרלה?")
    g_time = discord.ui.TextInput(label="זמן ההגרלה (בדקות)")

    async def on_submit(self, interaction: discord.Interaction):
        feed = bot.get_channel(GIVEAWAY_FEED_CH)
        embed = discord.Embed(title=f"🎉 הגרלה חדשה יצאה לדרך! | GIVEAWAY", description=f"**🎁 הפרס המוגרל:**\n```{self.g_title.value}```\n⏰ **זמן לסגירה ידנית על ידי המנהל**\n👑 **יוצר ההגרלה:** {interaction.user.mention}\n\nלחצו על האימוג'י 🎉 למטה כדי להיכנס להגרלה ולהשתתף!", color=0x2ecc71)
        embed.set_image(url=BANNER_URL)
        msg = await feed.send(embed=embed, view=GiveawayControlView(self.g_title.value))
        await msg.add_reaction("🎉")
        await interaction.response.send_message("✅ הגרלה נוצרה.", ephemeral=True)

class GiveawayPanelView(discord.ui.View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="🎁 פתח הגרלה חדשה לשחקנים", style=discord.ButtonStyle.green, custom_id="btn_g_v8_auto")
    async def open_g(self, interaction: discord.Interaction, button: discord.ui.Button):
        g_role = interaction.guild.get_role(GIVEAWAY_ROLE_ID)
        if g_role not in interaction.user.roles and not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message("❌ אבטחה: כפתור זה חסום עבורך ונועד למנהלי הגרלות בלבד!", ephemeral=True)
        await interaction.response.send_modal(CreateGiveawayModal())

class IssueWarnModal(discord.ui.Modal, title="Warn"):
    u_id = discord.ui.TextInput(label="User ID")
    u_reason = discord.ui.TextInput(label="Reason")
    async def on_submit(self, interaction: discord.Interaction):
        feed = bot.get_channel(WARN_FEED_CH)
        try:
            member = interaction.guild.get_member(int(self.u_id.value)) or await interaction.guild.fetch_member(int(self.u_id.value))
            if member.id not in warnings_db: warnings_db[member.id] = []
            warnings_db[member.id].append(self.u_reason.value)
            embed = discord.Embed(title="🚨 רישום עונש | אזהרה רשמית לצוות", color=0xe67e22)
            embed.add_field(name="👤 משתמש שנאזן", value=member.mention, inline=True)
            embed.add_field(name="📝 סיבה", value=f"```{self.u_reason.value}```", inline=False)
            embed.set_image(url=BANNER_URL)
            await feed.send(embed=embed)
            await interaction.response.send_message("✅ אזהרה נרשמה.", ephemeral=True)
        except: await interaction.response.send_message("❌ ID פגום.", ephemeral=True)

class WarnPanelView(discord.ui.View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="⚠️ רשום אזהרה למנהל", style=discord.ButtonStyle.danger, custom_id="btn_w_v8_auto")
    async def issue_w(self, interaction: discord.Interaction, button: discord.ui.Button):
        w_role = interaction.guild.get_role(WARN_STAFF_ROLE_ID)
        if w_role not in interaction.user.roles and not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message("❌ אבטחה: כפתור זה חסום עבורך ונועד לצוות עליון בלבד!", ephemeral=True)
        await interaction.response.send_modal(IssueWarnModal())

class CreateSuggestionModal(discord.ui.Modal, title="Suggestion"):
    s_text = discord.ui.TextInput(label="Suggestion", style=discord.TextStyle.paragraph)
    async def on_submit(self, interaction: discord.Interaction):
        feed = bot.get_channel(SUGGEST_FEED_CH)
        embed = discord.Embed(title="💡 הצעה חדשה מהקהילה", description=f"```{self.s_text.value}```", color=0xf1c40f)
        embed.set_image(url=BANNER_URL)
        msg = await feed.send(embed=embed)
        await msg.add_reaction("✅")
        await msg.add_reaction("❌")
        await interaction.response.send_message("✅ הצעה הוגשה.", ephemeral=True)

class SuggestionsPanelView(discord.ui.View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="🗳️ לחצו כאן והגישו הצעה חדשה לעיר", style=discord.ButtonStyle.primary, custom_id="btn_s_v8_auto")
    async def open_s(self, interaction: discord.Interaction, button: discord.ui.Button):
        m_role = interaction.guild.get_role(VERIFY_ROLE_ID)
        if m_role not in interaction.user.roles and not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message("❌ עליך לעבור אימות לפני שתוכל להגיש הצעה!", ephemeral=True)
        await interaction.response.send_modal(CreateSuggestionModal())
# --- מערכת לוגי רולים חכמה המזהה את יוצר הפעולה מה-Audit Logs ---
@bot.event
async def on_member_update(before, after):
    if before.guild.id != GUILD_ID: return
    guild = after.guild
    
    # מקרה 1: הוספת רול למשתמש
    if len(before.roles) < len(after.roles):
        new_role = next(role for role in after.roles if role not in before.roles)
        enforcer = "Unknown (API)"
        await asyncio.sleep(1) # המתנה קלה לסנכרון ה-Audit Logs בדיסקורד
        try:
            async for entry in guild.audit_logs(action=discord.AuditLogAction.member_role_update, limit=3):
                if entry.target.id == after.id:
                    enforcer = entry.user.mention
                    break
        except: pass
        await dispatch_log(LOG_ROLE_ADD, "Role Added", f"למשתמש {after.mention} הוענק רול חדש במערכת.\n\n👑 **היוצר / האחראי:** {enforcer}", 0x2ecc71, {"שם הרול": new_role.name, "מזהה רול": str(new_role.id)})
    
    # מקרה 2: הורדת רול ממשתמש
    elif len(before.roles) > len(after.roles):
        removed_role = next(role for role in before.roles if role not in after.roles)
        enforcer = "Unknown (API)"
        await asyncio.sleep(1)
        try:
            async for entry in guild.audit_logs(action=discord.AuditLogAction.member_role_update, limit=3):
                if entry.target.id == after.id:
                    enforcer = entry.user.mention
                    break
        except: pass
        await dispatch_log(LOG_ROLE_REMOVE, "Role Removed", f"למשתמש {after.mention} הוסר או נמחק רול מהחשבון.\n\n👑 **האחראי להסרה:** {enforcer}", 0xe74c3c, {"שם הרול": removed_role.name, "מזהה רול": str(removed_role.id)})

# פונקציית העל - מנקה הודעות ישנות ומקימה את כל הפנלים אוטומטית בכל התנעה מחדש!
async def run_automatic_setup():
    await bot.wait_until_ready()
    print("[AUTOMATION] Starting deep purge and fresh visual deployment...")
    
    # 1. פריסת פנל אימות
    v_ch = bot.get_channel(VERIFY_PANEL_CH)
    if v_ch:
        try: await v_ch.purge(limit=15)
        except: pass
        embed = discord.Embed(title="🔐 מערכת אימות | CHICAGO CITY", description="לחץ על כפתור האימות מטה לקבלת גישה מלאה לכל ערוצי השרת.", color=0x2ecc71)
        embed.set_image(url=BANNER_URL)
        await v_ch.send(embed=embed, view=VerifyView())
    
    # 2. פריסת פנל טיקטים לערוץ הנכון ומחיקת הבלאגן בחדר הווארנים!
    t_ch = bot.get_channel(TICKET_PANEL_CH)
    if t_ch:
        try: await t_ch.purge(limit=15)
        except: pass
        embed = discord.Embed(title="🎫 מרכז תמיכה ופניות | CHICAGO CITY", description="צריך עזרה או ערוץ פנייה פרטי? בחר את הקטגוריה המתאימה בתפריט הבחירה מטה.", color=0x3498db)
        embed.set_image(url=BANNER_URL)
        await t_ch.send(embed=embed, view=TicketOpenView())
        
    # ניקוי סופי של חדר פיד הווארנים מהטיקטים הישנים שנזרקו לשם בטעות
    w_feed_ch = bot.get_channel(WARN_FEED_CH)
    if w_feed_ch:
        try: await w_feed_ch.purge(limit=15)
        except: pass

    # 3. פריסת פנל הגרלות
    g_ch = bot.get_channel(GIVEAWAY_PANEL_CH)
    if g_ch:
        try: await g_ch.purge(limit=15)
        except: pass
        embed = discord.Embed(title="🎁 מרכז ניהול הגרלות השחקנים של הצוות", description="לחצו למטה לפתיחת טופס ההגרלה המהיר!", color=0x2ecc71)
        embed.set_image(url=BANNER_URL)
        await g_ch.send(embed=embed, view=GiveawayPanelView())
        
    # 4. פריסת פנל אזהרות
    w_ch = bot.get_channel(WARN_PANEL_CH)
    if w_ch:
        try: await w_ch.purge(limit=15)
        except: pass
        embed = discord.Embed(title="⚠️ פנל פיקוח ומשמעת הצוות", description="מרכז שליטה חסוי לרישום משמעת בצוות
