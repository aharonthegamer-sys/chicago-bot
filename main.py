import os
import asyncio
from flask import Flask
from threading import Thread
import discord
from discord.ext import tasks, commands

# ========================================================
# 1. שרת FLASK פנימי עבור RENDER (מניעת קריסות פורטים)
# ========================================================
app = Flask('')

@app.route('/')
def home():
    return "Chicago City System Core Online"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run_flask)
    t.daemon = True
    t.start()

# ========================================================
# 2. קונפיגורציה ואינטנטס אבטחה של CHICAGO CITY
# ========================================================
SERVER_NAME = "Chicago City Roleplay"
GUILD_ID = 1483039214793789483
STATUS_CHANNEL_ID = 1506965475270332476

# החלף את ה-ID הבא ל-ID של ערוץ הלוגים שלכם בדיסקורד (לדוגמה ערוץ #bot-cmd או #table)
DISCORD_LOG_CHANNEL_ID = 1506965475270332476 

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
        name="Community Members",
        value=f"```md\n# Total Members : {total_members}\n* Real Humans   : {real_humans}\n* Online Users  : {online_members}\n```",
        inline=True
    )
    embed.add_field(
        name="Staff Status",
        value=f"```md\n# Total Staff   : {total_staff}\n* Staff Online  : {online_staff}\n* Status        : Secured\n```",
        inline=True
    )
    embed.add_field(
        name="Server Upgrades",
        value=f"```Server Boosts  : {boost_count} Boosts\nBoost Level    : Level {boost_level}\nAnti-Raid Core : Active```",
        inline=False
    )

    view = discord.ui.View()
    view.add_item(discord.ui.Button(label="Web Store", url="https://discord.com", style=discord.ButtonStyle.link))
    view.add_item(discord.ui.Button(label="Server Rules", url="https://discord.com", style=discord.ButtonStyle.link))
    
    if guild.icon: 
        embed.set_thumbnail(url=guild.icon.url)
    embed.set_footer(text="Chicago City Automation Core")
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
class RenameTicketModal(discord.ui.Modal, title="Rename Channel"):
    new_name = discord.ui.TextInput(label="Enter new channel name", placeholder="support-fixed", required=True)

    async def on_submit(self, interaction: discord.Interaction):
        old_name = interaction.channel.name
        clean_name = self.new_name.value.lower().replace(" ", "-")
        await interaction.channel.edit(name=clean_name)
        await interaction.response.send_message(f"Channel name changed to: {clean_name}")
        await send_discord_log(
            title="✏️ Ticket Renamed",
            description=f"Staff {interaction.user.mention} renamed a support ticket channel.",
            color=0x3498db,
            fields={"Old Name": old_name, "New Name": clean_name, "Staff": interaction.user.name}
        )

class AddMemberModal(discord.ui.Modal, title="Add Member"):
    member_id = discord.ui.TextInput(label="Enter Member ID", placeholder="1483039214793789483", required=True)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            member = interaction.guild.get_member(int(self.member_id.value))
            if not member:
                member = await interaction.guild.fetch_member(int(self.member_id.value))
            if member:
                await interaction.channel.set_permissions(member, read_messages=True, send_messages=True, attach_files=True)
                await interaction.response.send_message(f"Added {member.mention} to this ticket.")
                await send_discord_log(
                    title="➕ Member Added to Ticket",
                    description=f"Staff {interaction.user.mention} added a member to a ticket.",
                    color=0x9b59b6,
                    fields={"Ticket Channel": interaction.channel.name, "Added User": member.name, "Staff": interaction.user.name}
                )
            else:
                await interaction.response.send_message("User not found.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"Error configuration ID: {e}", ephemeral=True)

class TicketControlView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🔒 סגור טיקט / Close", style=discord.ButtonStyle.danger, custom_id="btn_close_t_exp")
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Closing ticket in 5 seconds...")
        await send_discord_log(
            title="🔒 Ticket Closed",
            description=f"Ticket channel **{interaction.channel.name}** was deleted.",
            color=0xe74c3c,
            fields={"Closed By": interaction.user.name, "Channel": interaction.channel.name}
        )
        await asyncio.sleep(5)
        await interaction.channel.delete()

    @discord.ui.button(label="🙋‍♂️ קח טיפול / Claim", style=discord.ButtonStyle.success, custom_id="btn_claim_t_exp")
    async def claim_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        staff_role = interaction.guild.get_role(STAFF_ROLE_ID)
        if staff_role not in interaction.user.roles and not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message("Staff only feature.", ephemeral=True)
        button.disabled = True
        button.label = f"Claimed by: {interaction.user.name}"
        button.style = discord.ButtonStyle.secondary
        await interaction.response.edit_message(view=self)
        embed = discord.Embed(description=f"Ticket claimed by {interaction.user.mention}", color=discord.Color.green())
        await interaction.channel.send(embed=embed)
        await send_discord_log(
            title="💼 Ticket Claimed",
            description=f"Staff {interaction.user.mention} claimed a ticket under management control.",
            color=0x2ecc71,
            fields={"Ticket": interaction.channel.name, "Staff Member": interaction.user.name}
        )

    @discord.ui.button(label="✏️ שינוי שם", style=discord.ButtonStyle.primary, custom_id="btn_rename_t_exp")
    async def rename_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        staff_role = interaction.guild.get_role(STAFF_ROLE_ID)
        if staff_role not in interaction.user.roles and not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message("Permission denied.", ephemeral=True)
        await interaction.response.send_modal(RenameTicketModal())

    @discord.ui.button(label="➕ הוסף משתמש", style=discord.ButtonStyle.secondary, custom_id="btn_add_m_t_exp")
    async def add_member(self, interaction: discord.Interaction, button: discord.ui.Button):
        staff_role = interaction.guild.get_role(STAFF_ROLE_ID)
        if staff_role not in interaction.user.roles and not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message("Permission denied.", ephemeral=True)
        await interaction.response.send_modal(AddMemberModal())
class TicketDropdown(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="דיווח על שחקן / צוות", description="Report a player or staff", emoji="🚨", value="report"),
            discord.SelectOption(label="דיווח על באג", description="Report a technical server bug", emoji="🐛", value="bug"),
            discord.SelectOption(label="בחינה לצוות השרת", description="Apply for a staff position", emoji="📝", value="apply"),
            discord.SelectOption(label="שאלה כללית / עזרה", description="General assistance", emoji="❓", value="general")
        ]
        super().__init__(placeholder="Select your ticket category...", min_values=1, max_values=1, options=options, custom_id="ticket_dropdown_select_exp")

    async def callback(self, interaction: discord.Interaction):
        category = self.values
        guild = interaction.guild
        category_titles = {"report": "Report Player/Staff", "bug": "Bug Report", "apply": "Staff Application", "general": "General Help"}
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
            title=f"Ticket Channel | Category: {category_titles[category]}",
            description=f"Hello {interaction.user.mention},\nStaff will assist you shortly. Please explain your issue here.",
            color=0x5865F2
        )
        embed.add_field(name="Ticket Opener", value=interaction.user.mention, inline=True)
        embed.add_field(name="Staff Panel", value="Staff can use buttons below to manage.", inline=True)
        embed.set_footer(text="Chicago City Support")
        embed.timestamp = discord.utils.utcnow()
        
        await channel.send(embed=embed, view=TicketControlView())
        await interaction.response.send_message(f"Ticket created: {channel.mention}", ephemeral=True)
        
        await send_discord_log(
            title="📩 New Ticket Opened",
            description=f"User {interaction.user.mention} opened a support ticket.",
            color=0xe67e22,
            fields={"Category": category_titles[category], "Channel": channel.mention, "User": interaction.user.name}
        )

