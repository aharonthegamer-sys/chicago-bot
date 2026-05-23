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
# 2. קונפיגורציה קשיחה והפרדת ערוצי לוגים מוחלטת
# ========================================================
SERVER_NAME = "Chicago City Roleplay"
GUILD_ID = 1483039214793789483

STATUS_CHANNEL_ID = 1506965475270332476
GIVEAWAY_PANEL_CH = 1507022943413342328
GIVEAWAY_FEED_CH = 1483039216366780532
WARN_PANEL_CH = 1507023136095207515
WARN_FEED_CH = 1483039219336347810
SUGGEST_PANEL_CH = 1507020507776811068
SUGGEST_FEED_CH = 1483039217482334253
LOG_TICKET = 1483039219654852612
LOG_CHANNEL_DELETE = 1483039219654852616
LOG_CHANNEL_CREATE = 1483039219654852617
LOG_CHANNEL_UPDATE = 1483039219923554468
LOG_BAN_ADD = 1483039219923554469
LOG_BAN_REMOVE = 1483039219923554470
LOG_ROLE_CREATE = 1483039219923554471
LOG_ROLE_DELETE = 1483039219923554472
LOG_MEMBER_ADD = 1483039219923554475
LOG_MEMBER_REMOVE = 1483039219923554476
LOG_SECURITY = 1483039220284002367

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

async def dispatch_log(target_channel_id, title, description, color=0x5865F2, fields=None):
    channel = bot.get_channel(target_channel_id)
    if not channel:
        return
    embed = discord.Embed(title=title, description=description, color=color)
    if fields:
        for name, value in fields.items():
            embed.add_field(name=name, value=value, inline=True)
    embed.set_footer(text="Chicago City Audit Core")
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
        description="Live statistics panel. Data updates every 60 seconds.",
        color=0x010101 
    )
    embed.add_field(name="Community Members", value=f"```md\n# Total Members : {total_members}\n* Real Humans   : {real_humans}\n* Online Users  : {online_members}\n```", inline=True)
    embed.add_field(name="Staff Status", value=f"```md\n# Total Staff   : {total_staff}\n* Staff Online  : {online_staff}\n* Status        : Secured\n```", inline=True)
    embed.add_field(name="Server Upgrades", value=f"```Server Boosts  : {boost_count} Boosts\nBoost Level    : Level {boost_level}\nAnti-Raid Core : Active```", inline=False)
    view = discord.ui.View()
    view.add_item(discord.ui.Button(label="Web Store", url="https://discord.com", style=discord.ButtonStyle.link))
    if guild.icon: embed.set_thumbnail(url=guild.icon.url)
    embed.set_footer(text="Chicago City Automation Core")
    embed.timestamp = discord.utils.utcnow()
    try:
        if status_message is None:
            async for msg in channel.history(limit=5):
                if msg.author == bot.user and msg.embeds:
                    status_message = msg
                    break
        if status_message: await status_message.edit(embed=embed, view=view)
        else: status_message = await channel.send(embed=embed, view=view)
    except: pass
class VerifyView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🔑 אימות חשבון / VERIFY", style=discord.ButtonStyle.green, custom_id="verify_btn_v5")
    async def verify_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        role = interaction.guild.get_role(VERIFY_ROLE_ID)
        if not role: return await interaction.response.send_message("Verify role missing.", ephemeral=True)
        if role in interaction.user.roles: return await interaction.response.send_message("Already verified.", ephemeral=True)
        await interaction.user.add_roles(role)
        await interaction.response.send_message("Successfully verified!", ephemeral=True)
        await dispatch_log(LOG_SECURITY, "🔐 User Verified", f"{interaction.user.mention} verified.", 0x2ecc71, {"User": interaction.user.name})

class RenameTicketModal(discord.ui.Modal, title="Rename"):
    new_name = discord.ui.TextInput(label="New Name", placeholder="support-fixed")
    async def on_submit(self, interaction: discord.Interaction):
        clean_name = self.new_name.value.lower().replace(" ", "-")
        await interaction.channel.edit(name=clean_name)
        await interaction.response.send_message("Renamed.")
        await dispatch_log(LOG_TICKET, "✏️ Renamed", f"Renamed to {clean_name}", 0x3498db)

