import os
import aiohttp
import discord
from discord.ext import tasks, commands

# נתונים קבועים להטמעה
SERVER_NAME = "Chicago City"
CFX_CODE = "rmadb7p"
STATUS_CHANNEL_ID = 1506965475270332476
STAFF_ROLE_ID = 1483039215364345930

# אתחול הבוט עם Intents נדרשים לספירת משתמשים
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
intents.members = True        
intents.guilds = True         
intents.presences = True      

bot = commands.Bot(command_prefix="!", intents=intents)
status_message = None

@tasks.loop(minutes=2)
async def update_fivem_status():
    global status_message
    await bot.wait_until_ready()
    
    channel = bot.get_channel(STATUS_CHANNEL_ID)
    if not channel:
        print(f"[ERROR] ערוץ סטטוס {STATUS_CHANNEL_ID} לא נמצא.")
        return
    guild = channel.guild

    # 1. חישוב נתוני דיסקורד (חברי שרת וצוות אונליין)
    total_members = guild.member_count
    staff_role = guild.get_role(STAFF_ROLE_ID)
    
    online_staff_discord = 0
    if staff_role:
        online_staff_discord = sum(1 for m in staff_role.members if m.status in [discord.Status.online, discord.Status.dnd, discord.Status.idle])

    # 2. משיכת נתונים מה-API הרשמי של FiveM למניעת חסימות פורטים
    url = f"https://fivem.net{CFX_CODE}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    clients = 0
    max_clients = 0
    staff_online_fivem = 0
    server_online = False

    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, headers=headers, timeout=15) as response:
                if response.status == 200:
                    data = await response.json()
                    server_data = data.get('Data', {})
                    if server_data:
                        clients = server_data.get('clients', 0)
                        max_clients = server_data.get('sv_maxclients', 0)
                        
                        if max_clients > 0:
                            server_online = True
                            # ספירת אנשי צוות שנמצאים פיזית בתוך העיר
                            players_list = server_data.get('players', [])
                            for player in players_list:
                                for ident in player.get('identifiers', []):
                                    if ident.startswith('discord:'):
                                        try:
                                            d_id = int(ident.split(':')[1])
                                            member = guild.get_member(d_id)
                                            if member and staff_role in member.roles:
                                                staff_online_fivem += 1
                                        except:
                                            pass
        except Exception as e:
            print(f"[FiveM API Error] {e}")

    # 3. עדכון הסטטוס המשחקי של הבוט (Bio) ובניית ה-Embed
    if server_online:
        # שרת פתוח - ירוק
        status_text = "🟢 פעיל (Online)"
        embed_color = discord.Color.green()
        activity_text = f"City: {clients} / {max_clients} 🎮"
    else:
        # שרת סגור או שגיאה - אדום
        status_text = "🔴 מנותק (Offline)"
        embed_color = discord.Color.red()
        activity_text = "Chicago City 🎮"

    # עדכון הנוכחות בדיסקורד
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name=activity_text))

    # 4. יצירת הודעת ה-Embed המעוצבת
    embed = discord.Embed(
        title=f"📊 סטטוס רשת | {SERVER_NAME}",
        description="הנתונים מתעדכנים באופן אוטומטי לחלוטין כל 2 דקות.",
        color=embed_color
    )
    
    embed.add_field(
        name="🎮 שרת המשחק (FiveM)",
        value=f"```properties\n"
              f"Status        : {status_text}\n"
              f"Players       : {clients}/{max_clients}\n"
              f"Staff In-Game : {staff_online_fivem}\n"
              f"```",
        inline=False
    )
    
    embed.add_field(
        name="👥 שרת הדיסקורד (Discord)",
        value=f"```properties\n"
              f"Total Members : {total_members}\n"
              f"Staff Online  : {online_staff_discord}\n"
              f"```",
        inline=False
    )
    
    if guild.icon:
        embed.set_thumbnail(url=guild.icon.url)
        
    embed.set_footer(text="Chicago City Network")
    embed.timestamp = discord.utils.utcnow()

    # כפתור חיבור מהיר מתחת להודעה
    view = discord.ui.View()
    view.add_item(discord.ui.Button(label="⚡ התחברות מהירה לעיר", url=f"https://cfx.re{CFX_CODE}", style=discord.ButtonStyle.link))

    # 5. ניהול שליחה/עריכה אוטומטית למניעת ספאם בערוץ
    try:
        if status_message is None:
            async for msg in channel.history(limit=10):
                if msg.author == bot.user and msg.embeds:
                    status_message = msg
                    break
        
        if status_message:
            await status_message.edit(embed=embed, view=view)
        else:
            status_message = await channel.send(embed=embed, view=view)
    except Exception as e:
        print(f"[Discord Write Error] {e}")

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user.name}")
    if not update_fivem_status.is_running():
        update_fivem_status.start()

# הרצת הבוט (בסביבת Render מומלץ להשתמש בטוקן מתוך Environment Variables)
if __name__ == "__main__":
    token = os.getenv("DISCORD_TOKEN")
    if token:
        bot.run(token)
    else:
        print("ERROR: DISCORD_TOKEN variable is missing.")
