import discord
from discord.ext import commands
import os
import json
import time
from dotenv import load_dotenv

# =========================
# CONFIG
# =========================
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

if not TOKEN:
    raise ValueError("DISCORD_TOKEN mancante")

BANNER = "https://cdn.discordapp.com/attachments/1482844068009738434/1511074300755574975/ChatGPT_Image_1_giu_2026_20_28_18.png"

STAFF_ROLE = "🎫 Support"
TICKET_CATEGORY = "🎫 TICKETS"
LOG_CHANNEL = "📋・logs"
WELCOME_CHANNEL = "👋・ᴡᴇʟᴄᴏᴍᴇ"
GOODBYE_CHANNEL = "💔・ɢᴏᴏᴅʙʏᴇ"
MEMBER_ROLE = "Membro"

WARN_FILE = "warns.json"

# =========================
# BOT
# =========================
intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

raid_mode = False
spam_cache = {}

# =========================
# UTILS
# =========================
async def log(guild, text):
    try:
        channel = discord.utils.get(guild.text_channels, name=LOG_CHANNEL)
        if channel:
            await channel.send(text)
    except:
        pass

def load_warns():
    if not os.path.exists(WARN_FILE):
        return {}
    with open(WARN_FILE, "r") as f:
        return json.load(f)

def save_warns(data):
    with open(WARN_FILE, "w") as f:
        json.dump(data, f, indent=4)

# =========================
# READY
# =========================
@bot.event
async def on_ready():
    print(f"🔴 UNITY ONLINE: {bot.user}")
    await bot.tree.sync()

# =========================
# WELCOME / GOODBYE (FIXED)
# =========================
@bot.event
async def on_member_join(member):
    global raid_mode

    try:
        if raid_mode:
            await member.kick(reason="ANTI RAID")
            return

        await log(member.guild, f"🟢 JOIN {member}")

        channel = discord.utils.get(member.guild.text_channels, name=WELCOME_CHANNEL)

        if channel:
            embed = discord.Embed(
                title="🔴 UNITY",
                description=f"Benvenuto {member.mention}",
                color=discord.Color.red()
            )
            embed.set_image(url=BANNER)
            await channel.send(embed=embed)

    except Exception as e:
        print("JOIN ERROR:", e)


@bot.event
async def on_member_remove(member):
    try:
        await log(member.guild, f"🔴 LEAVE {member}")

        channel = discord.utils.get(member.guild.text_channels, name=GOODBYE_CHANNEL)

        if channel:
            embed = discord.Embed(
                title="🔴 GOODBYE",
                description=f"{member} ha lasciato il server",
                color=discord.Color.red()
            )
            embed.set_image(url=BANNER)
            await channel.send(embed=embed)

    except Exception as e:
        print("LEAVE ERROR:", e)

# =========================
# VERIFY
# =========================
class VerifyView(discord.ui.View):
    @discord.ui.button(label="Verifica", emoji="🔐", style=discord.ButtonStyle.danger)
    async def verify(self, interaction: discord.Interaction, button: discord.ui.Button):

        role = discord.utils.get(interaction.guild.roles, name=MEMBER_ROLE)

        if not role:
            return await interaction.response.send_message("❌ ruolo mancante", ephemeral=True)

        if role in interaction.user.roles:
            return await interaction.response.send_message("⚠️ già verificato", ephemeral=True)

        await interaction.user.add_roles(role)
        await interaction.response.send_message("✔ verificato", ephemeral=True)

@bot.tree.command(name="verifypanel")
async def verifypanel(interaction: discord.Interaction):

    embed = discord.Embed(
        title="🔐 UNITY VERIFY",
        color=discord.Color.red()
    )
    embed.set_image(url=BANNER)

    await interaction.response.send_message(embed=embed, view=VerifyView())

# =========================
# ANNUNCI
# =========================
@bot.tree.command(name="annunci")
async def annunci(interaction: discord.Interaction, titolo: str, messaggio: str):

    if not interaction.user.guild_permissions.administrator:
        return await interaction.response.send_message("❌ no permessi", ephemeral=True)

    embed = discord.Embed(
        title=f"🔴 {titolo}",
        description=messaggio,
        color=discord.Color.red()
    )
    embed.set_image(url=BANNER)

    await interaction.channel.send(embed=embed)
    await interaction.response.send_message("✔ inviato", ephemeral=True)

