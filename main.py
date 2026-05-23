import os
import asyncio
from flask import Flask
from threading import Thread
import discord
from discord.ext import tasks, commands

# ========================================================
# 1. שרת FLASK הרמטי ל-RENDER (מניעת קריסות פורטים)
# ========================================================
app = Flask('')

@app.route('/')
def home():
    return "Chicago City Discord Panel is Active 24/7!"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run_flask)
    t.daemon = True
    t.start()

# ========================================================
# 2. נתונים קבועים והגדרות אינטנטס מלאות
# ========================================================
SERVER_NAME = "Chicago City Network"
GUILD_ID = 1483039214793789483
STATUS_CHANNEL_ID = 1506965475270332476
VERIFY_ROLE_ID = 1483039214793789489
STAFF_ROLE_ID = 1483039215364345930

# הפעלת הגדרות אבטחה מיוחדות לספירת חברים אונליין
intents = discord.Intents.default()
intents.messages = True
intents.guilds = True         
intents.members = True        # מאפשר לבוט לקרוא את רשימת המשתמשים
intents.presences = True      # מאפשר לבוט לראות מי אונליין/DND/Idle

# יצירת הבוט עם הגדרת זיכרון פנימי קבוע (Chunking) למניעת קפיאה ב-Render
bot = commands.Bot(command_prefix="!", intents=intents, chunk_guilds_at_startup=True)
status_message = None
warnings_db = {}

@bot.event
async def on_message(message):
    if message.author.bot:
        return
    await bot.process_commands(message)

# ========================================================
# 3. מערכת הסטטוס היוקרתית - DISCORD RADAR (אוטומטי)
# ========================================================
@tasks.loop(seconds=60)
async def update_discord_radar():
    global status_message
    await bot.wait_until_ready()
    
    guild = bot.get_guild(GUILD_ID)
    channel = bot.get_channel(STATUS_CHANNEL_ID)

    if not guild or not channel:
        print("[ERROR] Guild or Channel missing. Check IDs!")
        return

    # פיצ'ר אבטחה: סנכרון וטעינת כל חברי השרת לזיכרון בלייב
    if len(guild.members) < guild.member_count:
        await guild.chunk()

    # חישוב משתמשי השרת (אמת בלבד ללא בוטים)
    total_members = guild.member_count
    bot_count = sum(1 for m in guild.members if m.bot)
    real_humans = total_members - bot_count
    
    # חישוב חברים אונליין (Online / DND / Idle)
    online_members = sum(1 for m in guild.members if m.status in [discord.Status.online, discord.Status.dnd, discord.Status.idle] and not m.bot)
    
    # חישוב אנשי צוות אונליין (לפי הרול שסיפקת)
    staff_role = guild.get_role(STAFF_ROLE_ID)
    total_staff = len(staff_role.members) if staff_role else 0
    online_staff = sum(1 for m in staff_role.members if m.status in [discord.Status.online, discord.Status.dnd, discord.Status.idle]) if staff_role else 0

    # חישוב רמת הבוסטים של השרת (פיצ'ר יוקרתי נוסף)
    boost_count = guild.premium_subscription_count
    boost_level = guild.premium_tier

    # בניית ה-Embed בעיצוב הייטק מפואר וחדשני
    embed = discord.Embed(
        title=f"✨ {SERVER_NAME} | Live Discord Panel",
        description="ברוכים הבאים ללוח הבקרה והסטטיסטיקות הרשמי של הקהילה.\nהנתונים הבאים מסונכרנים ישירות משרתי דיסקורד ומתעדכנים בכל 60 שניות.\n",
        color=0x5865F2  # כחול דיסקורד רשמי ויוקרתי
    )
    
    # קוביית משתמשי הקהילה
    embed.add_field(
        name="👥 חברי הקהילה (Users)",
        value=f"```properties\n"
              f"Total Members  : {total_members}\n"
              f"Real Humans    : {real_humans}\n"
              f"Online Users   : {online_members}\n"
              f"```",
        inline=False
    )
    
    # קוביית אנשי הצוות
    embed.add_field(
        name="🛡️ סטטוס צוות הניהול (Staff)",
        value=f"```properties\n"
              f"Total Staff    : {total_staff}\n"
              f"Staff Online   : {online_staff}\n"
              f"```",
        inline=False
    )

    # קוביית פיצ'רים של השרת
    embed.add_field(
        name="💎 שדרוגים ותשתית (Server Level)",
        value=f"```properties\n"
              f"Server Boosts  : {boost_count} Boosts\n"
              f"Boost Level    : Level {boost_level}\n"
              f"System Security: Maximum (Verified)\n"
              f"```",
        inline=False
    )

    # כפתורים אינטראקטיביים מתחת להודעה (פיצ'ר אקסטרה יפה)
    view = discord.ui.View()
    view.add_item(discord.ui.Button(label="📢 Updates Channel", url="https://discord.com", style=discord.ButtonStyle.link))
    view.add_item(discord.ui.Button(label="🎁 Store / Support", url="https://discord.com", style=discord.ButtonStyle.link))
    
    if guild.icon: 
        embed.set_thumbnail(url=guild.icon.url)
        
    embed.set_footer(text="🔄 Chicago City Automation System • Live Sync")
    embed.timestamp = discord.utils.utcnow()

    # מנגנון שליחה קשיח ואוטומטי לחלוטין לחדר הפרטי
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
    except Exception as e:
        print(f"[Discord Embed Error] {e}")