class AddMemberModal(discord.ui.Modal, title="Add Member"):
    member_id = discord.ui.TextInput(label="ID")
    async def on_submit(self, interaction: discord.Interaction):
        try:
            member = interaction.guild.get_member(int(self.member_id.value)) or await interaction.guild.fetch_member(int(self.member_id.value))
            if member:
                await interaction.channel.set_permissions(member, read_messages=True, send_messages=True)
                await interaction.response.send_message("Added member.")
                await dispatch_log(LOG_TICKET, "➕ Member Added", f"Added {member.name}", 0x9b59b6)
            else: await interaction.response.send_message("Not found", ephemeral=True)
        except: await interaction.response.send_message("Error", ephemeral=True)
class TicketControlView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🔒 Close", style=discord.ButtonStyle.danger, custom_id="btn_close_v5")
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Closing in 5s...")
        await dispatch_log(LOG_TICKET, "🔒 Closed", f"{interaction.channel.name} closed.", 0xe74c3c)
        await asyncio.sleep(5)
        await interaction.channel.delete()

    @discord.ui.button(label="🙋‍♂️ Claim", style=discord.ButtonStyle.success, custom_id="btn_claim_v5")
    async def claim_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        staff_role = interaction.guild.get_role(STAFF_ROLE_ID)
        if staff_role not in interaction.user.roles and not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message("Denied", ephemeral=True)
        button.disabled, button.label = True, f"Claimed by: {interaction.user.name}"
        await interaction.response.edit_message(view=self)
        await dispatch_log(LOG_TICKET, "💼 Claimed", f"Claimed by {interaction.user.name}", 0x2ecc71)

    @discord.ui.button(label="✏️ Rename", style=discord.ButtonStyle.primary, custom_id="btn_rn_v5")
    async def rename_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(RenameTicketModal())

    @discord.ui.button(label="➕ Add Member", style=discord.ButtonStyle.secondary, custom_id="btn_add_v5")
    async def add_member(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(AddMemberModal())
class TicketDropdown(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="דיווח על שחקן / צוות", value="report", emoji="🚨"),
            discord.SelectOption(label="דיווח על באג", value="bug", emoji="🐛"),
            discord.SelectOption(label="בחינה לצוות השרת", value="apply", emoji="📝"),
            discord.SelectOption(label="שאלה כללית / עזרה", value="general", emoji="❓")
        ]
        super().__init__(placeholder="Select category", options=options, custom_id="dropdown_v5")

    async def callback(self, interaction: discord.Interaction):
        category = self.values[0]
        guild = interaction.guild
        ticket_name = f"{category}-{interaction.user.name}".lower()
        if discord.utils.get(guild.channels, name=ticket_name):
            return await interaction.response.send_message("Ticket already open.", ephemeral=True)
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }
        channel = await guild.create_text_channel(name=ticket_name, overwrites=overwrites)
        embed = discord.Embed(title=f"Ticket | {category.upper()}", description="Explain your issue.", color=0x5865F2)
        embed.timestamp = discord.utils.utcnow()
        await channel.send(embed=embed, view=TicketControlView())
        await interaction.response.send_message(f"Created: {channel.mention}", ephemeral=True)
        await dispatch_log(LOG_TICKET, "📩 Ticket Opened", f"Opened by {interaction.user.name}", 0xe67e22)

class TicketOpenView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(TicketDropdown())
class CreateGiveawayModal(discord.ui.Modal, title="Giveaway"):
    g_title = discord.ui.TextInput(label="Prize")
    g_time = discord.ui.TextInput(label="Time (Minutes)")
    async def on_submit(self, interaction: discord.Interaction):
        feed = bot.get_channel(GIVEAWAY_FEED_CH)
        embed = discord.Embed(title="🎁 GIVEAWAY", description=f"Prize: {self.g_title.value}\nTime: {self.g_time.value}m", color=0x2ecc71)
        msg = await feed.send(embed=embed)
        await msg.add_reaction("🎉")
        await interaction.response.send_message("Giveaway created.", ephemeral=True)

