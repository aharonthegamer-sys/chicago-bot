import os
import asyncio
from flask import Flask
from threading import Thread
import discord
from discord.ext import tasks, commands

app = Flask('')

@app.route('/')
def home():
    return "Chicago City Center is Active!"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run_flask)
    t.daemon = True
    t.start()

SERVER_NAME = "Chicago City Roleplay"
GUILD_ID = 1483039214793789483
STATUS_CHANNEL_ID = 1506965475270332476
VERIFY_ROLE_ID = 1483039214793789489
STAFF_ROLE_ID = 1483039215364345930

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True 
intents.guilds = True         
intents.members = True        
intents.presences = True      

bot = commands.Bot(command_prefix="!", intents=intents, chunk_guilds_at_startup=True)
status_message = None
warnings_db = {}

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


class VerifyView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🔑 אימות חשבון / VERIFY", style=discord.ButtonStyle.green, custom_id="verify_btn")
    async def verify_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        role = interaction.guild.get_role(VERIFY_ROLE_ID)
        if not role: 
            return await interaction.response.send_message("❌ רול אימות לא נמצא.", ephemeral=True)
        
        if role in interaction.user.roles: 
            return await interaction.response.send_message("ℹ️ אתה כבר מאומת במערכת.", ephemeral=True)
        
        await interaction.user.add_roles(role)
        await interaction.response.send_message("✅ אושרת בהצלחה! ברוך הבא ל-Chicago City.", ephemeral=True)
class RenameTicketModal(discord.ui.Modal, title="📝 שינוי שם הערוץ"):
    new_name = discord.ui.TextInput(label="הזן שם חדש לערוץ (באותיות קטנות)", placeholder="e.g., bug-fixed", required=True, min_length=3, max_length=20)

    async def on_submit(self, interaction: discord.Interaction):
        clean_name = self.new_name.value.lower().replace(" ", "-")
        await interaction.channel.edit(name=clean_name)
        embed = discord.Embed(description=f"✏️ שם הערוץ שונה בהצלחה ל: **{clean_name}**", color=discord.Color.blue())
        await interaction.response.send_message(embed=embed)


class AddMemberModal(discord.ui.Modal, title="👤 הוספת חבר לטיקט"):
    member_id = discord.ui.TextInput(label="הזן את ה-ID של המשתמש", placeholder="e.g., 1483039214793789483", required=True, min_length=15, max_length=20)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            member = interaction.guild.get_member(int(self.member_id.value))
            if not member:
                member = await interaction.guild.fetch_member(int(self.member_id.value))
            if member:
                await interaction.channel.set_permissions(member, read_messages=True, send_messages=True, attach_files=True)
                embed = discord.Embed(description=f"✅ המשתמש {member.mention} התווסף לטיקט בהצלחה", color=discord.Color.green())
                await interaction.response.send_message(embed=embed)
            else:
                await interaction.response.send_message("❌ המשתמש לא נמצא בשרת.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ שגיאה במספר ה-ID: {e}", ephemeral=True)


class TicketControlView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🔒 סגור טיקט", style=discord.ButtonStyle.danger, custom_id="btn_close_t")
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("🛑 הטיקט ייסגר ויימחק מהמערכת בעוד 5 שניות...", ephemeral=False)
        await asyncio.sleep(5)
        await interaction.channel.delete()

    @discord.ui.button(label="🙋‍♂️ קח טיפול (Claim)", style=discord.ButtonStyle.success, custom_id="btn_claim_t")
    async def claim_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        staff_role = interaction.guild.get_role(STAFF_ROLE_ID)
        if staff_role not in interaction.user.roles and not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message("❌ רק אנשי צוות יכולים לקחת טיפול על פניות!", ephemeral=True)
        button.disabled = True
        button.label = f"🙋‍♂️ בטיפול של: {interaction.user.name}"
        button.style = discord.ButtonStyle.secondary
        embed = discord.Embed(description=f"💼 איש הצוות {interaction.user.mention} לקח את הטיקט תחת טיפולו.", color=discord.Color.green())
        await interaction.response.edit_message(view=self)
        await interaction.channel.send(embed=embed)

    @discord.ui.button(label="✏️ שינוי שם", style=discord.ButtonStyle.primary, custom_id="btn_rename_t")
    async def rename_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        staff_role = interaction.guild.get_role(STAFF_ROLE_ID)
        if staff_role not in interaction.user.roles and not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message("❌ הרשאה זו חסומה עבורך.", ephemeral=True)
        await interaction.response.send_modal(RenameTicketModal())

    @discord.ui.button(label="➕ הוסף משתמש", style=discord.ButtonStyle.secondary, custom_id="btn_add_m_t")
    async def add_member(self, interaction: discord.Interaction, button: discord.ui.Button):
        staff_role = interaction.guild.get_role(STAFF_ROLE_ID)
        if staff_role not in interaction.user.roles and not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message("❌ הרשאה זו חסומה עבורך.", ephemeral=True)
        await interaction.response.send_modal(AddMemberModal())
