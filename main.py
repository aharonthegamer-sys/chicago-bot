import os
import asyncio
from flask import Flask
from threading import Thread
import discord
from discord.ext import tasks, commands

# ========================================================
# 1. שרת FLASK עבור RENDER
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

# הגדרות ערוצים מדויקות לפי הקישורים שסיפקת
STATUS_CHANNEL_ID = 1506965475270332476       # חדר סרבר סטטוס המעוצב
DISCORD_LOG_CHANNEL_ID = 1506965475270332476  # חדר לוגים כללי של המערכת

GIVEAWAY_PANEL_CH = 1507022943413342328       # איפה שנמצא פנל ניהול ההגרלות
GIVEAWAY_FEED_CH = 1483039216366780532        # לאיפה שההגרלה נשלחת לשחקנים

WARN_PANEL_CH = 1507023136095207515           # איפה שנמצא פנל הפיקוח והווארנים
WARN_FEED_CH = 1483039219336347810            # לאיפה שהאזהרה נשלחת לתיעוד צוות

SUGGEST_PANEL_CH = 1507020507776811068        # איפה שנמצא פנל תיבת הרעיונות
SUGGEST_FEED_CH = 1483039217482334253         # לאיפה שההצעה נשלחת להצבעת הקהילה

# הגדרות רולים מדויקות
VERIFY_ROLE_ID = 1483039214793789489          # רול ממבר / אימות
STAFF_ROLE_ID = 1483039215364345930           # רול צוות כללי לטיקטים
GIVEAWAY_ROLE_ID = 1506419159414603868        # רול מנהלי הגרלות המורשים ללחוץ
WARN_STAFF_ROLE_ID = 1483039215393702012      # רול מנהלי אזהרות המורשים ללחוץ

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True 
intents.guilds = True         
intents.members = True        
intents.presences = True      

bot = commands.Bot(command_prefix="!", intents=intents, chunk_guilds_at_startup=True)
status_message = None
warnings_db = {}

async def send_discord_log(title, description, color=0x5865F2, fields=None):
    channel = bot.get_channel(DISCORD_LOG_CHANNEL_ID)
    if not channel:
        return
    embed = discord.Embed(title=title, description=description, color=color)
    if fields:
        for name, value in fields.items():
            embed.add_field(name=name, value=value, inline=True)
    embed.set_footer(text="Chicago City System Logs")
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
# ========================================================
# 3. פנל סטטיסטיקות – ADVANCED DISCORD RADAR
# ========================================================
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
    
    embed.add_field(
        name="👥 חברי הקהילה",
        value=f"```md\n# Total Members : {total_members}\n* Real Humans   : {real_humans}\n* Online Users  : {online_members}\n```",
        inline=True
    )
    
    embed.add_field(
        name="🛡️ צוות ניהול",
        value=f"```md\n# Total Staff   : {total_staff}\n* Staff Online  : {online_staff}\n* Status        : Secured\n```",
        inline=True
    )

    embed.add_field(
        name="💎 שיפורי שרת (Boosts)",
        value=f"```⚙️ סך הכל בוסטים: {boost_count} Boosts\n⭐ רמת בוסט שרת: Level {boost_level}\n🔒 הגנת אנטי-רייד: Active```",
        inline=False
    )

    view = discord.ui.View()
    view.add_item(discord.ui.Button(label="🔗 Web Store", url="https://discord.com", style=discord.ButtonStyle.link))
    view.add_item(discord.ui.Button(label="📜 Server Rules", url="https://discord.com", style=discord.ButtonStyle.link))
    
    if guild.icon: 
        embed.set_thumbnail(url=guild.icon.url)
        
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

# ========================================================
# 4. מערכת אימות חשבון (VERIFY PANEL)
# ========================================================
class VerifyView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🔑 אימות חשבון / VERIFY", style=discord.ButtonStyle.green, custom_id="verify_btn_expert")
    async def verify_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        role = interaction.guild.get_role(VERIFY_ROLE_ID)
        if not role: 
            return await interaction.response.send_message("Verify role missing.", ephemeral=True)
        
        if role in interaction.user.roles: 
            return await interaction.response.send_message("Already verified.", ephemeral=True)
        
        await interaction.user.add_roles(role)
        await interaction.response.send_message("Successfully verified! Welcome to Chicago City.", ephemeral=True)
        
        await send_discord_log(
            title="🔐 New User Verified",
            description=f"The user {interaction.user.mention} completed verification successfully.",
            color=0x2ecc71,
            fields={"User Name": interaction.user.name, "User ID": str(interaction.user.id)}
        )
