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
    return "Chicago City Diamond Core V2 is Online!"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run_flask)
    t.daemon = True
    t.start()

# ========================================================
# 2. קונפיגורציה קשיחה – הפרדה מוחלטת בין פנלים ללוגים
# ========================================================
SERVER_NAME = "Chicago City Roleplay"
GUILD_ID = 1483039214793789483

# קישורי תמונות הפרימיום הרשמיות של שיקגו סיטי
LOGO_URL = "https://discordapp.com"
BANNER_URL = "https://cdn.discordapp.com/attachments/1493198490237538407/1507887633076977754/ea602ee7ebc1a23f.png"

# ערוצי פנלים לקהילה (פרונט) - מתוקן ומבודד מחדרי הלוגים!
STATUS_CHANNEL_ID = 1506965475270332476       # חדר סרבר סטטוס
WELCOME_CHANNEL_ID = 1483039215032041530      # חדר ברוכים הבאים
VERIFY_PANEL_CH = 1483039214793789489         # חדר אימות (✔️-verfiy)
TICKET_PANEL_CH = 1483039219336347810         # חדר פתיחת טיקטים (ערוץ ייעודי לפתיחה)

GIVEAWAY_PANEL_CH = 1507022943413342328       # פנל ניהול הגרלות לצוות
GIVEAWAY_FEED_CH = 1483039216366780532        # פיד הגרלות לשחקנים

WARN_PANEL_CH = 1507023136095207515           # פנל ניהול אזהרות לצוות
WARN_FEED_CH = 1483039219336347810            # פיד אזהרות רשמי

SUGGEST_PANEL_CH = 1507020507776811068        # פנל ניהול הצעות
SUGGEST_FEED_CH = 1483039217482334253         # פיד הצעות להצבעה

# רשת ערוצי הלוגים הרשמית (תיעוד פנימי בלבד)
LOG_TICKET = 1483039219654852612              # לוג טיקטים (🎫-Ticket-logs)
LOG_CHANNEL_DELETE = 1483039219654852616       # לוג מחיקת חדרים
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

# פונקציית לוגים חכמה לניתוב אוטומטי של הודעות Embed לערוצי היעד עם הבאנר המטורף
async def dispatch_log(target_channel_id, title, description, color=0x010101, fields=None):
    channel = bot.get_channel(target_channel_id)
    if not channel:
        return
    embed = discord.Embed(title=f"🛡️ AUDIT CORE | {title.upper()}", description=description, color=color)
    if fields:
        for name, value in fields.items():
            embed.add_field(name=f"🔹 {name}", value=f"```yaml\n{value}\n```", inline=True)
    embed.set_thumbnail(url=LOGO_URL)
    embed.set_image(url=BANNER_URL)
    embed.set_footer(text="Chicago City System Log Protection Active")
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
        title=f"⚫ {SERVER_NAME.upper()} | LIVE RADAR STATUS",
        description="ברוכים הבאים ללוח המידע המרכזי של הרשת.\nהנתונים מסונכרנים ישירות מול שרתי המערכת הרשמיים.\n\n**─── SERVER INFRASTRUCTURE ───**",
        color=0x010101 
    )
    embed.add_field(name="👥 חברי הקהילה", value=f"```md\n# Total Members : {total_members}\n* Real Humans   : {real_humans}\n* Online Users  : {online_members}\n```", inline=True)
    embed.add_field(name="🛡️ צוות ניהול", value=f"```md\n# Total Staff   : {total_staff}\n* Staff Online  : {online_staff}\n* Status        : Secured\n```", inline=True)
    embed.add_field(name="💎 שיפורי שרת ובוסטים", value=f"```⚙️ Server Boosts  : {boost_count} Boosts\n⭐ Premium Tier  : Level {boost_level}\n🔒 Firewall Core : Active```", inline=False)
    
    view = discord.ui.View()
    view.add_item(discord.ui.Button(label="🔗 Web Store", url="https://discord.com", style=discord.ButtonStyle.link))
    embed.set_thumbnail(url=LOGO_URL)
    embed.set_image(url=BANNER_URL)
    embed.set_footer(text="⚡ Chicago City Realtime Tracking Engine")
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
        title="📥 WELCOME TO CHICAGO CITY ROLEPLAY",
        description=f"שלום רב {member.mention},\nברוך הבא לשרת הרשמי של Chicago City Roleplay!\n\n"
                    f"**📌 שלבי התחלה ראשוניים:**\n"
                    f"1️⃣ כנס לערוץ האימות המרכזי ובצע אימות חשבון בלחיצה אחת.\n"
                    f"2️⃣ קרא את חוקי הקהילה על מנת למנוע אי נעימויות מול צוות הפיקוח.\n\n"
                    f"**─── USER DATABASE IDENTITY ───**",
        color=0x010101
    )
    embed.add_field(name="👤 שם המשתמש", value=f"```yaml\n{member.name}\n```", inline=True)
    embed.add_field(name="🆔 מספר חשבון", value=f"```yaml\n{member.id}\n```", inline=True)
    
    embed.set_thumbnail(url=member.display_avatar.url)
    embed.set_image(url=BANNER_URL)
    embed.set_footer(text=f"Chicago City Member Database • #{member.guild.member_count}")
    embed.timestamp = discord.utils.utcnow()
    
    try: await channel.send(embed=embed)
    except: pass
        
    await dispatch_log(LOG_MEMBER_ADD, "Member Joined", f"{member.mention} has joined the discord layout.", 0x2ecc71, {"Account Name": member.name, "ID": str(member.id)})

