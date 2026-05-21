# --- מערכת הגרלות צבעונית מבוססת פאנל וטפסים (GIVEAWAY MODAL SYSTEM) ---
class GiveawayModal(Modal):
    def __init__(self):
        super().__init__(title="🎉 יצירת הגרלה חדשה - Chicago City")
        self.prize = TextInput(label="🎁 מה הפרס המטורף של ההגרלה?", placeholder="לדוגמה: רכב ספורט יוקרתי / 1,000,000$", required=True)
        self.time = TextInput(label="⏱️ זמן ריצה כולל (בדקות)", placeholder="לדוגמה: 15", required=True)
        self.winners = TextInput(label="👥 כמות זוכים מאושרים", placeholder="לדוגמה: 1", required=True)
        self.add_item(self.prize)
        self.add_item(self.time)
        self.add_item(self.winners)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        try:
            duration = int(self.time.value)
            winners_count = int(self.winners.value)
        except ValueError:
            return await interaction.followup.send("❌ שגיאה: נא להזין מספרים תקינים בשדות הזמן והזוכים!", ephemeral=True)

        public_ch = bot.get_channel(CHANNEL_GIVEAWAY_PUBLIC)
        if not public_ch: return await interaction.followup.send("❌ שגיאה: ערוץ ההגרלות הציבורי לא נמצא.", ephemeral=True)

        embed = discord.Embed(title="🎁 הגרלה מטורפת יצאה לדרך! ➔ CHICAGO CITY 🎉", color=discord.Color.gold())
        embed.description = f"🔥 **משתמשים יקרים, יש לכם הזדמנות לזכות בפרס מטורף!** 🔥\n\n" \
                            f"✨ **הפרס המנצח:** `{self.prize.value}`\n" \
                            f"👥 **כמות זוכים:** `{winners_count}`\n" \
                            f"⏱️ **זמן נותר לחגיגה:** `{duration}` דקות\n\n" \
                            f"🎉 **לחצו על הכפתור הירוק למטה כדי להיכנס להגרלה ולהבטיח את מקומכם!** 👇🏆"
        embed.set_footer(text="Chicago City • Luck & Giveaways")
        if interaction.guild.icon: embed.set_thumbnail(url=interaction.guild.icon.url)

        view = AdvancedGiveawayView(self.prize.value, winners_count)
        msg = await public_ch.send(embed=embed, view=view)
        await interaction.followup.send(f"✅ ההגרלה נוצרה ופורסמה בהצלחה בערוץ {public_ch.mention}!", ephemeral=True)

        await asyncio.sleep(duration * 60)
        if view.active:
            view.active = False
            await end_gv(public_ch, self.prize.value, winners_count, view.entrants, msg)

class GiveawayPanelView(View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="🎁 פתח הגרלה חדשה לשחקנים", style=discord.ButtonStyle.green, custom_id="gv_panel_btn")
    async def create_gv(self, interaction: discord.Interaction, button: Button):
        if interaction.guild.get_role(ROLE_STAFF) not in interaction.user.roles and not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message("❌ אין לך הרשאה לפתוח פאנל זה!", ephemeral=True)
        await interaction.response.send_modal(GiveawayModal())