# ========================================================
# 5. מערכת פנל הגרלות רשמי (GIVEAWAY CORE SYSTEM)
# ========================================================
class CreateGiveawayModal(discord.ui.Modal, title="🎁 יצירת הגרלה חדשה לשרת"):
    g_title = discord.ui.TextInput(label="מה הפרס של ההגרלה?", placeholder="e.g., 500K Cash / Premium Car", required=True)
    g_time = discord.ui.TextInput(label="זמן ההגרלה (בדקות בלבד)", placeholder="e.g., 60", required=True)

    async def on_submit(self, interaction: discord.Interaction):
        feed_channel = bot.get_channel(GIVEAWAY_FEED_CH)
        if not feed_channel:
            return await interaction.response.send_message("❌ ערוץ פיד ההגרלות לא נמצא במערכת.", ephemeral=True)

        embed = discord.Embed(
            title=f"🎉 הגרלה חדשה יצאה לדרך! | GIVEAWAY",
            description=f"**🎁 הפרס המוגרל:**\n```{self.g_title.value}```\n"
                        f"⏰ **זמן לסיום:** {self.g_time.value} דקות\n"
                        f"👑 **יוצר ההגרלה:** {interaction.user.mention}\n\n"
                        f"לחצו על האימוג'י 🎉 למטה כדי להיכנס להגרלה ולהשתתף!",
            color=0x2ecc71
        )
        embed.set_footer(text="Chicago City Staff Automation Core")
        embed.timestamp = discord.utils.utcnow()
        
        msg = await feed_channel.send(embed=embed)
        await msg.add_reaction("🎉")
        
        await interaction.response.send_message(f"✅ ההגרלה נוצרה בהצלחה ונשלחה לערוץ: {feed_channel.mention}", ephemeral=True)
        
        await send_discord_log(
            title="🎁 Giveaway Created",
            description=f"Staff member {interaction.user.mention} initialized a server giveaway.",
            color=0x2ecc71,
            fields={"Prize": self.g_title.value, "Duration": f"{self.g_time.value} Min", "Channel": feed_channel.name}
        )

class GiveawayPanelView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🎁 פתח הגרלה חדשה לשחקנים", style=discord.ButtonStyle.green, custom_id="btn_create_giveaway_cc")
    async def open_giveaway_modal(self, interaction: discord.Interaction, button: discord.ui.Button):
        g_role = interaction.guild.get_role(GIVEAWAY_ROLE_ID)
        if g_role not in interaction.user.roles and not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message("❌ הרשאה זו חסומה עבורך! רק מנהלי הגרלות מורשים ללחוץ.", ephemeral=True)
        await interaction.response.send_modal(CreateGiveawayModal())

# ========================================================
# 6. מערכת פנל פיקוח ואזהרות (WARN PANEL SYSTEM)
# ========================================================
class IssueWarnModal(discord.ui.Modal, title="🛡️ רישום אזהרה למשתמש"):
    u_id = discord.ui.TextInput(label="הזן מספר ID של השחקן", placeholder="e.g., 1483039214793789483", required=True)
    u_reason = discord.ui.TextInput(label="סיבת האזהרה", placeholder="e.g., Toxic Behavior / Staff Disrespect", required=True)

    async def on_submit(self, interaction: discord.Interaction):
        feed_channel = bot.get_channel(WARN_FEED_CH)
        if not feed_channel:
            return await interaction.response.send_message("❌ ערוץ פיד האזהרות לא נמצא במערכת.", ephemeral=True)

        try:
            member = interaction.guild.get_member(int(self.u_id.value))
            if not member:
                member = await interaction.guild.fetch_member(int(self.u_id.value))
        except:
            return await interaction.response.send_message("❌ מספר ה-ID שהזנת אינו תקין או שהמשתמש לא נמצא בשרת.", ephemeral=True)

        if member.id not in warnings_db:
            warnings_db[member.id] = []
        warnings_db[member.id].append(self.u_reason.value)
        total_warns = len(warnings_db[member.id])

        embed = discord.Embed(
            title="🚨 רישום עונש | אזהרה רשמית לצוות",
            color=0xe67e22
        )
        embed.add_field(name="👤 משתמש שנאשם", value=member.mention, inline=True)
        embed.add_field(name="👮 האוכף", value=interaction.user.mention, inline=True)
        embed.add_field(name="📝 סיבת האזהרה", value=f"```{self.u_reason.value}```", inline=False)
        embed.add_field(name="📊 סך הכל אזהרות", value=f"`{total_warns}`", inline=False)
        embed.set_footer(text="Chicago City Moderation Core")
        embed.timestamp = discord.utils.utcnow()
        
        await feed_channel.send(embed=embed)
        await interaction.response.send_message(f"✅ האזהרה נרשמה בהצלחה ותועדה בערוץ: {feed_channel.mention}", ephemeral=True)

        await send_discord_log(
            title="🛡️ Security Infraction Processed",
            description=f"Moderator logged a formal disciplinary warning.",
            color=0xe67e22,
            fields={"Target": member.name, "Enforcer": interaction.user.name, "Reason": self.u_reason.value}
        )