# =========================
# MODERAZIONE
# =========================
@bot.tree.command(name="ban")
async def ban(interaction, member: discord.Member, reason: str = "no reason"):
    await member.ban(reason=reason)
    await interaction.response.send_message("🔨 bannato", ephemeral=True)

@bot.tree.command(name="kick")
async def kick(interaction, member: discord.Member, reason: str = "no reason"):
    await member.kick(reason=reason)
    await interaction.response.send_message("👢 kickato", ephemeral=True)

@bot.tree.command(name="clear")
async def clear(interaction, amount: int):
    await interaction.channel.purge(limit=amount)
    await interaction.response.send_message("🧹 pulito", ephemeral=True)

# =========================
# WARN SYSTEM
# =========================
@bot.tree.command(name="warn")
async def warn(interaction, member: discord.Member, reason: str):

    warns = load_warns()
    uid = str(member.id)

    warns.setdefault(uid, []).append(reason)
    save_warns(warns)

    await interaction.response.send_message("⚠️ warn dato", ephemeral=True)

@bot.tree.command(name="warns")
async def warns(interaction, member: discord.Member):

    warns = load_warns().get(str(member.id), [])
    await interaction.response.send_message("\n".join(warns) if warns else "nessun warn", ephemeral=True)

# =========================
# ANTI SPAM (SAFE)
# =========================
@bot.event
async def on_message(message):

    try:
        if message.author.bot:
            return

        uid = message.author.id
        now = time.time()

        spam_cache.setdefault(uid, []).append(now)
        spam_cache[uid] = [t for t in spam_cache[uid] if now - t < 5]

        if len(spam_cache[uid]) > 5:
            await message.channel.send(f"⚠️ spam {message.author.mention}")

        await bot.process_commands(message)

    except:
        pass

# =========================
# RAID TOGGLE
# =========================
@bot.tree.command(name="raid")
async def raid(interaction):
    global raid_mode
    raid_mode = not raid_mode
    await interaction.response.send_message(f"🚨 raid mode: {raid_mode}", ephemeral=True)

# =========================
# TICKET SYSTEM FIXED
# =========================
class TicketView(discord.ui.View):

    @discord.ui.button(label="Apri Ticket", emoji="🎫", style=discord.ButtonStyle.danger)
    async def open(self, interaction, button):

        guild = interaction.guild
        user = interaction.user

        category = discord.utils.get(guild.categories, name=TICKET_CATEGORY)
        if not category:
            category = await guild.create_category(TICKET_CATEGORY)

        channel = await guild.create_text_channel(
            name=f"ticket-{user.id}",
            category=category
        )

        await channel.set_permissions(guild.default_role, view_channel=False)
        await channel.set_permissions(user, view_channel=True, send_messages=True)

        staff = discord.utils.get(guild.roles, name=STAFF_ROLE)
        if staff:
            await channel.set_permissions(staff, view_channel=True, send_messages=True)

        embed = discord.Embed(
            title="🎫 UNITY TICKET",
            description=f"{user.mention}",
            color=discord.Color.red()
        )

        await channel.send(embed=embed, view=TicketControl())
        await interaction.response.send_message(f"✔ {channel.mention}", ephemeral=True)

class TicketControl(discord.ui.View):

    def __init__(self):
        super().__init__(timeout=None)
        self.claimed = None

    @discord.ui.button(label="Claim", emoji="👑", style=discord.ButtonStyle.success)
    async def claim(self, interaction, button):

        role = discord.utils.get(interaction.guild.roles, name=STAFF_ROLE)

        if role not in interaction.user.roles:
            return await interaction.response.send_message("❌ no staff", ephemeral=True)

        if self.claimed:
            return await interaction.response.send_message("❌ già claimato", ephemeral=True)

        self.claimed = interaction.user
        await interaction.channel.send(f"👑 claimato da {interaction.user.mention}")
        await interaction.response.send_message("✔ claim", ephemeral=True)

    @discord.ui.button(label="Chiudi", emoji="🔒", style=discord.ButtonStyle.danger)
    async def close(self, interaction, button):
        await interaction.channel.delete()

