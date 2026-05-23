import os
import asyncio
import aiohttp
from flask import Flask
from threading import Thread
import discord
from discord.ext import tasks, commands

# הגדרות שרת Flask עבור Render לטובת זמינות 24/7
app = Flask('')

@app.route('/')
def home():
    return "Chicago City Bot - Advanced Status is Online!"

def run_flask():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run_flask)
    t.daemon = True
    t.start()

# נתונים קבועים ומדויקים של שרת שיקגו סיטי
SERVER_NAME = "Chicago City"
CFX_CODE = "rmadb7p"
SERVER_IP = "135.148.36.192:30125"
GUILD_ID = 1483039214793789483
STATUS_CHANNEL_ID = 1506965475270332476
VERIFY_ROLE_ID = 1483039214793789489
STAFF_ROLE_ID = 1483039215364345930

# הגדרת הבוט והפעלת כל ה-Intents הנדרשים לספירת משתמשים אונליין
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
intents.members = True        # קריטי: מאפשר לבוט לראות את כל הממברים
intents.guilds = True         # קריטי: מאפשר לבוט לקרוא נתוני שרת קבועים
intents.presences = True      # קריטי: מאפשר לבוט לזהות מצבי חיבור (Online/DND/Idle)

bot = commands.Bot(command_prefix="!", intents=intents)
status_message = None

