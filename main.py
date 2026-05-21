import discord
from discord.ext import commands, tasks
from discord.ui import Button, View, Select
import asyncio, datetime, os, random
from flask import Flask
from threading import Thread

app = Flask('')
@app.route('/')
def home(): return "Chicago City BOT is running 24/7!"
def run(): app.run(host='0.0.0.0', port=8080)
def keep_alive(): Thread(target=run).start()

intents = discord.Intents.default()
intents.message_content = intents.members = intents.guilds = intents.messages = intents.presences = True
bot = commands.Bot(command_prefix="!", intents=intents)

# איידיז קבועים — CHICAGO CITY
ROLE_VERIFIED = 1483039214793789489
ROLE_STAFF = 1483039215364345930
CHANNEL_GIVEAWAY = 1483039216366780532
ROLE_WARN_ADMIN = 1483039215393702012
CHANNEL_STAFF_WARNS_LOG = 1483039219336347810

LOG_CHANNELS = {
    "channel_create": 1483039219654852617, "channel_delete": 1483039219654852616,
    "channel_update": 1483039219923554468, "ban": 1483039219923554469,
    "unban": 1483039219923554470, "role_create": 1483039219923554471,
    "role_delete": 1483039219923554472, "message_edit": 1483039219923554473,
    "message_delete": 1483039219923554474, "welcome_embed": 1504124994999943269,
    "invite_tracker": 1506417177719210194, "security": 1483039220284002367
}

staff_warns_db, invites_cache = {}, {}

async def send_log(event_name, embed):
    ch_id = LOG_CHANNELS.get(event_name)
    if ch_id:
        channel = bot.get_channel(ch_id)
        if channel: await channel.send(embed=embed)

# מערכת אימות נקי — Chicago City
class VerifyView(View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="לחץ כאן לאימות 🛡️", style=discord.ButtonStyle.green, custom_id="verify_btn")
    async def verify_button(self, interaction: discord.Interaction, button: Button):
        await interaction.response.defer(ephemeral=True)
        role = interaction.guild.get_role(ROLE_VERIFIED)
        if role in interaction.user.roles: await interaction.followup.send("אתה כבר מאומת בשרת!", ephemeral=True)
        else:
            await interaction.user.add_roles(role)
            await interaction.followup.send("ברוך הבא ל-Chicago City! 🎉", ephemeral=True)

@bot.command()
@commands.has_permissions(administrator=True)
async def setup_verify(ctx):
    embed = discord.Embed(title="Chicago City", description="ברוכים הבאים לשרת הרשמי!\n\n**לחצו על הכפתור הירוק למטה כדי לקבל את רול התושב וגישה מלאה לערוצי השרת!**", color=discord.Color.from_rgb(46, 204, 113))
    embed.set_footer(text="Chicago City")
    if ctx.guild.icon: embed.set_image(url=ctx.guild.icon.url)
    await ctx.send(embed=embed, view=VerifyView())

# מערכת טיקטים נקי — Chicago City
class TicketControls(View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="קח טיפול 🙋‍♂️", style=discord.ButtonStyle.blurple, custom_id="tk_claim")
    async def claim(self, interaction: discord.Interaction, button: Button):
        await interaction.response.defer()
        if interaction.guild.get_role(ROLE_STAFF) not in interaction.user.roles: return
        await interaction.channel.send(f"🔒 הפנייה ננעלה בטיפול של {interaction.user.mention}")
        button.disabled = True; await interaction.message.edit(view=self)

    @discord.ui.button(label="סגור פנייה ❌", style=discord.ButtonStyle.red, custom_id="tk_close")
    async def close(self, interaction: discord.Interaction, button: Button):
        await interaction.response.defer()
        if interaction.guild.get_role(ROLE_STAFF) not in interaction.user.roles: return
        await interaction.channel.send("🚧 חדר הטיקט יימחק בעוד 5 שניות...")
        await asyncio.sleep(5); await interaction.channel.delete()

class TicketDropdown(Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="בחינה לצוות השרת", emoji="📝", value="צוות"),
            discord.SelectOption(label="דיווח על שחקן", emoji="🚫", value="דיווח"),
            discord.SelectOption(label="דיווח על באג", emoji="🐛", value="באג"),
            discord.SelectOption(label="שאלה כללית", emoji="❓", value="כללי")
        ]
        super().__init__(placeholder="בחר את נושא הפנייה לפתיחת טיקט... 📂", options=options, custom_id="tk_select")

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        ticket_channel = await interaction.guild.create_text_channel(name=f"ticket-{interaction.user.name}", category=interaction.channel.category)
        await ticket_channel.set_permissions(interaction.guild.default_role, read_messages=False)
        await ticket_channel.set_permissions(interaction.user, read_messages=True, send_messages=True)
        await ticket_channel.set_permissions(interaction.guild.get_role(ROLE_STAFF), read_messages=True, send_messages=True)
        await interaction.followup.send(f"✅ הטיקט נוצר! כנס לחדר: {ticket_channel.mention}", ephemeral=True)
        embed = discord.Embed(title="Chicago City", description=f"שלום {interaction.user.mention}, פנייתך בנושא `{self.values}` התקבלה!\nצוות השרת יגיע בהקדם.", color=discord.Color.red())
        embed.set_footer(text="Chicago City")
        if interaction.guild.icon: embed.set_image(url=interaction.guild.icon.url)
        await ticket_channel.send(embed=embed, view=TicketControls())
        p = await ticket_channel.send(f"<@&{ROLE_STAFF}>"); await p.delete()