@bot.tree.command(name="ticketpanel")
async def ticketpanel(interaction):
    embed = discord.Embed(
        title="🎫 UNITY TICKETS",
        color=discord.Color.red()
    )
    embed.set_image(url=BANNER)

    await interaction.response.send_message(embed=embed, view=TicketView())

# =========================
# DASHBOARD
# =========================
class AdminView(discord.ui.View):

    @discord.ui.button(label="RAID ON/OFF", style=discord.ButtonStyle.danger)
    async def raid(self, interaction, button):
        global raid_mode
        raid_mode = not raid_mode
        await interaction.response.send_message(f"🚨 {raid_mode}", ephemeral=True)

@bot.tree.command(name="dashboard")
async def dashboard(interaction):

    if not interaction.user.guild_permissions.administrator:
        return await interaction.response.send_message("❌ no permessi", ephemeral=True)

    embed = discord.Embed(
        title="⚙️ UNITY DASHBOARD",
        color=discord.Color.red()
    )
    embed.set_image(url=BANNER)

    await interaction.response.send_message(embed=embed, view=AdminView(), ephemeral=True)

# =========================
# RUN (IMPORTANT FIX)
# =========================
bot.run(TOKEN)import discord
from discord.ext import commands
import os
import json
import time
from dotenv import load_dotenv

# =========================
# CONFIG
# =========================
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

if not TOKEN:
    raise ValueError("DISCORD_TOKEN mancante")

BANNER = "https://cdn.discordapp.com/attachments/1482844068009738434/1511074300755574975/ChatGPT_Image_1_giu_2026_20_28_18.png"

WELCOME_CHANNEL_ID = 1510308783581171952
GOODBYE_CHANNEL_ID = 1510313831694340096

STAFF_ROLE = "🎫 Support"
TICKET_CATEGORY = "🎫 TICKETS"
LOG_CHANNEL = "📋・logs"
WARN_FILE = "warns.json"

# =========================
# INTENTS (OBBLIGATORI)
# =========================
intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

raid_mode = False
spam_cache = {}

