import discord
from discord.ext import commands
from discord.ui import Button, View, Select
import asyncio
import datetime
from flask import Flask
from threading import Thread
import os

app = Flask('')

@app.route('/')
def home():
    return "Chicago City BOT is running 24/7!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True
intents.messages = True

bot = commands.Bot(command_prefix="!", intents=intents)

# איידיז נעולים וסופיים של CHICAGO CITY
ROLE_VERIFIED = 1483039214793789489
CATEGORY_TICKETS = 1483039218954534966 # האיידי המדויק ששלחת!
ROLE_STAFF = 1483039215364345930
CHANNEL_GIVEAWAY = 1483039216366780532

LOG_CHANNELS = {
    "channel_create": 1483039219654852617,
    "channel_delete": 1483039219654852616,
    "channel_update": 1483039219923554468,
    "ban": 1483039219923554469,
    "unban": 1483039219923554470,
    "role_create": 1483039219923554471,
    "role_delete": 1483039219923554472,
    "message_edit": 1483039219923554473,
    "message_delete": 1483039219923554474,
    "member_join": 1483039219923554475,
    "member_leave": 1483039219923554476,
    "welcome_embed": 1504124994999943269,
    "invite_tracker": 1506417177719210194,
    "security": 1483039220284002367
}

warnings_db = {}
invites_cache = {}

# מערכת אימות (VERIFICATION)
class VerifyView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="התאמת עכשיו 🛡️", style=discord.ButtonStyle.green, custom_id="verify_btn")
    async def verify_button(self, interaction: discord.Interaction, button: Button):
        await interaction.response.defer(ephemeral=True)
        role = interaction.guild.get_role(ROLE_VERIFIED)
        if role in interaction.user.roles:
            await interaction.followup.send("אתה כבר מאומת בשרת!", ephemeral=True)
        else:
            await interaction.user.add_roles(role)
            await interaction.followup.send("אימות בוצע בהצלחה! ברוך הבא ל-Chicago City. 🎉", ephemeral=True)

@bot.command()
@commands.has_permissions(administrator=True)
async def setup_verify(ctx):
    embed = discord.Embed(
        title="מערכת אימות - Chicago City",
        description="ברוכים הבאים לשרת הרשמי! לחצו על הכפתור הירוק למטה כדי להתאמת ולקבל גישה מלאה לשאר ערוצי השרת.",
        color=discord.Color.blue()
    )
    embed.set_footer(text="Chicago City Security")
    await ctx.send(embed=embed, view=VerifyView())

# מערכת טיקטים (TICKETS)
class TicketControls(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="קח טיפול 🙋‍♂️", style=discord.ButtonStyle.blurple, custom_id="ticket_claim")
    async def claim(self, interaction: discord.Interaction, button: Button):
        await interaction.response.defer()
        if not interaction.user.get_role(ROLE_STAFF):
            return await interaction.followup.send("אין לך הרשאה לבצע פעולה זו.", ephemeral=True)
        await interaction.channel.send(f"הפנייה נלקחה לטיפול על ידי {interaction.user.mention} 🔒")
        button.disabled = True
        await interaction.message.edit(view=self)

    @discord.ui.button(label="סגור פנייה ❌", style=discord.ButtonStyle.red, custom_id="ticket_close")
    async def close(self, interaction: discord.Interaction, button: Button):
        await interaction.response.defer()
        if not interaction.user.get_role(ROLE_STAFF):
            return await interaction.followup.send("אין לך הרשאה לבצע פעולה זו.", ephemeral=True)
        await interaction.followup.send("החדר ייסגר בעוד 5 שניות...")
        await asyncio.sleep(5)
        await interaction.channel.delete()

    @discord.ui.button(label="שנה שם 📝", style=discord.ButtonStyle.grey, custom_id="ticket_rename")
    async def rename(self, interaction: discord.Interaction, button: Button):
        await interaction.response.defer(ephemeral=True)
        if not interaction.user.get_role(ROLE_STAFF):
            return await interaction.followup.send("אין לך הרשאה לבצע פעולה זו.", ephemeral=True)
        
        await interaction.followup.send("אנא רשום את השם החדש לחדר בצ'אט:", ephemeral=True)
        def check(m): return m.author == interaction.user and m.channel == interaction.channel
        try:
            msg = await bot.wait_for('message', check=check, timeout=30)
            await interaction.channel.edit(name=f"ticket-{msg.content}")
            await interaction.channel.send(f"שם החדר שונה בהצלחה ל: {msg.content}")
        except asyncio.TimeoutError:
            await interaction.channel.send("הזמן לשינוי השם עבר.")