@tasks.loop(seconds=60)
async def update_fivem_status():
    global status_message
    await bot.wait_until_ready()
    
    guild = bot.get_guild(GUILD_ID)
    channel = bot.get_channel(STATUS_CHANNEL_ID)
    
    if not guild:
        print(f"[ERROR] הבוט לא נמצא בשרת עם ה-ID שסופק: {GUILD_ID}")
        return
    if not channel:
        print(f"[ERROR] הבוט לא מוצא את חדר הסטטוס {STATUS_CHANNEL_ID}. ודא שיש לבוט הרשאת צפייה בחדר זה!")
        return

    # 1. חישוב נתונים מדויקים של שרת הדיסקורד (כולל צוות וממברים מחוברים)
    total_members = guild.member_count
    
    # סינון חברים שנמצאים במצב אונליין, נא לא להפריע או לא זמין
    online_members = sum(1 for m in guild.members if m.status in [discord.Status.online, discord.Status.dnd, discord.Status.idle] and not m.bot)
    
    staff_role = guild.get_role(STAFF_ROLE_ID)
    online_staff_discord = 0
    if staff_role:
        online_staff_discord = sum(1 for m in staff_role.members if m.status in [discord.Status.online, discord.Status.dnd, discord.Status.idle])

    # 2. משיכת נתוני שחקנים וצוות משרת ה-FiveM (מנגנון עקיפה כפול)
    dynamic_url = f"http://{SERVER_IP}/dynamic.json"
    players_url = f"http://{SERVER_IP}/players.json"
    proxy_url = f"https://fivem.net{CFX_CODE}"
    
    clients = 0
    max_clients = 32
    staff_online_fivem = 0
    server_online = False

    async with aiohttp.ClientSession() as session:
        try:
            # ניסיון פנייה ישיר ראשון ל-IP של השרת
            async with session.get(dynamic_url, timeout=5) as response:
                if response.status == 200:
                    data = await response.json()
                    clients = data.get('clients', 0)
                    max_clients = data.get('sv_maxclients', 32)
                    server_online = True
                    
                    # פנייה לקבלת רשימת שחקנים וזיהוי אנשי צוות בתוך המשחק
                    async with session.get(players_url, timeout=5) as p_resp:
                        if p_resp.status == 200:
                            p_data = await p_resp.json()
                            for player in p_data:
                                identifiers = player.get('identifiers', [])
                                for ident in identifiers:
                                    if ident.startswith('discord:'):
                                        d_id = int(ident.split(':'))
                                        member = guild.get_member(d_id)
                                        if member and staff_role in member.roles:
                                            staff_online_fivem += 1
                                            break
        except Exception as e:
            print(f"[INFO] Direct IP failed, trying Cfx Proxy: {e}")
            # ניסיון פנייה שני דרך שרת ה-Proxy הרשמי של Cfx במקרה של חסימת פורט
            try:
                headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
                async with session.get(proxy_url, headers=headers, timeout=6) as resp:
                    if resp.status == 200:
                        proxy_data = await resp.json()
                        server_data = proxy_data.get('Data', {})
                        clients = server_data.get('clients', 0)
                        max_clients = server_data.get('sv_maxclients', 32)
                        server_online = True
                        
                        players_list = server_data.get('players', [])
                        for player in players_list:
                            identifiers = player.get('identifiers', [])
                            for ident in identifiers:
                                if ident.startswith('discord:'):
                                    d_id = int(ident.split(':'))
                                    member = guild.get_member(d_id)
                                    if member and staff_role in member.roles:
                                        staff_online_fivem += 1
                                        break
            except Exception as backup_error:
                print(f"[ERROR] All FiveM API endpoints failed: {backup_error}")

    # 3. עדכון הסטטוס המשחקי של הבוט (Custom Status Bio)
    if server_online:
        activity_text = f"{clients} / {max_clients} of FIVEM"
        status_text = "🟢 Server Online"
        status_color = discord.Color.green()
    else:
        activity_text = "0 / 32 of FIVEM"
        status_text = "🔴 Server Offline"
        status_color = discord.Color.red()

    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name=activity_text))

    # 4. יצירת הודעת הסטטוס המורחבת והיוקרתית (Sleek Embed Design)
    embed = discord.Embed(
        title=f"📊 {SERVER_NAME} | Live Network Status",
        description="Here you can see the live statistics of our game and discord servers.",
        color=status_color
    )
    
    embed.add_field(
        name="🎮 FiveM Server Statistics",
        value=f"```properties\n"
              f"Server Status   : {status_text}\n"
              f"Online Players  : {clients}/{max_clients}\n"
              f"Staff In-Game   : {staff_online_fivem}\n"
              f"Server IP       : {SERVER_IP}\n"
              f"```",
        inline=False
    )
    
    embed.add_field(
        name="👥 Discord Server Statistics",
        value=f"```properties\n"
              f"Total Members   : {total_members}\n"
              f"Online Members  : {online_members}\n"
              f"Staff Online    : {online_staff_discord}\n"
              f"```",
        inline=False
    )

    view = discord.ui.View()
    view.add_item(discord.ui.Button(label="⚡ Connect to FiveM", url=f"https://cfx.re{CFX_CODE}", style=discord.ButtonStyle.link))

    if guild.icon:
        embed.set_thumbnail(url=guild.icon.url)
        
    embed.set_footer(text="🔄 Auto-updates every 60 seconds")
    embed.timestamp = discord.utils.utcnow()

    # 5. ניקוי וניהול הודעות בחדר למניעת תקיעות וחללים ריקים
    try:
        if status_message is None:
            # הבוט סורק את החדר כדי לבדוק אם שלח הודעה בעבר כדי לערוך אותה במקום להספים
            async for msg in channel.history(limit=10):
                if msg.author == bot.user and msg.embeds:
                    status_message = msg
                    break
        
        if status_message:
            await status_message.edit(embed=embed, view=view)
        else:
            status_message = await channel.send(embed=embed, view=view)
    except Exception as e:
        print(f"[ERROR] Failed to send/edit embed status message: {e}")

@bot.event
async def on_ready():
    print(f"Bot successfully authenticated as {bot.user.name} and initialized database caches.")
    if not update_fivem_status.is_running():
        update_fivem_status.start()
# מאגר נתונים זמני בזיכרון עבור אזהרות
warnings_db = {}

# --- מערכת אימות (Verify Panel) ---
class VerifyView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Verify Me", style=discord.ButtonStyle.green, custom_id="verify_btn")
    async def verify_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        role = interaction.guild.get_role(VERIFY_ROLE_ID)
        if not role:
            return await interaction.response.send_message("Verify role not found!", ephemeral=True)
        
        if role in interaction.user.roles:
            await interaction.response.send_message("You are already verified!", ephemeral=True)
        else:
            await interaction.user.add_roles(role)
            await interaction.response.send_message("Successfully verified! Welcome to Chicago City.", ephemeral=True)