class GiveawayPanelView(discord.ui.View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="🎁 Open Giveaway", style=discord.ButtonStyle.green, custom_id="g_panel_v5")
    async def open_g(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.guild.get_role(GIVEAWAY_ROLE_ID) not in interaction.user.roles and not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message("No permission.", ephemeral=True)
        await interaction.response.send_modal(CreateGiveawayModal())

class IssueWarnModal(discord.ui.Modal, title="Warn"):
    u_id = discord.ui.TextInput(label="User ID")
    u_reason = discord.ui.TextInput(label="Reason")
    async def on_submit(self, interaction: discord.Interaction):
        feed = bot.get_channel(WARN_FEED_CH)
        try:
            member = interaction.guild.get_member(int(self.u_id.value)) or await interaction.guild.fetch_member(int(self.u_id.value))
            if member.id not in warnings_db: warnings_db[member.id] = []
            warnings_db[member.id].append(self.u_reason.value)
            embed = discord.Embed(title="🚨 WARNING", description=f"User: {member.mention}\nReason: {self.u_reason.value}", color=0xe67e22)
            await feed.send(embed=embed)
            await interaction.response.send_message("Warned member.", ephemeral=True)
        except: await interaction.response.send_message("Error ID", ephemeral=True)

class WarnPanelView(discord.ui.View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="⚠️ Issue Warn", style=discord.ButtonStyle.danger, custom_id="w_panel_v5")
    async def issue_w(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.guild.get_role(WARN_STAFF_ROLE_ID) not in interaction.user.roles and not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message("No permission.", ephemeral=True)
        await interaction.response.send_modal(IssueWarnModal())

class CreateSuggestionModal(discord.ui.Modal, title="Suggestion"):
    s_text = discord.ui.TextInput(label="Suggestion text", style=discord.TextStyle.paragraph)
    async def on_submit(self, interaction: discord.Interaction):
        feed = bot.get_channel(SUGGEST_FEED_CH)
        embed = discord.Embed(title="💡 SUGGESTION", description=self.s_text.value, color=0xf1c40f)
        msg = await feed.send(embed=embed)
        await msg.add_reaction("✅")
        await msg.add_reaction("❌")
        await interaction.response.send_message("Suggestion submitted.", ephemeral=True)

class SuggestionsPanelView(discord.ui.View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="🗳️ Submit Suggestion", style=discord.ButtonStyle.primary, custom_id="s_panel_v5")
    async def open_s(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.guild.get_role(VERIFY_ROLE_ID) not in interaction.user.roles and not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message("Please verify first.", ephemeral=True)
        await interaction.response.send_modal(CreateSuggestionModal())
@bot.command()
@commands.has_permissions(administrator=True)
async def setup_all_panels(ctx):
    await ctx.message.delete()
    g_ch = bot.get_channel(GIVEAWAY_PANEL_CH)
    if g_ch: await g_ch.send(embed=discord.Embed(title="Giveaway Dashboard", color=0x2ecc71), view=GiveawayPanelView())
    w_ch = bot.get_channel(WARN_PANEL_CH)
    if w_ch: await w_ch.send(embed=discord.Embed(title="Warning Dashboard", color=0xe67e22), view=WarnPanelView())
    s_ch = bot.get_channel(SUGGEST_PANEL_CH)
    if s_ch: await s_ch.send(embed=discord.Embed(title="Suggestion Dashboard", color=0xf1c40f), view=SuggestionsPanelView())

@bot.command()
@commands.has_permissions(administrator=True)
async def setup_verify(ctx):
    await ctx.message.delete()
    await ctx.send(embed=discord.Embed(title="Verify Panel", description="Click to verify", color=0x2ecc71), view=VerifyView())

@bot.command()
@commands.has_permissions(administrator=True)
async def setup_tickets(ctx):
    await ctx.message.delete()
    await ctx.send(embed=discord.Embed(title="Ticket Support", description="Select category", color=0x3498db), view=TicketOpenView())

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
    print("====================================")
    print("PREMIUM LOG NETWORK SECURED")
    print("====================================")
    await bot.change_presence(activity=None)
    if not update_discord_radar.is_running(): update_discord_radar.start()

if __name__ == "__main__":
    keep_alive()
    token = os.getenv("DISCORD_TOKEN")
    if token: bot.run(token)