# =========================
# SAFE WARN SYSTEM
# =========================
def load_warns():
    try:
        if not os.path.exists(WARN_FILE):
            return {}
        with open(WARN_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def save_warns(data):
    try:
        with open(WARN_FILE, "w") as f:
            json.dump(data, f, indent=4)
    except:
        pass

# =========================
# SAFE LOG
# =========================
async def log(guild, text):
    try:
        channel = discord.utils.get(guild.text_channels, name=LOG_CHANNEL)
        if channel:
            await channel.send(text)
    except:
        pass

# =========================
# READY (SAFE SYNC)
# =========================
@bot.event
async def on_ready():
    print(f"🔴 UNITY ONLINE: {bot.user}")

    try:
        await bot.tree.sync()
    except Exception as e:
        print("SYNC ERROR:", e)

# =========================
# WELCOME / GOODBYE (CRASH PROOF)
# =========================
@bot.event
async def on_member_join(member):
    global raid_mode

    try:
        if raid_mode:
            await member.kick(reason="ANTI RAID")
            return

        await log(member.guild, f"🟢 JOIN {member}")

        channel = member.guild.get_channel(WELCOME_CHANNEL_ID)

        if channel:
            embed = discord.Embed(
                title="🔴 UNITY",
                description=f"Benvenuto {member.mention}",
                color=discord.Color.red()
            )
            embed.set_image(url=BANNER)
            await channel.send(embed=embed)

    except Exception as e:
        print("WELCOME ERROR:", e)


@bot.event
async def on_member_remove(member):
    try:
        await log(member.guild, f"🔴 LEAVE {member}")

        channel = member.guild.get_channel(GOODBYE_CHANNEL_ID)

        if channel:
            embed = discord.Embed(
                title="🔴 UNITY",
                description=f"{member} ha lasciato il server",
                color=discord.Color.red()
            )
            embed.set_image(url=BANNER)
            await channel.send(embed=embed)

    except Exception as e:
        print("GOODBYE ERROR:", e)

# =========================
# VERIFY
# =========================
class VerifyView(discord.ui.View):

    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Verifica", emoji="🔐", style=discord.ButtonStyle.danger)
    async def verify(self, interaction: discord.Interaction, button: discord.ui.Button):

        role = discord.utils.get(interaction.guild.roles, name="Membro")

        if not role:
            return await interaction.response.send_message("❌ ruolo mancante", ephemeral=True)

        try:
            await interaction.user.add_roles(role)
            await interaction.response.send_message("✔ verificato", ephemeral=True)
        except:
            await interaction.response.send_message("❌ errore ruolo", ephemeral=True)

@bot.tree.command(name="verifypanel")
async def verifypanel(interaction: discord.Interaction):

    embed = discord.Embed(
        title="🔐 UNITY VERIFY",
        color=discord.Color.red()
    )
    embed.set_image(url=BANNER)

    await interaction.response.send_message(embed=embed, view=VerifyView())

# =========================
# ANNUNCI
# =========================
@bot.tree.command(name="annunci")
async def annunci(interaction: discord.Interaction, titolo: str, messaggio: str):

    if not interaction.user.guild_permissions.administrator:
        return await interaction.response.send_message("❌ no permessi", ephemeral=True)

    embed = discord.Embed(
        title=f"🔴 {titolo}",
        description=messaggio,
        color=discord.Color.red()
    )
    embed.set_image(url=BANNER)

    await interaction.channel.send(embed=embed)
    await interaction.response.send_message("✔ inviato", ephemeral=True)

# =========================
# MODERAZIONE SAFE
# =========================
@bot.tree.command(name="ban")
async def ban(interaction: discord.Interaction, member: discord.Member, reason: str = "no reason"):
    try:
        await member.ban(reason=reason)
        await interaction.response.send_message("🔨 bannato", ephemeral=True)
    except:
        await interaction.response.send_message("❌ errore ban", ephemeral=True)

@bot.tree.command(name="kick")
async def kick(interaction: discord.Interaction, member: discord.Member, reason: str = "no reason"):
    try:
        await member.kick(reason=reason)
        await interaction.response.send_message("👢 kickato", ephemeral=True)
    except:
        await interaction.response.send_message("❌ errore kick", ephemeral=True)

@bot.tree.command(name="clear")
async def clear(interaction: discord.Interaction, amount: int):
    try:
        await interaction.channel.purge(limit=amount)
        await interaction.response.send_message("🧹 pulito", ephemeral=True)
    except:
        await interaction.response.send_message("❌ errore clear", ephemeral=True)

# =========================
# WARN SYSTEM
# =========================
@bot.tree.command(name="warn")
async def warn(interaction: discord.Interaction, member: discord.Member, reason: str):

    warns = load_warns()
    uid = str(member.id)

    warns.setdefault(uid, []).append(reason)
    save_warns(warns)

    await interaction.response.send_message("⚠️ warn dato", ephemeral=True)

@bot.tree.command(name="warns")
async def warns(interaction: discord.Interaction, member: discord.Member):

    warns = load_warns().get(str(member.id), [])
    await interaction.response.send_message("\n".join(warns) if warns else "nessun warn", ephemeral=True)

# =========================
# ANTI SPAM (SAFE)
# =========================
@bot.event
async def on_message(message):

    try:
        if message.author.bot:
            return

        now = time.time()
        uid = message.author.id

        spam_cache.setdefault(uid, []).append(now)
        spam_cache[uid] = [t for t in spam_cache[uid] if now - t < 5]

        if len(spam_cache[uid]) > 5:
            await message.channel.send(f"⚠️ spam {message.author.mention}")

        await bot.process_commands(message)

    except:
        pass

# =========================
# RAID TOGGLE
# =========================
@bot.tree.command(name="raid")
async def raid(interaction: discord.Interaction):

    global raid_mode
    raid_mode = not raid_mode

    await interaction.response.send_message(f"🚨 raid: {raid_mode}", ephemeral=True)

# =========================
# DASHBOARD
# =========================
class AdminView(discord.ui.View):

    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="RAID ON/OFF", style=discord.ButtonStyle.danger)
    async def raid(self, interaction: discord.Interaction, button: discord.ui.Button):

        global raid_mode
        raid_mode = not raid_mode

        await interaction.response.send_message(f"🚨 {raid_mode}", ephemeral=True)