class AdvancedGiveawayView(View):
    def __init__(self, prize, winners):
        super().__init__(timeout=None)
        self.prize, self.winners, self.entrants, self.active = prize, winners, [], True
    @discord.ui.button(label="🎉 הצטרף להגרלה!", style=discord.ButtonStyle.green, custom_id="gv_join")
    async def join(self, interaction: discord.Interaction, b: Button):
        await interaction.response.defer(ephemeral=True)
        if not self.active: return await interaction.followup.send("❌ ההגרלה כבר הגיעה לסיומה!", ephemeral=True)
        if interaction.user.id in self.entrants: return await interaction.followup.send("אתה כבר רשום במערכת ההגרלה הזו! 🍀", ephemeral=True)
        self.entrants.append(interaction.user.id)
        await interaction.followup.send("✅ נרשמת בהצלחה! המערכת נעלה את השם שלך בתיבת המזל.🍀", ephemeral=True)

    @discord.ui.button(label="📈 כמות רשומים", style=discord.ButtonStyle.grey, custom_id="gv_status")
    async def status(self, interaction: discord.Interaction, b: Button):
        await interaction.response.defer(ephemeral=True)
        await interaction.followup.send(f"📊 יש כרגע `{len(self.entrants)}` משתתפים רשומים בהגרלה זו.", ephemeral=True)

    @discord.ui.button(label="⏱️ סגור הגרלה כעת", style=discord.ButtonStyle.red, custom_id="gv_end_now")
    async def end_early(self, interaction: discord.Interaction, b: Button):
        await interaction.response.defer()
        if interaction.guild.get_role(ROLE_STAFF) not in interaction.user.roles: return
        self.active = False; await end_gv(interaction.channel, self.prize, self.winners, self.entrants, interaction.message)

async def end_gv(channel, prize, winners, entrants, msg):
    if len(entrants) < winners: await msg.edit(embed=discord.Embed(title="🌈 CHICAGO CITY ➔ GIVEAWAY", description="❌ ההגרלה בוטלה באופן אוטומטי עקב חוסר משתתפים בשרת.", color=discord.Color.red()), view=None)
    else:
        w = random.sample(entrants, winners); m = ", ".join([f"<@{x}>" for x in w])
        await msg.edit(embed=discord.Embed(title="🏆 ההגרלה הסתיימה רשמית! 🎉", description=f"✨ **הפרס המטורף שחולק:** `{prize}`\n\n👥 **הזוכים המאושרים שגרפו את הפרס:**\n{m}\n\n👑 ברכות לזוכים! פנו לצוות לקבלת הפרס.", color=discord.Color.green()), view=None)
        await channel.send(f"🎉 💎 **מזל טוב ענקי לזוכים המאושרים בהגרלה על {prize}!** {m}")

@bot.command()
@commands.has_permissions(administrator=True)
async def setup_giveaway_panel(ctx):
    embed = discord.Embed(title="🎁 מרכז ניהול ההגרלות הרשמי של הצוות 🎉", description="שלום חברי צוות יקרים! ✨\nמערכת זו מיועדת ליצירת הגרלות מעוצבות וצבעוניות בצורה קלה.\n\n**לחצו על הכפתור הירוק למטה כדי לפתוח את טופס יצירת ההגרלה המהיר!** 👇💎", color=discord.Color.green())
    embed.set_footer(text="Chicago City Staff Console • Color Edition")
    await ctx.send(embed=embed, view=GiveawayPanelView())

# --- פאנל אזהרות צבעוני מבוסס בחירת תיוג @ ישירה (WARN PANEL USER SELECT) ---
class StaffSelectReasonModal(Modal):
    def __init__(self, target_member):
        super().__init__(title="🚨 הזנת סיבת אזהרה - משמעת")
        self.target = target_member
        self.reason = TextInput(label="רשום כאן את סיבת האזהרה המלאה", placeholder="לדוגמה: חוסר כבוד חמור לדרג ניהול / אביוז דרגות", required=True)
        self.add_item(self.reason)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        tid = self.target.id
        if tid not in staff_warns_db: staff_warns_db[tid] = []
        t = datetime.datetime.now().strftime("%d/%m/%Y | %H:%M")
        staff_warns_db[tid].append({"reason": self.reason.value, "by": interaction.user.id, "date": t})
        count = len(staff_warns_db[tid])

        log_ch = bot.get_channel(CHANNEL_STAFF_WARNS_LOG)
        if log_ch:
            embed = discord.Embed(title="🚨 רישום משמעת חמור בצוות! ➔ CHICAGO CITY 💥", color=discord.Color.red())
            embed.description = f"💥 **אזהרה רשמית נרשמה בתיק האישי של חבר צוות!** 💥\n\n" \
                                f"👤 **חבר הצוות שנענש:** {self.target.mention}\n" \
                                f"🛡️ **האדמין המעניש מההנהלה:** {interaction.user.mention}\n" \
                                f"📅 **מועד ומילוי האירוע:** `{t}`\n\n" \
                                f"📝 **סיבת האזהרה בתיק:**\n```fix\n{self.reason.value}```\n" \
                                f"📊 **מצב תיק אזהרות עדכני:** `{'🟥' * count + '⬛' * (3 - count)}` ({count}/3 אזהרות)"
            embed.set_thumbnail(url=self.target.display_avatar.url)
            embed.set_footer(text="Chicago City Security Database System")
            await log_ch.send(embed=embed)
        await interaction.followup.send(f"✅ האזהרה נרשמה בהצלחה רבה ל-{self.target.mention} והלוג שודר לערוץ!", ephemeral=True)