class TicketOpenView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(TicketDropdown())

@bot.command()
@commands.has_permissions(administrator=True)
async def setup_verify(ctx):
    await ctx.message.delete()
    embed = discord.Embed(
        title=f"Verification | {SERVER_NAME.upper()}",
        description="Click the button below to verify your account and get full access.",
        color=0x2ecc71
    )
    if ctx.guild.icon:
        embed.set_thumbnail(url=ctx.guild.icon.url)
    embed.set_footer(text="Chicago City System Protection")
    await ctx.send(embed=embed, view=VerifyView())

@bot.command()
@commands.has_permissions(administrator=True)
async def setup_tickets(ctx):
    await ctx.message.delete()
    embed = discord.Embed(
        title=f"Support System | {SERVER_NAME.upper()}",
        description="Need support? Use the dropdown menu below to select your category and open a ticket.",
        color=0x3498db
    )
    if ctx.guild.icon:
        embed.set_thumbnail(url=ctx.guild.icon.url)
    embed.set_footer(text="Chicago City Support Center")
    await ctx.send(embed=embed, view=TicketOpenView())

@bot.command()
async def suggest(ctx, *, suggestion: str):
    await ctx.message.delete()
    embed = discord.Embed(title="New Suggestion", description=f"```{suggestion}```", color=0xf1c40f)
    embed.set_author(name=ctx.author.name, icon_url=ctx.author.display_avatar.url)
    embed.set_footer(text="Chicago City Suggestions")
    embed.timestamp = discord.utils.utcnow()
    msg = await ctx.send(embed=embed)
    await msg.add_reaction("✅")
    await msg.add_reaction("❌")
    
    await send_discord_log(
        title="💡 New User Suggestion Created",
        description=f"A new idea was logged by {ctx.author.mention}.",
        color=0xf1c40f,
        fields={"Author": ctx.author.name, "Suggestion": suggestion}
    )

@bot.command()
@commands.has_permissions(kick_members=True)
async def warn(ctx, member: discord.Member, *, reason: str = "No reason provided"):
    if member.id not in warnings_db: 
        warnings_db[member.id] = []
    warnings_db[member.id].append(reason)
    embed = discord.Embed(title="Warning Issued", color=0xe67e22)
    embed.add_field(name="User", value=member.mention, inline=True)
    embed.add_field(name="Moderator", value=ctx.author.mention, inline=True)
    embed.add_field(name="Reason", value=f"```{reason}```", inline=False)
    embed.add_field(name="Total Warnings", value=f"`{len(warnings_db[member.id])}`", inline=False)
    embed.set_footer(text="Chicago City Moderation")
    embed.timestamp = discord.utils.utcnow()
    await ctx.send(embed=embed)
    
    await send_discord_log(
        title="🛡️ Security Warning Logged",
        description=f"Moderator flagged a system infraction.",
        color=0xe67e22,
        fields={"Target": member.name, "Moderator": ctx.author.name, "Infraction": reason}
    )

@bot.command()
async def warnings(ctx, member: discord.Member = None):
    member = member or ctx.author
    warns = warnings_db.get(member.id, [])
    if not warns: 
        return await ctx.send(f"User {member.name} has no warnings.")
    embed = discord.Embed(title=f"Warnings History for {member.name.upper()}", color=0xe74c3c)
    for i, reason in enumerate(warns, 1):
        embed.add_field(name=f"Warning #{i}", value=f"Reason: `{reason}`", inline=False)
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
    print(f"PREMIUM CORE OPERATIONAL: {bot.user.name.upper()}")
    print("==================================================")
    await bot.change_presence(activity=None)
    if not update_discord_radar.is_running():
        update_discord_radar.start()

if __name__ == "__main__":
    keep_alive()
    token = os.getenv("DISCORD_TOKEN")
    if token:
        bot.run(token)