@bot.tree.command(name="dashboard")
async def dashboard(interaction: discord.Interaction):

    if not interaction.user.guild_permissions.administrator:
        return await interaction.response.send_message("❌ no permessi", ephemeral=True)

    embed = discord.Embed(
        title="⚙️ UNITY DASHBOARD",
        color=discord.Color.red()
    )
    embed.set_image(url=BANNER)

    await interaction.response.send_message(embed=embed, view=AdminView(), ephemeral=True)

# =========================
# RUN
# =========================
bot.run(TOKEN)import discord
from discord.ext import commands
import os
import json
import time
from dotenv import load_dotenv

# =========================
# CONFIG
# =========================
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

if not TOKEN:
    raise ValueError("DISCORD_TOKEN mancante")

BANNER = "https://cdn.discordapp.com/attachments/1482844068009738434/1511074300755574975/ChatGPT_Image_1_giu_2026_20_28_18.png"

WELCOME_CHANNEL_ID = 1510308783581171952
GOODBYE_CHANNEL_ID = 1510313831694340096

STAFF_ROLE = "🎫 Support"
TICKET_CATEGORY = "🎫 TICKETS"
LOG_CHANNEL = "📋・logs"

WARN_FILE = "warns.json"

# =========================
# BOT
# =========================
intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

raid_mode = False
spam_cache = {}

# =========================
# WARN SYSTEM
# =========================
def load_warns():
    if not os.path.exists(WARN_FILE):
        return {}
    with open(WARN_FILE, "r") as f:
        return json.load(f)

def save_warns(data):
    with open(WARN_FILE, "w") as f:
        json.dump(data, f, indent=4)

# =========================
# LOG
# =========================
async def log(guild, text):
    try:
        channel = discord.utils.get(guild.text_channels, name=LOG_CHANNEL)
        if channel:
            await channel.send(text)
    except:
        pass

# =========================
# READY
# =========================
@bot.event
async def on_ready():
    print(f"🔴 UNITY ONLINE: {bot.user}")
    await bot.tree.sync()

# =========================
# WELCOME / GOODBYE
# =========================
@bot.event
async def on_member_join(member):
    global raid_mode

    if raid_mode:
        try:
            await member.kick(reason="ANTI RAID")
        except:
            pass
        return

    await log(member.guild, f"🟢 JOIN {member}")

    try:
        channel = member.guild.get_channel(WELCOME_CHANNEL_ID)

        if channel:
            embed = discord.Embed(
                title="🔴 UNITY",
                description=f"Benvenuto {member.mention}",
                color=discord.Color.red()
            )
            embed.set_image(url=BANNER)

            await channel.send(embed=embed)

    except Exception as e:
        print("WELCOME ERROR:", e)


@bot.event
async def on_member_remove(member):

    await log(member.guild, f"🔴 LEAVE {member}")

    try:
        channel = member.guild.get_channel(GOODBYE_CHANNEL_ID)

        if channel:
            embed = discord.Embed(
                title="🔴 UNITY",
                description=f"{member} ha lasciato il server",
                color=discord.Color.red()
            )
            embed.set_image(url=BANNER)

            await channel.send(embed=embed)

    except Exception as e:
        print("GOODBYE ERROR:", e)

# =========================
# VERIFY
# =========================
class VerifyView(discord.ui.View):

    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Verifica", emoji="🔐", style=discord.ButtonStyle.danger)
    async def verify(self, interaction: discord.Interaction, button: discord.ui.Button):

        role = discord.utils.get(interaction.guild.roles, name="Membro")

        if not role:
            return await interaction.response.send_message("❌ ruolo mancante", ephemeral=True)

        await interaction.user.add_roles(role)
        await interaction.response.send_message("✔ verificato", ephemeral=True)