class CheckWarnModal(discord.ui.Modal, title="📋 בדיקת תיק אזהרות"):
    u_id = discord.ui.TextInput(label="הזן מספר ID של השחקן", placeholder="e.g., 1483039214793789483", required=True)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            member = interaction.guild.get_member(int(self.u_id.value))
            if not member:
                member = await interaction.guild.fetch_member(int(self.u_id.value))
        except:
            return await interaction.response.send_message("❌ משתמש לא נמצא.", ephemeral=True)

        warns = warnings_db.get(member.id, [])
        if not warns:
            return await interaction.response.send_message(f"🟢 המשתמש **{member.name}** נקי לחלוטין מחטאים ואין לו אזהרות.", ephemeral=True)

        embed = discord.Embed(title=f"📋 תיק אזהרות פתוח עבור {member.name.upper()}", color=0xe74c3c)
        for i, reason in enumerate(warns, 1):
            embed.add_field(name=f"📌 אזהרה מספר #{i}", value=f"סיבה: `{reason}`", inline=False)
        embed.set_footer(text=f"Total active penalties: {len(warns)}")
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

class RemoveWarnModal(discord.ui.Modal, title="🗑️ מחיקת אזהרה מתיק"):
    u_id = discord.ui.TextInput(label="הזן מספר ID של השחקן", placeholder="1483039214793789483", required=True)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            user_id = int(self.u_id.value)
        except:
            return await interaction.response.send_message("❌ ID לא תקין.", ephemeral=True)

        if user_id in warnings_db and warnings_db[user_id]:
            removed_reason = warnings_db[user_id].pop()
            await interaction.response.send_message(f"✅ האזהרה האחרונה נמחקה מתיק המשתמש בהצלחה. (סיבה שנמחקה: `{removed_reason}`)", ephemeral=True)
            
            await send_discord_log(
                title="🗑️ Warning Cleared",
                description=f"Staff member wiped the last active warning entry from database profile.",
                color=0x3498db,
                fields={"Cleared ID": str(user_id), "Staff": interaction.user.name}
            )
        else:
            await interaction.response.send_message("❌ למשתמש זה אין שום אזהרות רשומות במאגר הנתונים.", ephemeral=True)

class WarnPanelView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="⚠️ רשום אזהרה למנהל", style=discord.ButtonStyle.danger, custom_id="btn_issue_warn_cc")
    async def issue_warn_click(self, interaction: discord.Interaction, button: discord.ui.Button):
        w_role = interaction.guild.get_role(WARN_STAFF_ROLE_ID)
        if w_role not in interaction.user.roles and not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message("❌ פעולה חסומה! רק מנהלי אזהרות רשאים לגשת.", ephemeral=True)
        await interaction.response.send_modal(IssueWarnModal())

    @discord.ui.button(label="📋 כמות ואזהרים בתיק", style=discord.ButtonStyle.secondary, custom_id="btn_check_warn_cc")
    async def check_warn_click(self, interaction: discord.Interaction, button: discord.ui.Button):
        w_role = interaction.guild.get_role(WARN_STAFF_ROLE_ID)
        if w_role not in interaction.user.roles and not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message("❌ פעולה חסומה!", ephemeral=True)
        await interaction.response.send_modal(CheckWarnModal())

    @discord.ui.button(label="🟢 מחק אזהרה (Unwarn)", style=discord.ButtonStyle.success, custom_id="btn_remove_warn_cc")
    async def remove_warn_click(self, interaction: discord.Interaction, button: discord.ui.Button):
        w_role = interaction.guild.get_role(WARN_STAFF_ROLE_ID)
        if w_role not in interaction.user.roles and not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message("❌ פעולה חסומה!", ephemeral=True)
        await interaction.response.send_modal(RemoveWarnModal())
# ========================================================
# 7. מערכת פנל הצעות (SUGGESTIONS SYSTEM)
# ========================================================
class CreateSuggestionModal(discord.ui.Modal, title="💡 הגשת הצעה חדשה לעיר"):
    s_text = discord.ui.TextInput(label="פרט את ההצעה שלך בשלמותה", placeholder="e.g., Add new mapping for mechanics...", style=discord.TextStyle.paragraph, required=True, min_length=10)

    async def on_submit(self, interaction: discord.Interaction):
        feed_channel = bot.get_channel(SUGGEST_FEED_CH)
        if not feed_channel:
            return await interaction.response.send_message("❌ ערוץ פיד ההצעות לא נמצא במערכת.", ephemeral=True)

        embed = discord.Embed(
            title="💡 הצעה חדשה מהקהילה",
            description=f"```{self.s_text.value}```",
            color=0xf1c40f
        )
        embed.set_author(name=interaction.user.name, icon_url=interaction.user.display_avatar.url)
        embed.add_field(name="📊 מדד הצבעות", value="הצביעו באמצעות האימוג'ים המופיעים מטה:", inline=False)
        embed.set_footer(text="Chicago City Suggestion Core")
        embed.timestamp = discord.utils.utcnow()
        
        msg = await feed_channel.send(embed=embed)
        await msg.add_reaction("✅")
        await msg.add_reaction("❌")
        
        await interaction.response.send_message(f"✅ ההצעה שלך הוגשה בהצלחה ונשלחה לערוץ: {feed_channel.mention}", ephemeral=True)
        
        await send_discord_log(
            title="💡 New User Suggestion Created",
            description=f"A new idea was logged by {interaction.user.mention}.",
            color=0xf1c40f,
            fields={"Author": interaction.user.name, "Channel": feed_channel.name}
        )