@bot.command()
@commands.has_permissions(administrator=True)
async def setup_tickets(ctx):
    embed = discord.Embed(title="Chicago City", description="**בחר את המחלקה המתאימה בתפריט למטה לפתיחת חדר תמיכה!**", color=discord.Color.purple())
    embed.set_footer(text="Chicago City")
    if ctx.guild.icon: embed.set_image(url=ctx.guild.icon.url)
    await ctx.send(embed=embed, view=View().add_item(TicketDropdown()))

# מערכת הגרלות נקי
class AdvancedGiveawayView(View):
    def __init__(self, prize, winners):
        super().__init__(timeout=None)
        self.prize, self.winners, self.entrants, self.active = prize, winners, [], True
    @discord.ui.button(label="הצטרף להגרלה 🎉", style=discord.ButtonStyle.green, custom_id="gv_join")
    async def join(self, interaction: discord.Interaction, b: Button):
        await interaction.response.defer(ephemeral=True)
        if not self.active: return await interaction.followup.send("❌ ההגרלה הסתיימה!", ephemeral=True)
        if interaction.user.id in self.entrants: return await interaction.followup.send("אתה כבר רשום! 🍀", ephemeral=True)
        self.entrants.append(interaction.user.id)
        await interaction.followup.send("✅ נרשמת בהצלחה!", ephemeral=True)

    @discord.ui.button(label="כמות משתתפים 📈", style=discord.ButtonStyle.grey, custom_id="gv_status")
    async def status(self, interaction: discord.Interaction, b: Button):
        await interaction.response.defer(ephemeral=True)
        await interaction.followup.send(f"יש כרגע `{len(self.entrants)}` משתתפים.", ephemeral=True)

    @discord.ui.button(label="סגור הגרלה ⏱️", style=discord.ButtonStyle.red, custom_id="gv_end_now")
    async def end_early(self, interaction: discord.Interaction, b: Button):
        await interaction.response.defer()
        if interaction.guild.get_role(ROLE_STAFF) not in interaction.user.roles: return
        self.active = False; await end_gv(interaction.channel, self.prize, self.winners, self.entrants, interaction.message)

async def end_gv(channel, prize, winners, entrants, msg):
    if len(entrants) < winners: await msg.edit(embed=discord.Embed(title="Chicago City", description="ההגרלה בוטלה עקב חוסר משתתפים.", color=discord.Color.red()), view=None)
    else:
        w = random.sample(entrants, winners); m = ", ".join([f"<@{x}>" for x in w])
        await msg.edit(embed=discord.Embed(title="Chicago City", description=f"**ההגרלה הסתיימה!**\n\n**הפרס:** {prize}\n**הזוכים:** {m}", color=discord.Color.green()), view=None)
        await channel.send(f"🎉 **מזל טוב לזוכים בהגרלה על {prize}!** {m}")

@bot.command()
@commands.has_permissions(manage_messages=True)
async def giveaway(ctx, duration: int, winners: int, *, prize: str):
    embed = discord.Embed(title="Chicago City", description=f"🏆 **פרס:** `{prize}`\n👥 **זוכים:** `{winners}`\n⏱️ **זמן:** `{duration}` דקות", color=discord.Color.gold())
    embed.set_footer(text="Chicago City")
    v = AdvancedGiveawayView(prize, winners)
    msg = await bot.get_channel(CHANNEL_GIVEAWAY).send(embed=embed, view=v); await ctx.send("✅ ההגרלה שודרה בהצלחה!")
    await asyncio.sleep(duration * 60)
    if v.active: v.active = False; await end_gv(bot.get_channel(CHANNEL_GIVEAWAY), prize, winners, v.entrants, msg)

# מערכת אזהרות צוות נקי — Chicago City
@bot.command()
async def warn(ctx, member: discord.Member, *, reason: str = "לא צוינה סיבה"):
    if ctx.guild.get_role(ROLE_WARN_ADMIN) not in ctx.author.roles and not ctx.author.guild_permissions.administrator:
        return await ctx.send("❌ **אין לך הרשאה לבצע פעולה זו!**")
    if member.id not in staff_warns_db: staff_warns_db[member.id] = []
    t = datetime.datetime.now().strftime("%d/%m/%Y | %H:%M")
    staff_warns_db[member.id].append({"reason": reason, "by": ctx.author.id, "date": t})
    count = len(staff_warns_db[member.id])
    log_ch = bot.get_channel(CHANNEL_STAFF_WARNS_LOG)
    if log_ch:
        embed = discord.Embed(title="Chicago City", description="**רישום אזהרה לחבר צוות**", color=discord.Color.red())
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.add_field(name="👤 המנהל שהוזהר", value=member.mention, inline=True)
        embed.add_field(name="🛡️ האדמין המעניש", value=ctx.author.mention, inline=True)
        embed.add_field(name="📅 זמן האירוע", value=f"`{t}`", inline=False)
        embed.add_field(name="📝 סיבת האזהרה", value=f"```fix\n{reason}```", inline=False)
        bars = "Core" if count > 3 else "🟥" * count + "⬛" * (3 - count)
        embed.add_field(name="📊 תיק אזהרות", value=f"{bars} ({count}/3 אזהרות)", inline=False)
        embed.set_footer(text="Chicago City")
        if ctx.guild.icon: embed.set_image(url=ctx.guild.icon.url)
        await log_ch.send(embed=embed)
    await ctx.send(f"✅ **האזהרה נרשמה בהצלחה בלוג!** (סה''כ: `{count}`)")