class WarnUserSelect(UserSelect):
    def __init__(self, action_type):
        super().__init__(placeholder="אנא לחצו ובחרו חבר צוות מהרשימה... 👤✨", min_values=1, max_values=1)
        self.action_type = action_type

    async def callback(self, interaction: discord.Interaction):
        target = self.values[0]
        if self.action_type == "add":
            await interaction.response.send_modal(StaffSelectReasonModal(target))
        elif self.action_type == "view":
            c = len(staff_warns_db.get(target.id, []))
            if c == 0: return await interaction.response.send_message(f"🟢 ✨ **חבר הצוות המלך** {target.mention} **נקי לחלוטין ללא שום אזהרות בתיק האישי! כל הכבוד!** 🎉", ephemeral=True)
            embed = discord.Embed(title=f"📊 גיליון אזהרות צוות רשמי ➔ {target.name} 🚨", color=discord.Color.orange())
            for i, w in enumerate(staff_warns_db[target.id], 1):
                embed.add_field(name=f"🚨 אזהרה מספר {i} ➔ בתאריך {w['date']}", value=f"🔹 **רשם והעניש:** <@{w['by']}>\n🔹 **הסיבה הרשומה:** {w['reason']}", inline=False)
            embed.set_footer(text="Chicago City Internal Records")
            await interaction.response.send_message(embed=embed, ephemeral=True)
        elif self.action_type == "remove":
            if target.id in staff_warns_db and len(staff_warns_db[target.id]) > 0:
                staff_warns_db[target.id].pop()
                await interaction.response.send_message(f"✅ **האזהרה האחרונה של חבר הצוות** {target.mention} **נמחקה ונמחקה מהתיק בהצלחה! התיק נוקה.** 🔓", ephemeral=True)
            else: await interaction.response.send_message(f"❌ שגיאה: ל-{target.mention} אין שום אזהרות פעילות שניתן למחוק.", ephemeral=True)

class WarnPanelView(View):
    def __init__(self): super().__init__(timeout=None)
    
    @discord.ui.button(label="⚠️ רשום אזהרה למנהל", style=discord.ButtonStyle.red, custom_id="wp_add")
    async def add_warn_btn(self, interaction: discord.Interaction, button: Button):
        if interaction.guild.get_role(ROLE_WARN_ADMIN) not in interaction.user.roles and not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message("❌ אבטחה: פעולה זו חסומה ומיועדת לדרג ניהול עליון בלבד!", ephemeral=True)
        view = View().add_item(WarnUserSelect("add"))
        await interaction.response.send_message("⚙️ **אנא בחרו מתוך רשימת חברי הצוות מטה את המנהל שברצונכם להזהיר:**", view=view, ephemeral=True)

    @discord.ui.button(label="📊 כמות ווארנים בתיק", style=discord.ButtonStyle.grey, custom_id="wp_view")
    async def view_warn_btn(self, interaction: discord.Interaction, button: Button):
        if interaction.guild.get_role(ROLE_WARN_ADMIN) not in interaction.user.roles and not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message("❌ אבטחה: פעולה זו חסומה ומיועדת לדרג ניהול עליון בלבד!", ephemeral=True)
        view = View().add_item(WarnUserSelect("view"))
        await interaction.response.send_message("⚙️ **בחרו חבר צוות מהרשימה למטה כדי לבדוק את כמות האזהרות שלו:**", view=view, ephemeral=True)

    @discord.ui.button(label="🔓 מחק אזהרה (Unwarn)", style=discord.ButtonStyle.green, custom_id="wp_remove")
    async def remove_warn_btn(self, interaction: discord.Interaction, button: Button):
        if interaction.guild.get_role(ROLE_WARN_ADMIN) not in interaction.user.roles and not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message("❌ אבטחה: פעולה זו חסומה ומיועדת לדרג ניהול עליון בלבד!", ephemeral=True)
        view = View().add_item(WarnUserSelect("remove"))
        await interaction.response.send_message("⚙️ **בחרו חבר צוות מהרשימה מטה כדי למחוק לו את האזהרה האחרונה מהתיק:**", view=view, ephemeral=True)

