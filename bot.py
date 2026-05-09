import discord
from discord import app_commands
from discord.ext import commands
import json
import os

# ── Config ──────────────────────────────────────────────────────────────────
ROSTER_FILE = "roster.json"
MAX_ROSTER  = 20

# ── Persistence ──────────────────────────────────────────────────────────────
def load_data() -> dict:
    if os.path.exists(ROSTER_FILE):
        with open(ROSTER_FILE, "r") as f:
            return json.load(f)
    return {"players": [], "captain": None, "vice": None}


def save_data(data: dict) -> None:
    with open(ROSTER_FILE, "w") as f:
        json.dump(data, f, indent=2)


# ── Bot setup ────────────────────────────────────────────────────────────────
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)


@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"✅  Logged in as {bot.user} (ID: {bot.user.id})")
    print("Slash commands synced.")


# ── Helper: build embed ───────────────────────────────────────────────────────
def build_roster_embed(data: dict) -> discord.Embed:
    players = data["players"]
    captain = data["captain"]
    vice    = data["vice"]

    embed = discord.Embed(
        title="🏆  Team Roster",
        color=0x2F3136,
    )

    if not players:
        embed.description = "*No players on the roster yet.*"
        return embed

    lines = []
    for i, name in enumerate(players, start=1):
        tags = []
        if name == captain:
            tags.append("👑 Captain")
        elif name == vice:
            tags.append("🥈 Vice")
        tag_str = f"  — **{', '.join(tags)}**" if tags else ""
        lines.append(f"`{i:02d}.`  {name}{tag_str}")

    embed.description = "\n".join(lines)
    embed.set_footer(text=f"{len(players)}/{MAX_ROSTER} players")
    return embed


# ── /roster ───────────────────────────────────────────────────────────────────
@bot.tree.command(name="roster", description="Add a player to the roster.")
@app_commands.describe(player="The player's name to add.")
async def cmd_roster(interaction: discord.Interaction, player: str):
    data = load_data()

    if len(data["players"]) >= MAX_ROSTER:
        await interaction.response.send_message(
            f"❌  Roster is full ({MAX_ROSTER}/{MAX_ROSTER}). Remove someone first.",
            ephemeral=True,
        )
        return

    if player in data["players"]:
        await interaction.response.send_message(
            f"❌  **{player}** is already on the roster.", ephemeral=True
        )
        return

    data["players"].append(player)
    save_data(data)
    await interaction.response.send_message(
        f"✅  **{player}** added to the roster. ({len(data['players'])}/{MAX_ROSTER})"
    )


# ── /cut ──────────────────────────────────────────────────────────────────────
@bot.tree.command(name="cut", description="Remove a player from the roster.")
@app_commands.describe(player="The player's name to remove.")
async def cmd_cut(interaction: discord.Interaction, player: str):
    data = load_data()

    if player not in data["players"]:
        await interaction.response.send_message(
            f"❌  **{player}** is not on the roster.", ephemeral=True
        )
        return

    data["players"].remove(player)

    # Clear roles if the removed player held them
    if data["captain"] == player:
        data["captain"] = None
    if data["vice"] == player:
        data["vice"] = None

    save_data(data)
    await interaction.response.send_message(f"🗑️  **{player}** has been cut from the roster.")


# ── /setcaptain ───────────────────────────────────────────────────────────────
@bot.tree.command(name="setcaptain", description="Set a player as the team captain.")
@app_commands.describe(player="The player to make captain.")
async def cmd_setcaptain(interaction: discord.Interaction, player: str):
    data = load_data()

    if player not in data["players"]:
        await interaction.response.send_message(
            f"❌  **{player}** is not on the roster. Add them first.", ephemeral=True
        )
        return

    # If they're currently vice, clear that role
    if data["vice"] == player:
        data["vice"] = None

    data["captain"] = player
    save_data(data)
    await interaction.response.send_message(f"👑  **{player}** is now the **Captain**!")


# ── /setvice ──────────────────────────────────────────────────────────────────
@bot.tree.command(name="setvice", description="Set a player as the vice captain.")
@app_commands.describe(player="The player to make vice captain.")
async def cmd_setvice(interaction: discord.Interaction, player: str):
    data = load_data()

    if player not in data["players"]:
        await interaction.response.send_message(
            f"❌  **{player}** is not on the roster. Add them first.", ephemeral=True
        )
        return

    if data["captain"] == player:
        await interaction.response.send_message(
            f"❌  **{player}** is already the Captain. Assign a different player.", ephemeral=True
        )
        return

    data["vice"] = player
    save_data(data)
    await interaction.response.send_message(f"🥈  **{player}** is now the **Vice Captain**!")


# ── /removevice ───────────────────────────────────────────────────────────────
@bot.tree.command(name="removevice", description="Remove the current vice captain designation.")
async def cmd_removevice(interaction: discord.Interaction):
    data = load_data()

    if not data["vice"]:
        await interaction.response.send_message(
            "❌  There is no vice captain set.", ephemeral=True
        )
        return

    old = data["vice"]
    data["vice"] = None
    save_data(data)
    await interaction.response.send_message(f"🔄  **{old}** is no longer the Vice Captain.")


# ── /showroster ───────────────────────────────────────────────────────────────
@bot.tree.command(name="showroster", description="Display the current team roster.")
async def cmd_showroster(interaction: discord.Interaction):
    data = load_data()
    embed = build_roster_embed(data)
    await interaction.response.send_message(embed=embed)


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    TOKEN = os.getenv("DISCORD_TOKEN")
    if not TOKEN:
        raise RuntimeError("Set the DISCORD_TOKEN environment variable before running.")
    bot.run(TOKEN)
