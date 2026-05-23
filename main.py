import os
import asyncio
from flask import Flask
from threading import Thread
import discord
from discord.ext import tasks, commands

app = Flask('')

@app.route('/')
def home():
    return "Core Online"

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
        title=f"{SERVER_NAME.upper()} | LIVE STATS",
        description="Live statistics panel.",
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
        value=f"```Server Boosts  : {boost_count}\nBoost Level    : {boost_level}```",
        inline=False
    )

    view = discord.ui.View()
    view.add_item(discord.ui.Button(label="Store", url="https://discord.com", style=discord.ButtonStyle.link))
    
    if guild.icon: 
        embed.set_thumbnail(url=guild.icon.url)
        
    embed.set_footer(text="Chicago City Core")
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

    @discord.ui.button(label="VERIFY", style=discord.ButtonStyle.green, custom_id="verify_btn")
    async def verify_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        role = interaction.guild.get_role(VERIFY_ROLE_ID)
        if not role: 
            return await interaction.response.send_message("Role missing.", ephemeral=True)
        if role in interaction.user.roles: 
            return await interaction.response.send_message("Verified.", ephemeral=True)
        await interaction.user.add_roles(role)
        await interaction.response.send_message("Success.", ephemeral=True)
class RenameTicketModal(discord.ui.Modal, title="Rename Channel"):
    new_name = discord.ui.TextInput(label="Channel Name", placeholder="support-fixed", required=True)

    async def on_submit(self, interaction: discord.Interaction):
        clean_name = self.new_name.value.lower().replace(" ", "-")
        await interaction.channel.edit(name=clean_name)
        await interaction.response.send_message(f"Changed to {clean_name}")

class AddMemberModal(discord.ui.Modal, title="Add Member"):
    member_id = discord.ui.TextInput(label="Member ID", placeholder="1483039214793789483", required=True)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            member = interaction.guild.get_member(int(self.member_id.value))
            if not member:
                member = await interaction.guild.fetch_member(int(self.member_id.value))
            if member:
                await interaction.channel.set_permissions(member, read_messages=True, send_messages=True)
                await interaction.response.send_message("Added")
            else:
                await interaction.response.send_message("Not found", ephemeral=True)
        except:
            await interaction.response.send_message("Error", ephemeral=True)

class TicketControlView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Close", style=discord.ButtonStyle.danger, custom_id="btn_close_t")
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Closing...")
        await asyncio.sleep(5)
        await interaction.channel.delete()

    @discord.ui.button(label="Claim", style=discord.ButtonStyle.success, custom_id="btn_claim_t")
    async def claim_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        staff_role = interaction.guild.get_role(STAFF_ROLE_ID)
        if staff_role not in interaction.user.roles and not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message("Denied", ephemeral=True)
        button.disabled = True
        button.label = f"Claimed by {interaction.user.name}"
        await interaction.response.edit_message(view=self)

    @discord.ui.button(label="Rename", style=discord.ButtonStyle.primary, custom_id="btn_rename_t")
    async def rename_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(RenameTicketModal())

    @discord.ui.button(label="Add", style=discord.ButtonStyle.secondary, custom_id="btn_add_m_t")
    async def add_member(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(AddMemberModal())

class TicketDropdown(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Report Player", value="report"),
            discord.SelectOption(label="Bug", value="bug"),
            discord.SelectOption(label="Apply", value="apply"),
            discord.SelectOption(label="General", value="general")
        ]
        super().__init__(placeholder="Select category", options=options, custom_id="ticket_dropdown_select")

    async def callback(self, interaction: discord.Interaction):
        category = self.values[0]
        guild = interaction.guild
        ticket_name = f"{category}-{interaction.user.name}".lower()
        
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }
        channel = await guild.create_text_channel(name=ticket_name, overwrites=overwrites)
        
        embed = discord.Embed(title="Ticket Open", description="Explain issue", color=0x5865F2)
        embed.timestamp = discord.utils.utcnow()
        await channel.send(embed=embed, view=TicketControlView())
        await interaction.response.send_message("Created", ephemeral=True)

class TicketOpenView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(TicketDropdown())

@bot.command()
@commands.has_permissions(administrator=True)
async def setup_verify(ctx):
    await ctx.message.delete()
    embed = discord.Embed(title="Verification", description="Click to verify", color=0x2ecc71)
    await ctx.send(embed=embed, view=VerifyView())

@bot.command()
@commands.has_permissions(administrator=True)
async def setup_tickets(ctx):
    await ctx.message.delete()
    embed = discord.Embed(title="Tickets", description="Select category", color=0x3498db)
    await ctx.send(embed=embed, view=TicketOpenView())

@bot.command()
async def suggest(ctx, *, message: str):
    await ctx.message.delete()
    embed = discord.Embed(title="Suggestion", description=message, color=0xf1c40f)
    await ctx.send(embed=embed)

@bot.command()
@commands.has_permissions(kick_members=True)
async def warn(ctx, member: discord.Member, *, reason: str = "None"):
    if member.id not in warnings_db: warnings_db[member.id] = []
    warnings_db[member.id].append(reason)
    await ctx.send("Warned")

@bot.command()
async def warnings(ctx, member: discord.Member = None):
    member = member or ctx.author
    await ctx.send(f"Warnings count: {len(warnings_db.get(member.id, []))}")

@bot.event
async def on_connect():
    bot.add_view(VerifyView())
    bot.add_view(TicketOpenView())
    bot.add_view(TicketControlView())

@bot.event
async def on_ready():
    await bot.change_presence(activity=None)
    if not update_discord_radar.is_running():
        update_discord_radar.start()

if __name__ == "__main__":
    keep_alive()
    token = os.getenv("DISCORD_TOKEN")
    if token:
        bot.run(token)