@bot.command()
@commands.has_permissions(administrator=True)
async def setup_warn_panel(ctx):
    embed = discord.Embed(title="⚠️ פאנל פיקוח ומשמעת הצוות ➔ CHICAGO CITY 🛑", description="מרכז שליטה ואבטחה חסוי לניהול, בדיקה ורישום משמעת בצוות השרת.\n\n**רק דרג ניהול עליון מורשה ללחוץ על הכפתורים ולבצע שינויים או מחיקות!** 🛡️✨", color=discord.Color.red())
    embed.set_footer(text="Chicago City Management Dashboard Only")
    await ctx.send(embed=embed, view=WarnPanelView())

# --- מערכת הצעות צבעונית ומטורפת (SUGGESTIONS SYSTEM) ---
CHANNEL_SUGG_PANEL = 1507020507776811068
CHANNEL_SUGG_LOGS = 1483039217482334253

class SuggestionModal(Modal):
    def __init__(self):
        super().__init__(title="💡 הגשת הצעה מטורפת חדשה לעיר")
        self.sugg = TextInput(label="רשום ופרט כאן את ההצעה המטורפת שלך", style=discord.TextStyle.paragraph, placeholder="רשום כאן את רעיונך בצורה הכי ברורה ומפורטת שיש...", required=True)
        self.add_item(self.sugg)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        log_ch = bot.get_channel(CHANNEL_SUGG_LOGS)
        if not log_ch: return await interaction.followup.send("❌ ערוץ הלוגים של ההצעות לא נמצא.", ephemeral=True)
        
        embed = discord.Embed(title="💡 הצעה חדשה ומטורפת עלתה לאוויר! 🔥", color=discord.Color.blue())
        embed.description = f"👑 **תושבי Chicago City היקרים, הצעה חדשה ומטורפת עלתה לשיפוטכם!** 👑\n\n```fix\n{self.sugg.value}```\n" \
                            f"🔹 **הוגש בגאווה על ידי האזרח:** {interaction.user.mention}\n\n" \
                            f"**הצביעו עכשיו באמצעות האימוג'ים למטה והשפיעו על עתיד העיר!** 👇✨"
        embed.set_footer(text="Chicago City • Community Feedback System")
        if interaction.guild.icon: embed.set_thumbnail(url=interaction.guild.icon.url)
        
        msg = await log_ch.send(embed=embed)
        await msg.add_reaction("👍")
        await msg.add_reaction("👎")
        await interaction.followup.send("✅ ההצעה שלך נשלחה בהצלחה רבה לערוץ ההצעות המרכזי ונוספו לה תגובות הצבעה! תודה 🎉💎", ephemeral=True)