class VerifyView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🔑 אימות חשבון / VERIFY", style=discord.ButtonStyle.green, custom_id="verify_btn_diamond_final_v2")
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
            title="Gate Authentication Success",
            description=f"The user {interaction.user.mention} unlocked the verified wall database.",
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
        await dispatch_log(LOG_TICKET, "Ticket Renamed", f"Staff {interaction.user.mention} altered layout.", 0x3498db, {"Old": old_name, "New": clean_name})

class AddMemberModal(discord.ui.Modal, title="👤 הוספת חבר לטיקט (تيوג / שם / ID)"):
    member_input = discord.ui.TextInput(label="הזן תיוג משתמש, שם או מספר ID", placeholder="e.g., @Aharon / 1483039214793789483", required=True)

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
            await dispatch_log(LOG_TICKET, "Member Integrated", f"{interaction.user.name} added {member.name}", 0x9b59b6, {"Channel": interaction.channel.name})
        else:
            await interaction.response.send_message("❌ שחקן לא נמצא.", ephemeral=True)

class TicketControlView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🔒 סגור טיקט / Close", style=discord.ButtonStyle.danger, custom_id="btn_close_t_v8")
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("🛑 הערוץ יימחק לחלוטין בעוד 5 שניות...")
        await dispatch_log(LOG_TICKET, "Ticket Destruction Logs", f"**{interaction.channel.name}** was completely wiped.", 0xe74c3c, {"Closed By": interaction.user.name})
        await asyncio.sleep(5)
        await interaction.channel.delete()

    @discord.ui.button(label="🙋‍♂️ קח טיפול / Claim", style=discord.ButtonStyle.success, custom_id="btn_claim_t_v8")
    async def claim_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        staff_role = interaction.guild.get_role(STAFF_ROLE_ID)
        if staff_role not in interaction.user.roles and not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message("❌ דרג צוות מורשה בלבד!", ephemeral=True)
        button.disabled, button.label, button.style = True, f"Claimed by: {interaction.user.name}", discord.ButtonStyle.secondary
        await interaction.response.edit_message(view=self)
        await interaction.channel.send(embed=discord.Embed(description=f"💼 פנייה זו נלקחה תחת טיפולו האישי של {interaction.user.mention}", color=0x010101).set_image(url=BANNER_URL))
        await dispatch_log(LOG_TICKET, "Ticket Interception", f"Claimed by {interaction.user.name}", 0x2ecc71, {"Ticket Channel": interaction.channel.name})

    @discord.ui.button(label="✏️ שינוי שם", style=discord.ButtonStyle.primary, custom_id="btn_rename_t_v8")
    async def rename_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(RenameTicketModal())

    @discord.ui.button(label="➕ הוסף משתמש", style=discord.ButtonStyle.secondary, custom_id="btn_add_m_t_v8")
    async def add_member(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(AddMemberModal())
class TicketDropdown(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="דיווח על שחקן / צוות", description="Report a player or staff", emoji="🚨", value="report"),
            discord.SelectOption(label="דיווח על באג", description="Report a server bug", emoji="🐛", value="bug"),
            discord.SelectOption(label="בחינה לצוות השרת", description="Apply for staff", emoji="📝", value="apply"),
            discord.SelectOption(label="שאלה כללית / עזרה", description="General assistance room", emoji="❓", value="general")
        ]
        super().__init__(placeholder="🔽 בחר את קטגוריית הפנייה שלך...", options=options, custom_id="ticket_dropdown_v8_final")

    async def callback(self, interaction: discord.Interaction):
        category = self.values
        guild = interaction.guild
        category_titles = {"report": "Report Player/Staff", "bug": "Bug Report", "apply": "Staff Application", "general": "General Help"}
        ticket_prefix = {"report": "report", "bug": "bug", "apply": "apply", "general": "help"}
        ticket_name = f"{ticket_prefix[category]}-{interaction.user.name}".lower()
        if discord.utils.get(guild.channels, name=ticket_name):
            return await interaction.response.send_message("❌ כבר יש לך פנייה פתוחה במערכת!", ephemeral=True)
        
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True, attach_files=True),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }
        channel = await guild.create_text_channel(name=ticket_name, overwrites=overwrites)
        
        embed = discord.Embed(
            title=f"🎫 מרכז תמיכה פנימי | קטגוריה: {category_titles[category].upper()}", 
            description=f"שלום רב {interaction.user.mention},\nצוות הניהול קיבל את פנייתך ויתפנה אליך בהקדם.\n\n"
                        f"**📋 הנחיות להתקדמות:**\nאנא פרט את המקרה בצורה מלאה כאן בצ'אט וספק את כל ההוכחות/מידע שברשותך.", 
            color=0x010101
        )
        embed.set_thumbnail(url=LOGO_URL)
        embed.set_image(url=BANNER_URL)
        embed.set_footer(text="Chicago City Customer Support Infrastructure")
        embed.timestamp = discord.utils.utcnow()
        
        await channel.send(embed=embed, view=TicketControlView())
        await interaction.response.send_message(f"✅ פנייה נוצרה בהצלחה: {channel.mention}", ephemeral=True)
        await dispatch_log(LOG_TICKET, "New Ticket Opened", f"Opened by {interaction.user.name}", 0xe67e22, {"Category": category_titles[category], "Channel": channel.name})