class TicketDropdown(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="דיווח על שחקן / צוות", description="Report a player or staff", emoji="🚨", value="report"),
            discord.SelectOption(label="דיווח על באג", description="Report a technical server bug", emoji="🐛", value="bug"),
            discord.SelectOption(label="בחינה לצוות השרת", description="Apply for a staff position", emoji="📝", value="apply"),
            discord.SelectOption(label="שאלה כללית / עזרה", description="General assistance", emoji="❓", value="general")
        ]
        super().__init__(placeholder="🔽 בחר את קטגוריית הפנייה שלך...", min_values=1, max_values=1, options=options, custom_id="ticket_dropdown_select")

    async def callback(self, interaction: discord.Interaction):
        category = self.values
        guild = interaction.guild
        category_titles = {"report": "🚨| דיווח שחקן-צוות", "bug": "🐛| דיווח על באג", "apply": "📝| בחינה לצוות", "general": "❓| שאלה כללית"}
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
            title=f"🎫 פנייה חדשה | קטגוריה: {category_titles[category]}",
            description=f"שלום רב {interaction.user.mention},\nצוות הניהול קיבל את פנייתך ויתפנה אליך בהקדם.\n\n**📋 כיצד להתקדם?**\nאנא פרט וספק את כל המידע הרלוונטי כאן בצ'אט.",
            color=0x5865F2
        )
        embed.add_field(name="👤 פותח הפנייה", value=interaction.user.mention, inline=True)
        embed.add_field(name="🛠️ פאנל ניהול", value="אנשי צוות, השתמשו בכפתורים מטה לניהול המקרה.", inline=True)
        embed.set_footer(text=f"Chicago City Network • {category_titles[category]}")
        embed.timestamp = discord.utils.utcnow()
        
        await channel.send(embed=embed, view=TicketControlView())
        await interaction.response.send_message(f"✅ הפנייה שנפתחה בהצלחה בחדר: {channel.mention}", ephemeral=True)


class TicketOpenView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(TicketDropdown())


@bot.command()
@commands.has_permissions(administrator=True)
async def setup_verify(ctx):
    await ctx.message.delete()
    embed = discord.Embed(
        title=f"🔐 מערכת אימות | {SERVER_NAME.upper()}",
        description="על מנת לקבל גישה מלאה לשרת, אנא לחץ על כפתור האימות המופיע מטה.\n\n**⚠️ שים לב:**\nבלחיצה אתה מאשר שקראת והסכמת לחוקי הקהילה.",
        color=0x2ecc71
    )
    if ctx.guild.icon:
        embed.set_thumbnail(url=ctx.guild.icon.url)
    embed.set_footer(text="Chicago City Protection Core")
    await ctx.send(embed=embed, view=VerifyView())


@bot.command()
@commands.has_permissions(administrator=True)
async def setup_tickets(ctx):
    await ctx.message.delete()
    embed = discord.Embed(
        title=f"🎫 מרכז תמיכה ופניות | {SERVER_NAME.upper()}",
        description="צריך עזרה? השתמש בתפריט הבחירה המופיע מטה, בחר את הקטגוריה המתאימה וחדר אישי ייפתח עבורך.",
        color=0x3498db
    )
    if ctx.guild.icon:
        embed.set_thumbnail(url=ctx.guild.icon.url)
    embed.set_footer(text="Chicago City Support Center")
    await ctx.send(embed=embed, view=TicketOpenView())


@bot.command()
async def suggest(ctx, *, suggestion: str):
    await ctx.message.delete()
    embed = discord.Embed(title="💡 הצעה חדשה מהקהילה", description=f"```{suggestion}```", color=0xf1c40f)
    embed.set_author(name=ctx.author.name, icon_url=ctx.author.display_avatar.url)
    embed.add_field(name="📊 מדד הצבעות", value="הצבע באמצעות האימוג'ים המופיעים מטה:", inline=False)
    embed.set_footer(text="Chicago City Suggestions")
    embed.timestamp = discord.utils.utcnow()
    msg = await ctx.send(embed=embed)
    await msg.add_reaction("✅")
    await msg.add_reaction("❌")


@bot.command()
@commands.has_permissions(kick_members=True)
async def warn(ctx, member: discord.Member, *, reason: str = "לא צוינה סיבה תקינה"):
    if member.id not in warnings_db: 
        warnings_db[member.id] = []
    warnings_db[member.id].append(reason)
    embed = discord.Embed(title="🛡️ רישום אזהרה למערכת", color=0xe67e22)
    embed.add_field(name="👤 משתמש שנאזן", value=member.mention, inline=True)
    embed.add_field(name="👮 האוכף", value=ctx.author.mention, inline=True)
    embed.add_field(name="📝 סיבת האזהרה", value=f"```{reason}```", inline=False)
    embed.add_field(name="📊 סך הכל אזהרות", value=f"`{len(warnings_db[member.id])}`", inline=False)
    embed.set_footer(text="Chicago City Moderation Core")
    embed.timestamp = discord.utils.utcnow()
    await ctx.send(embed=embed)


@bot.command()
async def warnings(ctx, member: discord.Member = None):
    member = member or ctx.author
    warns = warnings_db.get(member.id, [])
    if not warns: 
        return await ctx.send(f"🟢 **{member.name}** נקי לחלוטין ואין לו אזהרות רשומות במערכת.")
    embed = discord.Embed(title=f"📋 תיק אזהרות עבור {member.name.upper()}", color=0xe74c3c)
    for i, reason in enumerate(warns, 1):
        embed.add_field(name=f"📌 אזהרה מספר #{i}", value=f"סיבה: `{reason}`", inline=False)
    embed.set_footer(text=f"Total: {len(warns)} warnings")
    await ctx.send(embed=embed)


@bot.event
async def on_connect():
    bot.add_view(VerifyView())
    bot.add_view(TicketOpenView())
    bot.add_view(TicketControlView())


@bot.event
async def on_ready():
    print("==================================================")
    print(f" PREMIUM CORE OPERATIONAL: {bot.user.name.upper()}")
    print("==================================================")
    await bot.change_presence(activity=None)
    if not update_discord_radar.is_running():
        update_discord_radar.start()


if __name__ == "__main__":
    keep_alive()
    token = os.getenv("DISCORD_TOKEN")
    if token:
        bot.run(token)