class SuggestionPanelView(View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="💡 לחצו כאן והגישו הצעה חדשה לעיר!", style=discord.ButtonStyle.blurple, custom_id="sugg_panel_btn")
    async def add_sugg(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_modal(SuggestionModal())

@bot.command()
@commands.has_permissions(administrator=True)
async def setup_suggestions(ctx):
    embed = discord.Embed(title="💡 תיבת הרעיונות וההצעות של CHICAGO CITY 💎", description="יש לכם רעיון משוגע ומטורף לשדרוג חווית המשחק בעיר, הצעה לרכב ספורט חדש או מערכת שווה שחובה להוסיף? 🚀✨\n\n**לחצו על הכפתור הכחול הנוצץ למטה, מלאו את הטופס שיפתח ויאללה - ההצעה שלכם עולה ישירות לקהילה!** 👇🎉", color=discord.Color.blue())
    embed.set_footer(text="Chicago City • Power of Community")
    if ctx.guild.icon: embed.set_image(url=ctx.guild.icon.url)
    await ctx.send(embed=embed, view=SuggestionPanelView())

# פקודת say
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

# --- מנוע ה-INVITE TRACKER הצבעוני והמשוגע ברמת פרטיזן עילית (PREMIUM AVATAR TRACKER) ---
async def fetch_invites(guild):
    try: return {invite.code: invite for invite in await guild.invites()}
    except: return {}

@bot.event
async def on_guild_join(guild):
    invites_cache[guild.id] = await fetch_invites(guild)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user.name}")
    for guild in bot.guilds: invites_cache[guild.id] = await fetch_invites(guild)
    if not update_fivem_status.is_running(): update_fivem_status.start()

@bot.event
async def on_member_join(member):
    w_ch = bot.get_channel(LOG_CHANNELS["welcome_embed"])
    if w_ch:
        embed = discord.Embed(title="🌈 ברוך הבא לשרת הרשמי ➔ CHICAGO CITY 🎉", description=f"💎 **תושב חדש ומלך הצטרף לעיר, איזה כיף!** 💎\n\n👤 **שלום לך:** {member.mention}\n🛡️ **אנא כנס לערוץ האבטחה והשלם את תהליך האימות המהיר:** <#{ROLE_VERIFIED}> ✨", color=discord.Color.red())
        embed.set_thumbnail(url=member.display_avatar.url); embed.set_footer(text="Chicago City Administration • Welcome System")
        if member.guild.icon: embed.set_image(url=member.guild.icon.url)
        await w_ch.send(embed=embed)

    log_ch = bot.get_channel(CHANNEL_INVITE_LOGS)
    if not log_ch: return
    
    old_invites = invites_cache.get(member.guild.id, {})
    new_invites = await fetch_invites(member.guild)
    invites_cache[member.guild.id] = new_invites
    
    inviter_str, code_str, total_str = "לא ידוע / קישור ישיר 🔗", "לא ידוע 🔒", "0"
    
    for code in old_invites:
        if code in new_invites and old_invites[code].uses < new_invites[code].uses:
            inviter = old_invites[code].inviter
            inviter_str = inviter.mention
            code_str = f"`{code}`"
            total_uses = sum(inv.uses for inv in new_invites.values() if inv.inviter and inv.inviter.id == inviter.id)
            total_str = f"`{total_uses}`"
            break
            
    # עיצוב מטורף, עשיר בצבעים ואימוג'ים - עם האוואטר של השחקן בצד ימין!
    embed = discord.Embed(title="📥 אזרח חדש נקלט במערכת מעקב ההזמנות! 🎉💎", color=discord.Color.from_rgb(155, 89, 182))
    embed.description = f"✨ **ברוכים הבאים ל-Chicago City!** ✨\n\n" \
                        f"👤 **המשתמש שהצטרף לעיר:** {member.mention}\n" \
                        f"🆔 **מזהה הדיסקורד שלו:** `{member.id}`\n" \
                        f"━━━━━━━━━━━━━━━━━━━━━━━\n" \
                        f"🤝 **הוזמן והובא ישירות ע''י:** {inviter_str}\n" \
                        f"📊 **סך כל ההזמנות המוצלחות שלו בשרת:** `{total_str} אזרחים מחוברים` 💎\n" \
                        f"🔑 **קוד ההזמנה הדיגיטלי שבו השתמש:** {code_str}"
    
    embed.set_footer(text="Chicago City Ultra-Premium Invite Logging System")
    # הצגת תמונת הפרופיל הדינמית והאישית של השחקן שנכנס בצד ימין (Thumbnail)!
    embed.set_thumbnail(url=member.display_avatar.url)
    await log_ch.send(embed=embed)