@bot.tree.command(name="verifypanel")
async def verifypanel(interaction: discord.Interaction):

    embed = discord.Embed(
        title="🔐 UNITY VERIFY",
        color=discord.Color.red()
    )
    embed.set_image(url=BANNER)

    await interaction.response.send_message(embed=embed, view=VerifyView())

# =========================
# ANNUNCI
# =========================
@bot.tree.command(name="annunci")
async def annunci(interaction: discord.Interaction, titolo: str, messaggio: str):

    if not interaction.user.guild_permissions.administrator:
        return await interaction.response.send_message("❌ no permessi", ephemeral=True)

    embed = discord.Embed(
        title=f"🔴 {titolo}",
        description=messaggio,
        color=discord.Color.red()
    )
    embed.set_image(url=BANNER)

    await interaction.channel.send(embed=embed)
    await interaction.response.send_message("✔ inviato", ephemeral=True)

# =========================
# MODERAZIONE
# =========================
@bot.tree.command(name="ban")
async def ban(interaction: discord.Interaction, member: discord.Member, reason: str = "no reason"):
    await member.ban(reason=reason)
    await interaction.response.send_message("🔨 bannato", ephemeral=True)

@bot.tree.command(name="kick")
async def kick(interaction: discord.Interaction, member: discord.Member, reason: str = "no reason"):
    await member.kick(reason=reason)
    await interaction.response.send_message("👢 kickato", ephemeral=True)

@bot.tree.command(name="clear")
async def clear(interaction: discord.Interaction, amount: int):
    await interaction.channel.purge(limit=amount)
    await interaction.response.send_message("🧹 pulito", ephemeral=True)

# =========================
# WARN
# =========================
@bot.tree.command(name="warn")
async def warn(interaction: discord.Interaction, member: discord.Member, reason: str):

    warns = load_warns()
    uid = str(member.id)

    warns.setdefault(uid, []).append(reason)
    save_warns(warns)

    await interaction.response.send_message("⚠️ warn dato", ephemeral=True)

@bot.tree.command(name="warns")
async def warns(interaction: discord.Interaction, member: discord.Member):

    warns = load_warns().get(str(member.id), [])
    await interaction.response.send_message("\n".join(warns) if warns else "nessun warn", ephemeral=True)

# =========================
# ANTI SPAM
# =========================
@bot.event
async def on_message(message: discord.Message):

    if message.author.bot:
        return

    now = time.time()
    uid = message.author.id

    spam_cache.setdefault(uid, []).append(now)
    spam_cache[uid] = [t for t in spam_cache[uid] if now - t < 5]

    if len(spam_cache[uid]) > 5:
        await message.channel.send(f"⚠️ spam {message.author.mention}")

    await bot.process_commands(message)

# =========================
# RAID TOGGLE
# =========================
@bot.tree.command(name="raid")
async def raid(interaction: discord.Interaction):

    global raid_mode
    raid_mode = not raid_mode

    await interaction.response.send_message(f"🚨 raid: {raid_mode}", ephemeral=True)

# =========================
# RUN
# =========================
bot.run(TOKEN)import discord
from discord.ext import commands
import os
import json
import time
from dotenv import load_dotenv

# =========================
# CONFIG
# =========================
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

if not TOKEN:
    raise ValueError("DISCORD_TOKEN mancante")

BANNER = "https://cdn.discordapp.com/attachments/1482844068009738434/1511074300755574975/ChatGPT_Image_1_giu_2026_20_28_18.png"

STAFF_ROLE = "🎫 Support"
TICKET_CATEGORY = "🎫 TICKETS"
LOG_CHANNEL = "📋・logs"
WARN_FILE = "warns.json"

# =========================
# INTENTS (FIX IMPORTANTISSIMO)
# =========================
intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

raid_mode = False
spam_cache = {}

# =========================
# WARN SYSTEM
# =========================
def load_warns():
    if not os.path.exists(WARN_FILE):
        return {}
    with open(WARN_FILE, "r") as f:
        return json.load(f)

def save_warns(data):
    with open(WARN_FILE, "w") as f:
        json.dump(data, f, indent=4)