class TicketDropdown(Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="בחינה לצוות", emoji="📝", description="הגשת מועמדות לצוות השרת"),
            discord.SelectOption(label="דיווח על שחקן / צוות", emoji="🚫", description="דיווח על הפרת חוקים בשרת"),
            discord.SelectOption(label="דיווח על באג", emoji="🐛", description="דיווח על תקלה במערכות"),
            discord.SelectOption(label="שאלה כללית", emoji="❓", description="עזרה ופניות כלליות אחרות")
        ]
        super().__init__(placeholder="בחר את קטגוריית הפנייה שלך... 🎫", options=options, custom_id="ticket_select")

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        guild = interaction.guild
        category = guild.get_channel(CATEGORY_TICKETS)
        
        if not category:
            return await interaction.followup.send("שגיאה: קטגוריית הטיקטים לא נמצאה בשרת. ודא שהקטגוריה קיימת.", ephemeral=True)
            
        ticket_channel = await guild.create_text_channel(
            name=f"{self.values}-{interaction.user.name}",
            category=category
        )
        
        await ticket_channel.set_permissions(guild.default_role, read_messages=False)
        await ticket_channel.set_permissions(interaction.user, read_messages=True, send_messages=True)
        await ticket_channel.set_permissions(guild.get_role(ROLE_STAFF), read_messages=True, send_messages=True)
        
        await interaction.followup.send(f"הפנייה שלך נפתחה בהצלחה! כנס לחדר: {ticket_channel.mention}", ephemeral=True)
        
        embed = discord.Embed(
            title="פנייה חדשה בשרת 🎫",
            description=f"שלום {interaction.user.mention}, תודה שפתחת פנייה בנושא **{self.values}**!\nצוות השרת קיבל התראה ויגיע לעזור בהקדם.",
            color=discord.Color.orange()
        )
        await ticket_channel.send(embed=embed, view=TicketControls())