@bot.command()
async def warns(ctx, member: discord.Member):
    c = len(staff_warns_db.get(member.id, []))
    if c == 0: return await ctx.send(f"🟢 {member.mention} נקי ללא אזהרות.")
    embed = discord.Embed(title=f"Chicago City — תיק אזהרות ל-{member.name}", color=discord.Color.orange())
    for i, w in enumerate(staff_warns_db[member.id], 1):
        embed.add_field(name=f"🚨 אזהרה {i} ({w['date']})", value=f"• ע''י: <@{w['by']}>\n• סיבה: {w['reason']}", inline=False)
    embed.set_footer(text="Chicago City")
    await ctx.send(embed=embed)

@bot.command()
async def unwarn(ctx, member: discord.Member):
    if ctx.guild.get_role(ROLE_WARN_ADMIN) not in ctx.author.roles and not ctx.author.guild_permissions.administrator: return
    if member.id in staff_warns_db and len(staff_warns_db[member.id]) > 0:
        staff_warns_db[member.id].pop(); await ctx.send(f"✅ האזהרה האחרונה של {member.mention} נמחקה.")
    else: await ctx.send("אין אזהרות בתיק.")

# מערכת כריזה וחדשות
@bot.command()
@commands.has_permissions(administrator=True)
async def say(ctx, channel: discord.TextChannel, em: str, *, content: str):
    embed = discord.Embed(description=content, color=discord.Color.blue()); embed.set_footer(text="Chicago City")
    await channel.send(embed=embed); await ctx.send("✅ ההכרזה נשלחה!")

# לוגים אוטומטיים
@bot.event
async def on_guild_channel_create(c): await send_log("channel_create", discord.Embed(title="Chicago City", description=f"🟢 ערוץ נוצר: {c.name}", color=discord.Color.green()))
@bot.event
async def on_guild_channel_delete(c): await send_log("channel_delete", discord.Embed(title="Chicago City", description=f"🔴 ערוץ נמחק: {c.name}", color=discord.Color.red()))
@bot.event
async def on_message_edit(b, a):
    if b.author.bot or b.content == a.content: return
    await send_log("message_edit", discord.Embed(title="Chicago City", description=f"📝 הודעה נערכה ע''י {b.author.mention}\nחדר: {b.channel.mention}\nישן: {b.content}\nחדש: {a.content}", color=discord.Color.gold()))
@bot.event
async def on_message_delete(m):
    if m.author.bot: return
    await send_log("message_delete", discord.Embed(title="Chicago City", description=f"🗑️ הודעה נמחקה ע''י {m.author.mention}\nחדר: {m.channel.mention}\nתוכן: {m.content}", color=discord.Color.red()))

@bot.event
async def on_member_join(member):
    w_ch = bot.get_channel(LOG_CHANNELS["welcome_embed"])
    if w_ch:
        embed = discord.Embed(title="Chicago City", description=f"💎 ברוך הבא, {member.name}! 💎\nכנס לערוץ האימות לקבלת גישה: <#{ROLE_VERIFIED}> 🛡️", color=discord.Color.red())
        embed.set_thumbnail(url=member.display_avatar.url); embed.set_footer(text="Chicago City")
        if member.guild.icon: embed.set_image(url=member.guild.icon.url)
        await w_ch.send(embed=embed)

@tasks.loop(minutes=10)
async def update_stats():
    for g in bot.guilds:
        online = sum(1 for m in g.members if m.status != discord.Status.offline and not m.bot)
        r = g.get_role(ROLE_STAFF); staff = sum(1 for m in r.members if m.status != discord.Status.offline and not m.bot) if r else 0
        async def up(prefix, val):
            name = f"{prefix} {val}"
            ch = discord.utils.get(g.voice_channels, name=name)
            if not ch:
                for vc in g.voice_channels:
                    if vc.name.startswith(prefix): await vc.edit(name=name); return
                await g.create_voice_channel(name=name, overwrites={g.default_role: discord.PermissionOverwrite(connect=False)})
            else: await ch.edit(name=name)
        try:
            await up("👥 Total Members:", g.member_count); await up("🟢 Online Users:", online); await up("🛡️ Staff Online:", staff)
        except: pass

@bot.event
async def on_ready(): print(f"Logged in as {bot.user.name}"); update_stats.start()

keep_alive()
bot.run(os.environ['DISCORD_TOKEN'])