# =========================
# LOG SAFE
# =========================
async def log(guild, text):
    try:
        channel = discord.utils.get(guild.text_channels, name=LOG_CHANNEL)
        if channel:
            await channel.send(text)
    except:
        pass

# =========================
# READY
# =========================
@bot.event
async def on_ready():
    print(f"🔴 UNITY ONLINE: {bot.user}")

    await bot.tree.sync()

    # FIX VIEW PERSISTENTI
    bot.add_view(VerifyView())
    bot.add_view(AdminView())
    bot.add_view(TicketView())

# =========================
# WELCOME / GOODBYE (FIX)
# =========================
@bot.event
async def on_member_join(member):
    global raid_mode

    try:
        if raid_mode:
            await member.kick(reason="ANTI RAID")
            return

        await log(member.guild, f"🟢 JOIN {member}")

        channel = discord.utils.get(member.guild.text_channels, name="👋・welcome")

        if channel:
            embed = discord.Embed(
                title="🔴 UNITY",
                description=f"Benvenuto {member.mention}",
                color=discord.Color.red()
            )
            embed.set_image(url=BANNER)
            await channel.send(embed=embed)

    except:
        pass


@bot.event
async def on_member_remove(member):
    try:
        await log(member.guild, f"🔴 LEAVE {member}")

        channel = discord.utils.get(member.guild.text_channels, name="💔・goodbye")

        if channel:
            embed = discord.Embed(
                title="🔴 ADDIO",
                description=f"{member} ha lasciato il server",
                color=discord.Color.red()
            )
            embed.set_image(url=BANNER)
            await channel.send(embed=embed)

    except:
        pass

# =========================
# VERIFY
# =========================
class VerifyView(discord.ui.View):

    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Verifica", emoji="🔐", style=discord.ButtonStyle.danger)
    async def verify(self, interaction: discord.Interaction, button: discord.ui.Button):

        role = discord.utils.get(interaction.guild.roles, name="Membro")

        if not role:
            return await interaction.response.send_message("❌ ruolo mancante", ephemeral=True)

        await interaction.user.add_roles(role)
        await interaction.response.send_message("✔ verificato", ephemeral=True)

@bot.tree.command(name="verifypanel")
async def verifypanel(interaction: discord.Interaction):

    embed = discord.Embed(
        title="🔐 UNITY VERIFY",
        color=discord.Color.red()
    )
    embed.set_image(url=BANNER)

    await interaction.response.send_message(embed=embed, view=VerifyView())

# =========================
# ANNUNCI
# =========================
@bot.tree.command(name="annunci")
async def annunci(interaction: discord.Interaction, titolo: str, messaggio: str):

    if not interaction.user.guild_permissions.administrator:
        return await interaction.response.send_message("❌ no permessi", ephemeral=True)

    embed = discord.Embed(
        title=f"🔴 {titolo}",
        description=messaggio,
        color=discord.Color.red()
    )
    embed.set_image(url=BANNER)

    await interaction.channel.send(embed=embed)
    await interaction.response.send_message("✔ inviato", ephemeral=True)

# =========================
# MODERAZIONE
# =========================
@bot.tree.command(name="ban")
async def ban(interaction: discord.Interaction, member: discord.Member, reason: str = "no reason"):
    await member.ban(reason=reason)
    await interaction.response.send_message("🔨 bannato", ephemeral=True)

@bot.tree.command(name="kick")
async def kick(interaction: discord.Interaction, member: discord.Member, reason: str = "no reason"):
    await member.kick(reason=reason)
    await interaction.response.send_message("👢 kickato", ephemeral=True)

@bot.tree.command(name="clear")
async def clear(interaction: discord.Interaction, amount: int):
    await interaction.channel.purge(limit=amount)
    await interaction.response.send_message("🧹 pulito", ephemeral=True)

# =========================
# WARN SYSTEM
# =========================
@bot.tree.command(name="warn")
async def warn(interaction: discord.Interaction, member: discord.Member, reason: str):

    warns = load_warns()
    uid = str(member.id)

    warns.setdefault(uid, []).append(reason)
    save_warns(warns)

    await interaction.response.send_message("⚠️ warn dato", ephemeral=True)

