import os
import asyncio
import discord
from flask import Flask
from threading import Thread
from discord.ext import tasks, commands

# ========================================================
# 1. שרת FLASK מובנה עבור RENDER
# ========================================================
app = Flask('')

@app.route('/')
def home():
    return "Chicago City Ultimate Core VIP v12 Online"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run_flask)
    t.daemon = True
    t.start()

# ========================================================
# 2. קונפיגורציה קשיחה ומבודדת – קישורי תמונות יציבים לתמיד
# ========================================================
SERVER_NAME = "Chicago City Roleplay"
GUILD_ID = 1483039214793789483

# קישור ישיר, נקי וקבוע של הלוגו שלכם שלא ייחסם לעולמים על ידי דיסקורד!
LOGO_URL = "https://imgur.com"
BANNER_URL = "https://imgur.com"

STATUS_CHANNEL_ID = 1506965475270332476       # סרבר סטטוס
WELCOME_CHANNEL_ID = 1483039215032041530      # ברוכים הבאים
INVITE_TRACKER_CH = 1506417177719210194       # מעקב הזמנות

GIVEAWAY_FEED_CH = 1483039216366780532
WARN_FEED_CH = 1483039219336347810
SUGGEST_FEED_CH = 1483039217482334253

# רשת ערוצי הלוגים הכללית
LOG_TICKET = 1483039219654852612
LOG_SECURITY = 1483039220284002367
LOG_ROLE_ADD = 1507881637705420961
LOG_ROLE_REMOVE = 1507881755753971872
LOG_MEMBER_ADD = 1483039219923554475

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
intents.invites = True   

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
    w_channel = bot.get_channel(WELCOME_CHANNEL_ID)
    if w_channel:
        w_embed = discord.Embed(title="📥 WELCOME TO CHICAGO CITY!", description=f"שלום רב {member.mention},\nברוך הבא לשרת הרשמי של Chicago City Roleplay!", color=0x2ec76f)
        w_embed.set_thumbnail(url=member.display_avatar.url)
        w_embed.set_image(url=BANNER_URL)
        try: await w_channel.send(embed=w_embed)
        except: pass

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
            inviter_text = invite.inviter.mention; uses_count = invite.uses; break

    embed = discord.Embed(title="📥 הצטרפות חדשה - מעקב הזמנות", description=f"המשתמש {member.mention} נכנס לשרת הרשת.\n\n👑 **הוזמן על ידי:** {inviter_text}\n📊 **מספר שימושים:** `{uses_count}`")
    embed.add_field(name="🆔 מספר מזהה (ID)", value=f"`{member.id}`", inline=False)
    embed.set_image(url=BANNER_URL)
    try: await track_channel.send(embed=embed)
    except: pass

class VerifyView(discord.ui.View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="🔑 אימות חשבון / VERIFY", style=discord.ButtonStyle.green, custom_id="verify_btn_diamond_final_v12")
    async def verify_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        role = interaction.guild.get_role(VERIFY_ROLE_ID)
        if not role: return await interaction.response.send_message("❌ רול אימות חסר.", ephemeral=True)
        if role in interaction.user.roles: return await interaction.response.send_message("ℹ️ אתה כבר מאומת.", ephemeral=True)
        await interaction.user.add_roles(role)
        await interaction.response.send_message("✅ אושרת בהצלחה!", ephemeral=True)

class RenameTicketModal(discord.ui.Modal, title="📝 שינוי שם הערוץ"):
    new_name = discord.ui.TextInput(label="שם ערוץ חדש", placeholder="support-fixed", required=True)
    async def on_submit(self, interaction: discord.Interaction):
        clean = self.new_name.value.lower().replace(" ", "-")
        await interaction.channel.edit(name=clean)
        await interaction.response.send_message(f"✅ שם הערוץ שונה ל: {clean}")

class AddMemberModal(discord.ui.Modal, title="👤 הוספת חבר לטיקט"):
    member_input = discord.ui.TextInput(label="תייג את המשתמש או הזן מזהה ID", placeholder="@Aharon", required=True)
    async def on_submit(self, interaction: discord.Interaction):
        guild = interaction.guild
        raw_input = self.member_input.value.strip()
        clean_id = raw_input.replace("<@", "").replace(">", "").replace("!", "")
        try: member = guild.get_member(int(clean_id)) or await guild.fetch_member(int(clean_id))
        except: member = discord.utils.get(guild.members, name=raw_input)
        if member:
            await interaction.channel.set_permissions(member, read_messages=True, send_messages=True, attach_files=True)
            await interaction.response.send_message(f"✅ המשתמש {member.mention} התווסף לטיקט בהצלחה!")
        else: await interaction.response.send_message("❌ המערכת לא זיהתה את המשתמש.", ephemeral=True)

class TicketControlView(discord.ui.View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="🔒 Close", style=discord.ButtonStyle.danger, custom_id="btn_close_final_v12")
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        staff = interaction.guild.get_role(STAFF_ROLE_ID)
        if staff not in interaction.user.roles and not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message("❌ חסום לצוות!", ephemeral=True)
        await interaction.response.send_message("🛑 הערוץ ייסגר בעוד 5 שניות...")
        await asyncio.sleep(5); await interaction.channel.delete()

    @discord.ui.button(label="🙋‍♂️ Claim", style=discord.ButtonStyle.success, custom_id="btn_claim_final_v12")
    async def claim_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        staff = interaction.guild.get_role(STAFF_ROLE_ID)
        if staff not in interaction.user.roles and not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message("❌ חסום לצוות!", ephemeral=True)
        button.disabled, button.label, button.style = True, f"בטיפול: {interaction.user.name}", discord.ButtonStyle.secondary
        await interaction.response.edit_message(view=self)
        await interaction.channel.send(embed=discord.Embed(description=f"💼 הפנייה נלקחה לטיפול של {interaction.user.mention}", color=discord.Color.green()))

    @discord.ui.button(label="✏️ שינוי שם", style=discord.ButtonStyle.primary, custom_id="btn_rn_final_v12")
    async def rename_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        staff = interaction.guild.get_role(STAFF_ROLE_ID)
        if staff not in interaction.user.roles and not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message("❌ חסום לצוות!", ephemeral=True)
        await interaction.response.send_modal(RenameTicketModal())