# --- מערכת טיקטים (Ticket System) ---
class TicketControlView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🔒 Close Ticket", style=discord.ButtonStyle.danger, custom_id="close_ticket_btn")
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Closing ticket in 5 seconds...", ephemeral=False)
        await asyncio.sleep(5)
        await interaction.channel.delete()

class TicketOpenView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="📩 Open Ticket", style=discord.ButtonStyle.primary, custom_id="open_ticket_btn")
    async def open_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = interaction.guild
        ticket_name = f"ticket-{interaction.user.name}".lower()
        
        existing_channel = discord.utils.get(guild.channels, name=ticket_name)
        if existing_channel:
            return await interaction.response.send_message(f"You already have an open ticket: {existing_channel.mention}", ephemeral=True)

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True, attach_files=True),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }

        channel = await guild.create_text_channel(name=ticket_name, overwrites=overwrites)
        
        embed = discord.Embed(
            title=f"{SERVER_NAME} | Support Ticket",
            description=f"Hello {interaction.user.mention},\nStaff will be with you shortly. Click the button below to close this ticket.",
            color=discord.Color.blue()
        )
        await channel.send(embed=embed, view=TicketControlView())
        await interaction.response.send_message(f"Ticket created: {channel.mention}", ephemeral=True)

# --- פקודות ניהול והקמה (Setup Commands) ---
@bot.command()
@commands.has_permissions(administrator=True)
async def setup_verify(ctx):
    embed = discord.Embed(
        title=f"Welcome to {SERVER_NAME}",
        description="Click the button below to verify your account and gain access to the server.",
        color=discord.Color.green()
    )
    await ctx.send(embed=embed, view=VerifyView())
    await ctx.message.delete()

@bot.command()
@commands.has_permissions(administrator=True)
async def setup_tickets(ctx):
    embed = discord.Embed(
        title=f"{SERVER_NAME} | Support",
        description="Need help? Click the button below to open a support ticket.",
        color=discord.Color.blue()
    )
    await ctx.send(embed=embed, view=TicketOpenView())
    await ctx.message.delete()

# --- מערכת הצעות (Suggestions) ---
@bot.command()
async def suggest(ctx, *, suggestion: str):
    await ctx.message.delete()
    embed = discord.Embed(
        title="New Suggestion!",
        description=suggestion,
        color=discord.Color.gold()
    )
    embed.set_footer(text=f"Suggested by: {ctx.author}", icon_url=ctx.author.display_avatar.url)
    msg = await ctx.send(embed=embed)
    await msg.add_reaction("✅")
    await msg.add_reaction("❌")

# --- מערכת אזהרות (Warnings) ---
@bot.command()
@commands.has_permissions(kick_members=True)
async def warn(ctx, member: discord.Member, *, reason: str = "No reason provided"):
    if member.id not in warnings_db:
        warnings_db[member.id] = []
    
    warnings_db[member.id].append(reason)
    total_warns = len(warnings_db[member.id])
    
    embed = discord.Embed(
        title="Member Warned",
        description=f"{member.mention} has been warned.\n**Reason:** {reason}\n**Total Warnings:** {total_warns}",
        color=discord.Color.orange()
    )
    await ctx.send(embed=embed)

@bot.command()
async def warnings(ctx, member: discord.Member = None):
    member = member or ctx.author
    warns = warnings_db.get(member.id, [])
    
    if not warns:
        return await ctx.send(f"{member.mention} has no warnings.")
    
    embed = discord.Embed(title=f"Warnings for {member.name}", color=discord.Color.red())
    for i, reason in enumerate(warns, 1):
        embed.add_field(name=f"Warning #{i}", value=reason, inline=False)
    await ctx.send(embed=embed)

# --- טעינת כפתורים קבועים בהפעלת הבוט (Persistent Views) ---
@bot.event
async def on_connect():
    bot.add_view(VerifyView())
    bot.add_view(TicketOpenView())
    bot.add_view(TicketControlView())

# --- הרצת השרת והבוט ---
if __name__ == "__main__":
    keep_alive()  # הפעלת שרת ה-Flask לטובת Render
    
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        print("ERROR: DISCORD_TOKEN environment variable is missing!")
    else:
        bot.run(token)