@bot.tree.command(name="warns")
async def warns(interaction: discord.Interaction, member: discord.Member):

    warns = load_warns().get(str(member.id), [])
    await interaction.response.send_message("\n".join(warns) if warns else "nessun warn", ephemeral=True)

# =========================
# ANTI SPAM (FIX)
# =========================
@bot.event
async def on_message(message: discord.Message):

    try:
        if message.author.bot:
            return

        now = time.time()
        uid = message.author.id

        spam_cache.setdefault(uid, []).append(now)
        spam_cache[uid] = [t for t in spam_cache[uid] if now - t < 5]

        if len(spam_cache[uid]) > 5:
            await message.channel.send(f"⚠️ spam {message.author.mention}")

        await bot.process_commands(message)

    except:
        pass

# =========================
# RAID TOGGLE
# =========================
@bot.tree.command(name="raid")
async def raid(interaction: discord.Interaction):

    global raid_mode
    raid_mode = not raid_mode

    await interaction.response.send_message(f"🚨 raid mode: {raid_mode}", ephemeral=True)

# =========================
# TICKET SYSTEM
# =========================
class TicketView(discord.ui.View):

    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Apri Ticket", emoji="🎫", style=discord.ButtonStyle.danger)
    async def open(self, interaction: discord.Interaction, button: discord.ui.Button):

        guild = interaction.guild
        user = interaction.user

        category = discord.utils.get(guild.categories, name=TICKET_CATEGORY)
        if not category:
            category = await guild.create_category(TICKET_CATEGORY)

        channel = await guild.create_text_channel(f"ticket-{user.id}", category=category)

        await channel.set_permissions(guild.default_role, view_channel=False)
        await channel.set_permissions(user, view_channel=True, send_messages=True)

        staff = discord.utils.get(guild.roles, name=STAFF_ROLE)
        if staff:
            await channel.set_permissions(staff, view_channel=True, send_messages=True)

        embed = discord.Embed(
            title="🎫 UNITY TICKET",
            description=user.mention,
            color=discord.Color.red()
        )

        await channel.send(embed=embed, view=TicketControl())
        await interaction.response.send_message(f"✔ {channel.mention}", ephemeral=True)

class TicketControl(discord.ui.View):

    def __init__(self):
        super().__init__(timeout=None)
        self.claimed = None

    @discord.ui.button(label="Claim", emoji="👑", style=discord.ButtonStyle.success)
    async def claim(self, interaction: discord.Interaction, button: discord.ui.Button):

        role = discord.utils.get(interaction.guild.roles, name=STAFF_ROLE)

        if role not in interaction.user.roles:
            return await interaction.response.send_message("❌ no staff", ephemeral=True)

        if self.claimed:
            return await interaction.response.send_message("❌ già claimato", ephemeral=True)

        self.claimed = interaction.user
        await interaction.channel.send(f"👑 claimato da {interaction.user.mention}")
        await interaction.response.send_message("✔ claim ok", ephemeral=True)

    @discord.ui.button(label="Chiudi", emoji="🔒", style=discord.ButtonStyle.danger)
    async def close(self, interaction: discord.Interaction, button: discord.ui.Button):

        await interaction.channel.delete()

# =========================
# DASHBOARD
# =========================
class AdminView(discord.ui.View):

    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="RAID ON/OFF", style=discord.ButtonStyle.danger)
    async def raid(self, interaction: discord.Interaction, button: discord.ui.Button):

        global raid_mode
        raid_mode = not raid_mode

        await interaction.response.send_message(f"🚨 {raid_mode}", ephemeral=True)

@bot.tree.command(name="dashboard")
async def dashboard(interaction: discord.Interaction):

    if not interaction.user.guild_permissions.administrator:
        return await interaction.response.send_message("❌ no permessi", ephemeral=True)

    embed = discord.Embed(
        title="⚙️ UNITY DASHBOARD",
        color=discord.Color.red()
    )
    embed.set_image(url=BANNER)

    await interaction.response.send_message(embed=embed, view=AdminView(), ephemeral=True)

# =========================
# RUN
# =========================
bot.run(TOKEN)
