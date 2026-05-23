import os
import asyncio
import aiohttp
from flask import Flask
from threading import Thread
import discord
from discord.ext import tasks, commands

# אתחול שרת Flask עבור Render
app = Flask('')

@app.route('/')
def home():
    return "Status Bot Online!"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run_flask)
    t.daemon = True
    t.start()

# נתונים קבועים ומדויקים של שיקגו סיטי
SERVER_NAME = "Chicago City"
CFX_CODE = "rmadb7p"
SERVER_IP = "135.148.36.192:30125"
GUILD_ID = 1483039214793789483
STATUS_CHANNEL_ID = 1506965475270332476
VERIFY_ROLE_ID = 1483039214793789489

intents = discord.Intents.default()
intents.messages = True
intents.guilds = True         
intents.members = True        

bot = commands.Bot(command_prefix="!", intents=intents)
status_message = None

@tasks.loop(seconds=60)
async def update_status():
    global status_message
    await bot.wait_until_ready()
    
    guild = bot.get_guild(GUILD_ID)
    channel = bot.get_channel(STATUS_CHANNEL_ID)

    if not guild or not channel:
        print("[ERROR] Guild or Channel not found!")
        return

    # נתוני דיסקורד בסיסיים שחסינים מקריסות
    total_members = guild.member_count

    # ערכי ברירת מחדל
    clients = 0
    max_clients = 32
    status_text = "🟢 פעיל (Online)"
    embed_color = discord.Color.green()

    # קריאת נתוני FiveM מוגנת בתוך בלוק try/except שלא מסוגל לתקוע את הבוט
    url = f"https://fivem.net{CFX_CODE}"
    headers = {"User-Agent": "Mozilla/5.0"}
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, timeout=5) as response:
                if response.status == 200:
                    data = await response.json()
                    server_data = data.get('Data', {})
                    if server_data:
                        clients = server_data.get('clients', 0)
                        max_clients = server_data.get('sv_maxclients', 32)
                else:
                    status_text = "🔴 מנותק / תחזוקה"
                    embed_color = discord.Color.red()
    except:
        status_text = "🔴 מנותק / שגיאת API"
        embed_color = discord.Color.red()

    # בניית ה-Embed המעוצב לחדר
    embed = discord.Embed(
        title=f"📊 סטטוס רשת | {SERVER_NAME}",
        description="הנתונים מתעדכנים באופן אוטומטי לחלוטין בכל 60 שניות.",
        color=embed_color
    )
    embed.add_field(
        name="🎮 שרת המשחק (FiveM)",
        value=f"```properties\nStatus   : {status_text}\nPlayers  : {clients}/{max_clients}\nServer IP: {SERVER_IP}\n```",
        inline=False
    )
    embed.add_field(
        name="👥 שרת הדיסקורד (Discord)",
        value=f"```properties\nTotal Members : {total_members}\n```",
        inline=False
    )

    view = discord.ui.View()
    view.add_item(discord.ui.Button(label="⚡ התחברות מהירה לעיר", url=f"https://cfx.re{CFX_CODE}", style=discord.ButtonStyle.link))
    if guild.icon: embed.set_thumbnail(url=guild.icon.url)
    embed.set_footer(text="Chicago City Network")
    embed.timestamp = discord.utils.utcnow()

    # מנגנון שליחה/עריכה אוטומטי ללא פקודות
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
        print(f"[Discord Error] {e}")

@bot.event
async def on_ready():
    print(f"Bot is ready: {bot.user.name}")
    if not update_status.is_running():
        update_status.start()
# מאגר נתונים זמני בזיכרון עבור אזהרות
warnings_db = {}

# מערכת פקודות מובנית שעובדת במקביל ל-on_ready
@bot.event
async def on_message(message):
    if message.author.bot:
        return
    await bot.process_commands(message)

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

# --- הרצת הבוט ---
if __name__ == "__main__":
    keep_alive()  # הפעלת שרת ה-Flask לטובת Render
    
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        print("ERROR: DISCORD_TOKEN environment variable is missing!")
    else:
        bot.run(token)