class FiveMConnectView(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(discord.ui.Button(label="🚀 התחברות ישירה ומהירה לעיר!", style=discord.ButtonStyle.link, url="https://cfx.re"))

# משימת הסטטוס המאוחדת והצבעונית כל 2 דקות
@tasks.loop(minutes=2)
async def update_fivem_status():
    global fivem_msg_id
    ch = bot.get_channel(CHANNEL_FIVEM_STATUS)
    if not ch: return
    
    guild = ch.guild
    total_dc_members = guild.member_count
    online_dc_users = sum(1 for m in guild.members if m.status != discord.Status.offline and not m.bot)
    staff_role = guild.get_role(ROLE_STAFF)
    staff_dc_online = sum(1 for m in staff_role.members if m.status != discord.Status.offline and not m.bot) if staff_role else 0

    status_str, players_str, staff_str, color = "🔴 מנותק (Offline)", "0 / 0", "0 מחוברים", discord.Color.red()
    
    headers = {"User-Agent": "Mozilla/5.0"}
    async with aiohttp.ClientSession(headers=headers) as session:
        try:
            async with session.get(f"https://fivem.net{CFX_ID}", timeout=5) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    server_data = data.get("Data", {})
                    status_str = "🟢 מקוון (Online)"
                    color = discord.Color.green()
                    players_list = server_data.get("players", [])
                    players_str = f"{len(players_list)} / {server_data.get('sv_maxclients', 64)}"
                    fivem_identifiers = []
                    for player in players_list:
                        for identifier in player.get('identifiers', []):
                            if identifier.startswith('discord:'):
                                fivem_identifiers.append(int(identifier.replace('discord:', '')))
                    staff_game_count = sum(1 for m in staff_role.members if m.id in fivem_identifiers) if staff_role else 0
                    staff_str = f"{staff_game_count} אנשי צוות בעיר"
        except: pass

    # עיצוב טבלת הסטטוסים המרוכזת ברמת יוקרה עשירה בצבעים!
    embed = discord.Embed(title="📊 רשת הניטור והסטטיסטיקות הרשמית ➔ CHICAGO CITY 💎", color=color, timestamp=datetime.datetime.utcnow())
    embed.add_field(name="🎮 FIVEM GAME SERVER METRICS", value=f"```ansi\n• סטטוס השרת באוויר: {status_str}\n• שחקנים מחוברים בעיר: {players_str}\n• אנשי צוות בתוך העיר: {staff_str}```", inline=False)
    embed.add_field(name="💬 DISCORD NETWORK METRICS", value=f"```ansi\n• סך הכל תושבים רשומים: {total_dc_members} אזרחים\n• אזרחים מחוברים כרגע: {online_dc_users} אונליין\n• אנשי צוות זמינים בדיסקורד: {staff_dc_online} מנהלים```", inline=False)
    embed.set_footer(text="Chicago City • Live Statistics Network Dashboard")
    if guild.icon: embed.set_thumbnail(url=guild.icon.url)

    try:
        if fivem_msg_id is None:
            async for m in ch.history(limit=5):
                if m.author == bot.user and m.embeds and m.embeds.title == "📊 רשת הניטור והסטטיסטיקות הרשמית ➔ CHICAGO CITY 💎":
                    fivem_msg_id = m.id; await m.edit(embed=embed, view=FiveMConnectView()); return
            msg = await ch.send(embed=embed, view=FiveMConnectView())
            fivem_msg_id = msg.id
        else:
            msg = await ch.fetch_message(fivem_msg_id)
            await msg.edit(embed=embed, view=FiveMConnectView())
    except: fivem_msg_id = None

keep_alive()
bot.run(os.environ['DISCORD_TOKEN'])