class TicketOpenView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(TicketDropdown())
class GiveawayFeedControls(discord.ui.View):
    def __init__(self, msg_id):
        super().__init__(timeout=None)
        self.msg_id = msg_id

    @discord.ui.button(label="🔒 סגור הגרלה / Close", style=discord.ButtonStyle.danger, custom_id="btn_close_giveaway_feed")
    async def close_g_click(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.guild.get_role(GIVEAWAY_ROLE_ID) not in interaction.user.roles and not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message("❌ אין לך גישה למערכת ניהול ההגרלות הזו!", ephemeral=True)
        
        try:
            msg = await interaction.channel.fetch_message(self.msg_id)
            reaction = discord.utils.get(msg.reactions, emoji="🎉")
            users = [user async for user in reaction.users() if not user.bot]
            if not users:
                return await interaction.response.send_message("❌ לא נמצאו משתתפים חוקיים בהגרלה הנוכחית.", ephemeral=True)
            
            winner = random.choice(users)
            embed = msg.embeds[0]
            embed.title = "🎉 ההגרלה הסתיימה רשמית! | FINISHED"
            embed.description = f"{embed.description}\n\n👑 **הזוכה המאושר הוא:** {winner.mention}\n🛑 הסטטוס ננעל ועודכן במאגר."
            embed.color = 0xe74c3c
            
            self.clear_items()
            await msg.edit(embed=embed, view=self)
            await interaction.response.send_message(f"✅ ההגרלה נסגרה בהצלחה! הזוכה שנבחר: {winner.mention}")
        except:
            await interaction.response.send_message("❌ תקלה: ההודעה נמחקה או לא נמצאה.", ephemeral=True)

    @discord.ui.button(label="🔄 רול מחדש / Reroll", style=discord.ButtonStyle.primary, custom_id="btn_reroll_giveaway_feed")
    async def reroll_g_click(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.guild.get_role(GIVEAWAY_ROLE_ID) not in interaction.user.roles and not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message("❌ אין לך גישה!", ephemeral=True)
        
        try:
            msg = await interaction.channel.fetch_message(self.msg_id)
            reaction = discord.utils.get(msg.reactions, emoji="🎉")
            users = [user async for user in reaction.users() if not user.bot]
            if not users:
                return await interaction.response.send_message("❌ אין משתתפים.", ephemeral=True)
            
            winner = random.choice(users)
            await interaction.channel.send(f"🔄 **REROLL!** הזוכה החדש שנבחר מתוך מאגר המשתתפים הוא: {winner.mention} 🎉")
            await interaction.response.send_message(f"✅ בוצע רול מחדש. הזוכה החדש: {winner.mention}", ephemeral=True)
        except:
            await interaction.response.send_message("❌ שגיאה בביצוע הרול מחדש.", ephemeral=True)

class CreateGiveawayModal(discord.ui.Modal, title="🎁 יצירת הגרלה חדשה לשרת"):
    g_title = discord.ui.TextInput(label="מה הפרס של ההגרלה?", placeholder="e.g., VIP Premium Pass", required=True)
    g_time = discord.ui.TextInput(label="זמן ההגרלה (בדקות בלבד)", placeholder="e.g., 60", required=True)

    async def on_submit(self, interaction: discord.Interaction):
        feed_channel = bot.get_channel(GIVEAWAY_FEED_CH)
        if not feed_channel: return await interaction.response.send_message("❌ ערוץ פיד ההגרלות לא נמצא.", ephemeral=True)

        embed = discord.Embed(
            title=f"🎉 הגרלה חדשה יצאה לדרך! | GIVEAWAY", 
            description=f"**🎁 הפרס המוגרל במערכת:**\n```{self.g_title.value}```\n⏰ **זמן לסיום:** {self.g_time.value} דקות\n👑 **יוצר ההגרלה:** {interaction.user.mention}\n\nלחצו על 🎉 למטה להרשמה!", 
            color=0x010101
        )
        embed.set_thumbnail(url=LOGO_URL)
        embed.set_image(url=BANNER_URL)
        
        temp_msg = await feed_channel.send(embed=embed)
        await temp_msg.add_reaction("🎉")
        
        # עדכון ההודעה המקורית עם כפתורי השליטה הייעודיים של הצוות (סגירה וררול)
        await temp_msg.edit(view=GiveawayFeedControls(temp_msg.id))
        await interaction.response.send_message(f"✅ ההגרלה נוצרה בהצלחה ב: {feed_channel.mention}", ephemeral=True)

class GiveawayPanelView(discord.ui.View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="🎁 פתח הגרלה חדשה לשחקנים", style=discord.ButtonStyle.green, custom_id="btn_create_g_diamond_v8")
    async def open_giveaway_modal(self, interaction: discord.Interaction, button: discord.ui.Button):
        g_role = interaction.guild.get_role(GIVEAWAY_ROLE_ID)
        if g_role not in interaction.user.roles and not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message("❌ הרשאה זו חסומה עבורך!", ephemeral=True)
        await interaction.response.send_modal(CreateGiveawayModal())
# ========================================================
# 11. מערכת לוגי רולים חכמה המזהה את האחראי (Audit Log)
# ========================================================
@bot.event
async def on_member_update(before, after):
    if before.guild.id != GUILD_ID: 
        return
    guild = after.guild
    
    # מקרה א': הוספת רול למשתמש
    if len(before.roles) < len(after.roles):
        new_role = next(role for role in after.roles if role not in before.roles)
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
            target_channel_id=LOG_ROLE_ADD,
            title="Role Allocated",
            description=f"למשתמש {after.mention} הוענק רול חדש בשרת.\n\n👑 **האחראי לביצוע:** {enforcer}",
            color=0x2ecc71,
            fields={"שם הרול": new_role.name, "מזהה רול": str(new_role.id), "שם המשתמש": after.name}
        )
    
    # מקרה ב': הורדת רול ממשתמש
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
# 12. פונקציית פריסה אוטומטית מלאה בהתנעה (Auto-Setup)
# ========================================================
async def run_automatic_setup():
    await bot.wait_until_ready()
    print("[AUTOMATION] Starting deep purge and fresh visual deployment...")
    
    # 1. פנל אימות חשבון (Verify Panel)
    v_ch = bot.get_channel(VERIFY_PANEL_CH)
    if v_ch:
        try: await v_ch.purge(limit=15)
        except: pass
        embed = discord.Embed(
            title=f"🔐 מערכת אימות חשבון | {SERVER_NAME.upper()}",
            description="על מנת לקבל גישה מלאה לכל ערוצי השרת ולוודא שאינך בוט, אנא לחץ על כפתור האימות המופיע מטה.\n\n**⚠️ דגש חשוב:**\nבלחיצה על הכפתור אתה מאשר שקראת והסכמת לחוקי הקהילה ותנאי השימוש.",
            color=0x2ecc71
        )
        embed.set_image(url=BANNER_URL)
        await v_ch.send(embed=embed, view=VerifyView())
    
    # 2. פנל פתיחת טיקטים (Ticket Panel)
    t_ch = bot.get_channel(TICKET_PANEL_CH)
    if t_ch:
        try: await t_ch.purge(limit=15)
        except: pass
        embed = discord.Embed(
            title=f"🎫 מרכז תמיכה ופניות | {SERVER_NAME.upper()}",
            description="צריך עזרה? נתקלת בבעיה או שברצונך לפתוח פנייה רשמית לצוות השרת?\nהשתמש בתפריט הבחירה המופיע מטה, בחר את הקטגוריה המתאימה ביותר למקרה שלך, וחדר אישי ייפתח עבורך מול צוות השרת.",
            color=0x3498db
        )
        embed.set_image(url=BANNER_URL)
        await t_ch.send(embed=embed, view=TicketOpenView())
        
    # 3. פנל הגרלות לצוות (Giveaway Management Panel)
    g_ch = bot.get_channel(GIVEAWAY_PANEL_CH)
    if g_ch:
        try: await g_ch.purge(limit=15)
        except: pass
        embed = discord.Embed(
            title="🎁 מרכז ניהול הגרלות השחקנים של הצוות",
            description="שלום חברי צוות יקרים!\nמערכת זו מיועדת ליצירת הגרלות מעוצבות בשניות בצורה קלה.\n\nלחצו על הכפתור הירוק למטה כדי לפתוח את טופס יצירת ההגרלה המהיר!",
            color=0x2ecc71
        )
        embed.set_image(url=BANNER_URL)
        await g_ch.send(embed=embed, view=GiveawayPanelView())
        
    # 4. פנל אזהרות לצוות (Warn Management Panel)
    w_ch = bot.get_channel(WARN_PANEL_CH)
    if w_ch:
        try: await w_ch.purge(limit=15)
        except: pass
        embed = discord.Embed(
            title="⚠️ פנל פיקוח ומשמעת הצוות",
            description="מרכז שליטה ואבטחה חסוי לניהול, בדיקה ורישום משמעת בצוות השרת.\n\n**🚨 רק דרג ניהול עליון מורשה ללחוץ על הכפתורים ולבצע שינויים או מחיקות!**",
            color=0xe67e22
        )
        embed.set_image(url=BANNER_URL)
        await w_ch.send(embed=embed, view=WarnPanelView())
        
    # 5. פנל הצעות לקהילה (Suggestion Panel)
    s_ch = bot.get_channel(SUGGEST_PANEL_CH)
    if s_ch:
        try: await s_ch.purge(limit=15)
        except: pass
        embed = discord.Embed(
            title="💎 תיבת הרעיונות וההצעות של CHICAGO CITY",
            description="יש לכם רעיון משוגע ומטורף לשדרוג חווית המשחק בעיר?\n\nלחצו על הכפתור הכחול למטה, מלאו את הטופס שייפתח ויאללה - ההצעה שלכם עולה ישירות לקהילה!",
            color=0xf1c40f
        )
        embed.set_image(url=BANNER_URL)
        await s_ch.send(embed=embed, view=SuggestionsPanelView())
    print("[AUTOMATION] Visual interfaces deployed successfully.")

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
    print(f"CHICAGO DIAMOND ENGINE RUNNING PERFECTLY")
    print("====================================")
    await bot.change_presence(activity=None)
    
    # הפעלת לולאת הראדאר של הסטטיסטיקות
    if not update_discord_radar.is_running(): 
        update_discord_radar.start()
        
    # הפעלת פריסת הפנלים האוטומטית
    bot.loop.create_task(run_automatic_setup())

if __name__ == "__main__":
    keep_alive()
    token = os.getenv("DISCORD_TOKEN")
    if token: 
        bot.run(token)