class TicketDropdownView(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(TicketDropdown())

@bot.command()
@commands.has_permissions(administrator=True)
async def setup_tickets(ctx):
    embed = discord.Embed(
        title="מערכת פניות ותמיכה - Chicago City 🎫",
        description="צריך עזרה או רוצה לפתוח פנייה לצוות? בחרו את הנושא המדויק מתוך התפריט הנפתח למטה.",
        color=discord.Color.purple()
    )
    await ctx.send(embed=embed, view=TicketDropdownView())

# הגרלות (GIVEAWAYS)
class GiveawayView(View):
    def __init__(self, message_id):
        super().__init__(timeout=None)
        self.message_id = message_id
        self.entrants = []

    @discord.ui.button(label="הצטרף להגרלה 🎉", style=discord.ButtonStyle.green, custom_id="join_giveaway")
    async def join(self, interaction: discord.Interaction, button: Button):
        await interaction.response.defer(ephemeral=True)
        if interaction.user.id in self.entrants:
            return await interaction.followup.send("אתה כבר רשום להגרלה זו!", ephemeral=True)
        self.entrants.append(interaction.user.id)
        await interaction.followup.send("נרשמת להגרלה בהצלחה! בהצלחה 🍀", ephemeral=True)

@bot.command()
@commands.has_permissions(manage_messages=True)
async def giveaway(ctx, duration: int, winners: int, *, prize: str):
    embed = discord.Embed(
        title="🎉 הגרלה חדשה יצאה לדרך! 🎉",
        description=f"**פרס:** {prize}\n**מספר זוכים:** {winners}\n**זמן לסיום:** {duration} דקות\n\nלחצו על הכפתור למטה כדי להיכנס!",
        color=discord.Color.gold()
    )
    channel = bot.get_channel(CHANNEL_GIVEAWAY)
    gv_view = GiveawayView(None)
    msg = await channel.send(embed=embed, view=gv_view)
    gv_view.message_id = msg.id
    await ctx.send(f"ההגרלה פורסמה בהצלחה בערוץ {channel.mention}!")
    
    await asyncio.sleep(duration * 60)
    
    import random
    if len(gv_view.entrants) < winners:
        await channel.send(f"ההגרלה על **{prize}** מבוטלת עקב חוסר משתתפים.")
    else:
        chosen_winners = random.sample(gv_view.entrants, winners)
        mentions = ", ".join([f"<@{w}>" for w in chosen_winners])
        await channel.send(f"🎉 מזל טוב לזוכים בהגרלה על **{prize}**: {mentions}! פנו לצוות לקבלת הפרס.")

# אזהרות (MODERATION)
@bot.command()
@commands.has_permissions(manage_messages=True)
async def warn(ctx, member: discord.Member, *, reason: str = "לא צוינה סיבה"):
    if member.id not in warnings_db:
        warnings_db[member.id] = []
    warnings_db[member.id].append(reason)
    
    embed = discord.Embed(title="⚠️ קיבלת אזהרה בשרת", description=f"שרת: Chicago City\nסיבה: {reason}", color=discord.Color.red())
    try: await member.send(embed=embed)
    except: pass
    
    await ctx.send(f"המשתמש {member.mention} הוזהר בהצלחה. (סה''כ אזהרות: {len(warnings_db[member.id])})")

@bot.command()
async def warns(ctx, member: discord.Member):
    count = len(warnings_db.get(member.id, []))
    await ctx.send(f"למשתמש {member.mention} יש כרגע `{count}` אזהרות בשרת.")

@bot.command()
@commands.has_permissions(manage_messages=True)
async def unwarn(ctx, member: discord.Member):
    if member.id in warnings_db and len(warnings_db[member.id]) > 0:
        warnings_db[member.id].pop()
        await ctx.send(f"האזהרה האחרונה של {member.mention} הוסרה בהצלחה.")
    else:
        await ctx.send("למשתמש זה אין אזהרות פעילות.")

# כריזה (ANNOUNCEMENTS)
@bot.command()
@commands.has_permissions(administrator=True)
async def say(ctx, channel: discord.TextChannel, embed_keyword: str, *, content: str):
    if embed_keyword.lower() == "embed":
        embed = discord.Embed(description=content, color=discord.Color.blue(), timestamp=datetime.datetime.utcnow())
        embed.set_footer(text="הנהלת Chicago City")
        await channel.send(embed=embed)
        await ctx.send(f"ההכרזה נשלחה בהצלחה בערוץ {channel.mention}!")
    else:
        full_text = f"{embed_keyword} {content}"
        embed = discord.Embed(description=full_text, color=discord.Color.blue(), timestamp=datetime.datetime.utcnow())
        embed.set_footer(text="הנהלת Chicago City")
        await channel.send(embed=embed)
        await ctx.send(f"ההכרזה נשלחה בהצלחה בערוץ {channel.mention}!")

# לוגים (AUDIT LOGS)
async def send_log(event_name, embed):
    ch_id = LOG_CHANNELS.get(event_name)
    if ch_id:
        channel = bot.get_channel(ch_id)
        if channel: await channel.send(embed=embed)

@bot.event
async def on_guild_channel_create(channel):
    embed = discord.Embed(title="🟢 ערוץ חדש נוצר", description=f"שם הערוץ: {channel.name}\nסוג: {channel.type}\nקטגוריה: {channel.category}", color=discord.Color.green())
    await send_log("channel_create", embed)

@bot.event
async def on_guild_channel_delete(channel):
    embed = discord.Embed(title="🔴 ערוץ נמחק", description=f"שם הערוץ שהוסר: {channel.name}\nסוג: {channel.type}", color=discord.Color.red())
    await send_log("channel_delete", embed)

@bot.event
async def on_guild_channel_update(before, after):
    if before.name != after.name:
        embed = discord.Embed(title="🔵 ערוץ עודכן", description=f"שם ישן: {before.name}\nשם חדש: {after.name}", color=discord.Color.blue())
        await send_log("channel_update", embed)

@bot.event
async def on_member_ban(guild, user):
    embed = discord.Embed(title="🔨 שחקן הורחק מהשרת (BAN)", description=f"שם: {user.name}\nאיידי: {user.id}", color=discord.Color.dark_red())
    await send_log("ban", embed)

@bot.event
async def on_member_unban(guild, user):
    embed = discord.Embed(title="🔓 הרחקה בוטלה (UNBAN)", description=f"שם: {user.name}\nאיידי: {user.id}", color=discord.Color.light_grey())
    await send_log("unban", embed)

@bot.event
async def on_guild_role_create(role):
    embed = discord.Embed(title="✨ רול חדש נוצר", description=f"שם הרול: {role.name}\nאיידי: {role.id}", color=discord.Color.teal())
    await send_log("role_create", embed)

@bot.event
async def on_guild_role_delete(role):
    embed = discord.Embed(title="🔥 רול נמחק", description=f"שם הרול שהוסר: {role.name}", color=discord.Color.orange())
    await send_log("role_delete", embed)

@bot.event
async def on_message_edit(before, after):
    if before.author.bot or before.content == after.content: return
    embed = discord.Embed(title="📝 הודעה נערכה", description=f"**כותב:** {before.author.mention}\n**חדר:** {before.channel.mention}\n\n**תוכן ישן:**\n{before.content}\n\n**תוכן חדש:**\n{after.content}", color=discord.Color.gold())
    await send_log("message_edit", embed)

@bot.event
async def on_message_delete(message):
    if message.author.bot: return
    embed = discord.Embed(title="🗑️ הודעה נמחקה", description=f"**כותב ההודעה:** {message.author.mention}\n**ערוץ:** {message.channel.mention}\n\n**תוכן ההודעה:**\n{message.content}", color=discord.Color.red())
    await send_log("message_delete", embed)

@bot.event
async def on_member_join(member):
    embed = discord.Embed(title="📥 משתמש חדש נכנס", description=f"משתמש: {member.mention}\nשם משתמש: {member.name}\nאיידי: {member.id}", color=discord.Color.green())
    await send_log("member_join", embed)
    
    welcome_channel = bot.get_channel(LOG_CHANNELS["welcome_embed"])
    if welcome_channel:
        # עיצוב הוולקם המבוקש!
        w_embed = discord.Embed(
            title=f"🎉 ברוך הבא ל-Chicago City, {member.name}! 🎉",
            description=f"שמחים שהצטרפת אלינו! כנס לערוץ האימות כדי לקבל גישה מלאה לשרת: <#{ROLE_VERIFIED}> 🛡️",
            color=discord.Color.red(),
            timestamp=datetime.datetime.utcnow()
        )
        # תמונת הפרופיל של מי שנכנס בצד ימין למעלה (Thumbnail)
        w_embed.set_thumbnail(url=member.display_avatar.url)
        # תמונת הלוגו הגדולה שביקשת למטה!
        w_embed.set_image(url="https://discordapp.net")
        w_embed.set_footer(text="Chicago City System Welcome")
        await welcome_channel.send(embed=w_embed)

    # מערכת אינוויט טראקר מעוצבת ומשודרגת פה!
    invites_before = invites_cache.get(member.guild.id, {})
    try:
        invites_after = await member.guild.invites()
        invites_cache[member.guild.id] = {invite.code: invite.uses for invite in invites_after}
        inviter_text = "לא נמצא (או קישור קבוע)"
        code_text = "אין קוד"
        uses_text = "0"
        
        for invite in invites_after:
            if invite.code in invites_before and invite.uses > invites_before[invite.code]:
                inviter_text = f"{invite.inviter.mention}"
                code_text = f"`{invite.code}`"
                uses_text = f"`{invite.uses}`"
                break
    except:
        inviter_text = "חוסר הרשאות לעקוב"
        code_text = "שגיאה"
        uses_text = "שגיאה"
            
    inv_embed = discord.Embed(
        title="🔗 לוג הזמנות חדש — Invite Tracker", 
        description=f"המשתמש {member.mention} נכנס לשרת הרשמי של Chicago City! 🎉", 
        color=discord.Color.magenta(),
        timestamp=datetime.datetime.utcnow()
    )
    inv_embed.add_field(name="👤 הוזמן על ידי:", value=inviter_text, inline=True)
    inv_embed.add_field(name="🔑 קוד הזמנה:", value=code_text, inline=True)
    inv_embed.add_field(name="📊 סך הכל שימושים בקוד:", value=uses_text, inline=True)
    inv_embed.set_footer(text="Chicago City System Tracking")
    
    await send_log("invite_tracker", inv_embed)

@bot.event
async def on_member_remove(member):
    embed = discord.Embed(title="📤 משתמש עזב את השרת", description=f"משתמש: {member.mention}\nשם: {member.name}", color=discord.Color.light_grey())
    await send_log("member_leave", embed)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user.name}")
    print("Serving Chicago City Server")
    for guild in bot.guilds:
        try:
            invites = await guild.invites()
            invites_cache[guild.id] = {invite.code: invite.uses for invite in invites}
        except: pass
    print("Invite cache seeded for Chicago City")

keep_alive()

bot.run(os.environ['DISCORD_TOKEN'])