class SuggestionsPanelView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🗳️ לחצו כאן והגישו הצעה חדשה לעיר", style=discord.ButtonStyle.primary, custom_id="btn_create_suggest_cc")
    async def open_suggest_modal(self, interaction: discord.Interaction, button: discord.ui.Button):
        m_role = interaction.guild.get_role(VERIFY_ROLE_ID)
        if m_role not in interaction.user.roles and not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message("❌ עליך לעבור אימות (Verify) לפני שתוכל להגיש הצעה!", ephemeral=True)
        await interaction.response.send_modal(CreateSuggestionModal())

# ========================================================
# 8. פקודות הקמה והפעלה רשמיות (ADMIN SETUP COMMANDS)
# ========================================================
@bot.command()
@commands.has_permissions(administrator=True)
async def setup_all_panels(ctx):
    await ctx.message.delete()
    
    # 1. הקמת פנל הגרלות
    g_channel = bot.get_channel(GIVEAWAY_PANEL_CH)
    if g_channel:
        g_embed = discord.Embed(
            title="🎁 מרכז ניהול הגרלות השחקנים של הצוות",
            description="שלום חברי צוות יקרים!\nמערכת זו מיועדת ליצירת הגרלות מעוצבות בשניות בצורה קלה.\n\n"
                        "לחצו על הכפתור הירוק למטה כדי לפתוח את טופס יצירת ההגרלה המהיר!",
            color=0x2ecc71
        )
        if ctx.guild.icon: g_embed.set_thumbnail(url=ctx.guild.icon.url)
        g_embed.set_footer(text="Chicago City Staff Console • Color Edition")
        await g_channel.send(embed=g_embed, view=GiveawayPanelView())

    # 2. הקמת פנל אזהרות
    w_channel = bot.get_channel(WARN_PANEL_CH)
    if w_channel:
        w_embed = discord.Embed(
            title="⚠️ פנל פיקוח ומשמעת הצוות",
            description="מרכז שליטה ואבטחה חסוי לניהול, בדיקה ורישום משמעת בצוות השרת.\n\n"
                        "**🚨 רק דרג ניהול עליון מורשה ללחוץ על הכפתורים ולבצע שינויים או מחיקות!**",
            color=0xe67e22
        )
        if ctx.guild.icon: w_embed.set_thumbnail(url=ctx.guild.icon.url)
        w_embed.set_footer(text="Chicago City Management Dashboard Only")
        await w_channel.send(embed=w_embed, view=WarnPanelView())

    # 3. הקמת פנל הצעות
    s_channel = bot.get_channel(SUGGEST_PANEL_CH)
    if s_channel:
        s_embed = discord.Embed(
            title="💎 תיבת הרעיונות וההצעות של CHICAGO CITY",
            description="יש לכם רעיון משוגע ומטורף לשדרוג חווית המשחק בעיר?\n\n"
                        "לחצו על הכפתור הכחול למטה, מלאו את הטופס שייפתח ויאללה - ההצעה שלכם עולה ישירות לקהילה!",
            color=0xf1c40f
        )
        if ctx.guild.icon: s_embed.set_thumbnail(url=ctx.guild.icon.url)
        s_embed.set_footer(text="Chicago City • Power of Community")
        await s_channel.send(embed=s_embed, view=SuggestionsPanelView())

    await ctx.send("✅ כל הפנלים הוקמו בהצלחה בערוצים המתאימים בעיצוב פרימיום!", delete_after=5)

# ========================================================
# 9. סנכרון כפתורים קבועים והפעלה רשמית
# ========================================================
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
    print("==================================================")
    print(f"PREMIUM EXPERT CORE OPERATIONAL: {bot.user.name.upper()}")
    print("==================================================")
    await bot.change_presence(activity=None)
    if not update_discord_radar.is_running():
        update_discord_radar.start()

if __name__ == "__main__":
    keep_alive()
    token = os.getenv("DISCORD_TOKEN")
    if token:
        bot.run(token)