# ========================================================
# 4. מערכת אימות (Verify Panel)
# ========================================================
class VerifyView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Verify Me", style=discord.ButtonStyle.green, custom_id="verify_btn")
    async def verify_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        role = interaction.guild.get_role(VERIFY_ROLE_ID)
        if not role: return await interaction.response.send_message("Verify role not found!", ephemeral=True)
        if role in interaction.user.roles: await interaction.response.send_message("You are already verified!", ephemeral=True)
        else:
            await interaction.user.add_roles(role)
            await interaction.response.send_message("Successfully verified! Welcome.", ephemeral=True)

# ========================================================
# 5. מערכת טיקטים (Ticket System)
# ========================================================
class TicketControlView(discord.ui.View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="🔒 Close Ticket", style=discord.ButtonStyle.danger, custom_id="close_ticket_btn")
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Closing ticket...", ephemeral=False)
        await asyncio.sleep(3)
        await interaction.channel.delete()

class TicketOpenView(discord.ui.View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="📩 Open Ticket", style=discord.ButtonStyle.primary, custom_id="open_ticket_btn")
    async def open_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = interaction.guild
        ticket_name = f"ticket-{interaction.user.name}".lower()
        if discord.utils.get(guild.channels, name=ticket_name):
            return await interaction.response.send_message("You already have an open ticket!", ephemeral=True)
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True, attach_files=True),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }
        channel = await guild.create_text_channel(name=ticket_name, overwrites=overwrites)
        embed = discord.Embed(title="Support Ticket", description="Staff will be with you shortly.", color=discord.Color.blue())
        await channel.send(embed=embed, view=TicketControlView())
        await interaction.response.send_message(f"Ticket created: {channel.mention}", ephemeral=True)

# ========================================================
# 6. פקודות ניהול והקמה (Setup Commands)
# ========================================================
@bot.command()
@commands.has_permissions(administrator=True)
async def setup_verify(ctx):
    embed = discord.Embed(title=f"Welcome to {SERVER_NAME}", description="Click below to verify.", color=discord.Color.green())
    await ctx.send(embed=embed, view=VerifyView())
    await ctx.message.delete()

@bot.command()
@commands.has_permissions(administrator=True)
async def setup_tickets(ctx):
    embed = discord.Embed(title="Support", description="Click below to open a ticket.", color=discord.Color.blue())
    await ctx.send(embed=embed, view=TicketOpenView())
    await ctx.message.delete()

# --- מערכת הצעות (Suggestions) ---
@bot.command()
async def suggest(ctx, *, suggestion: str):
    await ctx.message.delete()
    embed = discord.Embed(title="New Suggestion!", description=suggestion, color=discord.Color.gold())
    embed.set_footer(text=f"By: {ctx.author}")
    msg = await ctx.send(embed=embed)
    await msg.add_reaction("✅")
    await msg.add_reaction("❌")

# --- מערכת אזהרות (Warnings) ---
@bot.command()
@commands.has_permissions(kick_members=True)
async def warn(ctx, member: discord.Member, *, reason: str = "No reason"):
    if member.id not in warnings_db: warnings_db[member.id] = []
    warnings_db[member.id].append(reason)
    await ctx.send(f"{member.mention} warned. Total: {len(warnings_db[member.id])}")

@bot.command()
async def warnings(ctx, member: discord.Member = None):
    member = member or ctx.author
    warns = warnings_db.get(member.id, [])
    if not warns: return await ctx.send("No warnings.")
    await ctx.send(f"{member.name} has {len(warns)} warnings.")

# --- טעינת כפתורים קבועים בהפעלת הבוט (Persistent Views) ---
@bot.event
async def on_connect():
    bot.add_view(VerifyView())
    bot.add_view(TicketOpenView())
    bot.add_view(TicketControlView())

@bot.event
async def on_ready():
    print(f"System Operational: {bot.user.name}")
    # הסרת סטטוס ה-Watching מהביו לחלוטין כפי שביקשת
    await bot.change_presence(activity=None)
    if not update_discord_radar.is_running():
        update_discord_radar.start()

# ========================================================
# 7. הרצת הבוט
# ========================================================
if __name__ == "__main__":
    keep_alive()  
    token = os.getenv("DISCORD_TOKEN")
    if token: bot.run(token)
