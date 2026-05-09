import discord
from discord import app_commands
from discord.ext import commands
import json
import os
 
# ── Config ───────────────────────────────────────────────────────────────────
ROSTER_FILE       = "roster.json"
MAX_ROSTER        = 20
DEFAULT_FORMATION = ["ST", "ST", "CAM", "CM", "CM", "CDM", "WB", "WB", "CB", "CB", "GK"]
 
POSITION_EMOJIS: dict[str, str] = {
    "ST":  "⚽",
    "CF":  "🔥",
    "CAM": "🎯",
    "LW":  "⚡",
    "RW":  "⚡",
    "CM":  "👟",
    "CDM": "🛡️",
    "DM":  "🛡️",
    "WB":  "💨",
    "LB":  "💨",
    "RB":  "💨",
    "CB":  "🧱",
    "GK":  "🧤",
}
 
# ── Persistence ───────────────────────────────────────────────────────────────
def load_data() -> dict:
    if os.path.exists(ROSTER_FILE):
        with open(ROSTER_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        data.setdefault("formation", DEFAULT_FORMATION)
        data.setdefault("lineup", [None] * len(data["formation"]))
        data.setdefault("position_roles", {})
        return data
    return {
        "players":        [],
        "captain":        None,
        "vice":           None,
        "formation":      DEFAULT_FORMATION.copy(),
        "lineup":         [None] * len(DEFAULT_FORMATION),
        "position_roles": {},
    }
 
def save_data(data: dict) -> None:
    with open(ROSTER_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
 
def sync_lineup_size(data: dict) -> None:
    size    = len(data["formation"])
    current = data.get("lineup", [])
    if len(current) < size:
        data["lineup"] = current + [None] * (size - len(current))
    elif len(current) > size:
        data["lineup"] = current[:size]
 
# ── Helpers ───────────────────────────────────────────────────────────────────
def pos_emoji(position: str) -> str:
    return POSITION_EMOJIS.get(position.upper(), "🔵")
 
def is_admin(interaction: discord.Interaction) -> bool:
    perms = interaction.user.guild_permissions
    return perms.administrator or perms.manage_guild
 
# ── Embed builders ────────────────────────────────────────────────────────────
def build_roster_embed(data: dict) -> discord.Embed:
    players = data["players"]
    captain = data["captain"]
    vice    = data["vice"]
    embed   = discord.Embed(title="🏆  Team Roster", color=0x2F3136)
    if not players:
        embed.description = "*No players on the roster yet.*"
        return embed
    lines = []
    for i, name in enumerate(players, 1):
        tags = []
        if name == captain:
            tags.append("👑 Captain")
        elif name == vice:
            tags.append("🥈 Vice")
        suffix = f"  — **{', '.join(tags)}**" if tags else ""
        lines.append(f"`{i:02d}.`  {name}{suffix}")
    embed.description = "\n".join(lines)
    embed.set_footer(text=f"{len(players)}/{MAX_ROSTER} players")
    return embed
 
def build_lineup_embed(data: dict) -> discord.Embed:
    formation = data["formation"]
    lineup    = data["lineup"]
    sync_lineup_size(data)
    in_lineup = {p for p in lineup if p}
    bench     = [p for p in data["players"] if p not in in_lineup]
    embed     = discord.Embed(title="📋  Starting Lineup", color=0x00A651)
    embed.add_field(name="Formation", value=" · ".join(formation), inline=False)
    lines = []
    for i, (pos, player) in enumerate(zip(formation, lineup), 1):
        emoji = pos_emoji(pos)
        p_str = f"**{player}**" if player else "*Empty*"
        if player and player == data.get("captain"):
            p_str += "  👑"
        elif player and player == data.get("vice"):
            p_str += "  🥈"
        lines.append(f"{emoji} `{pos:<4}` #{i:02d}  {p_str}")
    embed.add_field(name="Starting XI", value="\n".join(lines), inline=False)
    if bench:
        embed.add_field(
            name="🪑  Bench / Did Not Make Cut",
            value="\n".join(f"• {p}" for p in bench),
            inline=False,
        )
    filled = sum(1 for p in lineup if p)
    embed.set_footer(text=f"{filled}/{len(formation)} spots filled  •  {len(bench)} on bench")
    return embed
 
# ── Bot ───────────────────────────────────────────────────────────────────────
intents         = discord.Intents.default()
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)
 
@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"✅  Logged in as {bot.user} (ID: {bot.user.id})")
    print("Slash commands synced globally.")
 
# ═════════════════════════════════════════════════════════════════════════════
#  ROSTER COMMANDS  (admin-only)
# ═════════════════════════════════════════════════════════════════════════════
 
@bot.tree.command(name="roster", description="[Admin] Add a player to the roster.")
@app_commands.describe(player="The player's name to add.")
async def cmd_roster(interaction: discord.Interaction, player: str):
    if not is_admin(interaction):
        await interaction.response.send_message("❌  Only admins can use this command.", ephemeral=True); return
    data = load_data()
    if len(data["players"]) >= MAX_ROSTER:
        await interaction.response.send_message(f"❌  Roster is full ({MAX_ROSTER}/{MAX_ROSTER}).", ephemeral=True); return
    if player in data["players"]:
        await interaction.response.send_message(f"❌  **{player}** is already on the roster.", ephemeral=True); return
    data["players"].append(player)
    save_data(data)
    await interaction.response.send_message(f"✅  **{player}** added. ({len(data['players'])}/{MAX_ROSTER})")
 
@bot.tree.command(name="cut", description="[Admin] Remove a player from the roster.")
@app_commands.describe(player="The player's name to remove.")
async def cmd_cut(interaction: discord.Interaction, player: str):
    if not is_admin(interaction):
        await interaction.response.send_message("❌  Only admins can use this command.", ephemeral=True); return
    data = load_data()
    if player not in data["players"]:
        await interaction.response.send_message(f"❌  **{player}** is not on the roster.", ephemeral=True); return
    data["players"].remove(player)
    if data["captain"] == player: data["captain"] = None
    if data["vice"] == player:    data["vice"]    = None
    data["lineup"] = [None if p == player else p for p in data.get("lineup", [])]
    save_data(data)
    await interaction.response.send_message(f"🗑️  **{player}** has been cut from the roster.")
 
@bot.tree.command(name="setcaptain", description="[Admin] Set a player as the team captain.")
@app_commands.describe(player="The player to make captain.")
async def cmd_setcaptain(interaction: discord.Interaction, player: str):
    if not is_admin(interaction):
        await interaction.response.send_message("❌  Only admins can use this command.", ephemeral=True); return
    data = load_data()
    if player not in data["players"]:
        await interaction.response.send_message(f"❌  **{player}** is not on the roster.", ephemeral=True); return
    if data["vice"] == player: data["vice"] = None
    data["captain"] = player
    save_data(data)
    await interaction.response.send_message(f"👑  **{player}** is now the **Captain**!")
 
@bot.tree.command(name="setvice", description="[Admin] Set a player as the vice captain.")
@app_commands.describe(player="The player to make vice captain.")
async def cmd_setvice(interaction: discord.Interaction, player: str):
    if not is_admin(interaction):
        await interaction.response.send_message("❌  Only admins can use this command.", ephemeral=True); return
    data = load_data()
    if player not in data["players"]:
        await interaction.response.send_message(f"❌  **{player}** is not on the roster.", ephemeral=True); return
    if data["captain"] == player:
        await interaction.response.send_message(f"❌  **{player}** is already the Captain.", ephemeral=True); return
    data["vice"] = player
    save_data(data)
    await interaction.response.send_message(f"🥈  **{player}** is now the **Vice Captain**!")
 
@bot.tree.command(name="removevice", description="[Admin] Remove the vice captain designation.")
async def cmd_removevice(interaction: discord.Interaction):
    if not is_admin(interaction):
        await interaction.response.send_message("❌  Only admins can use this command.", ephemeral=True); return
    data = load_data()
    if not data["vice"]:
        await interaction.response.send_message("❌  No vice captain is set.", ephemeral=True); return
    old = data["vice"]
    data["vice"] = None
    save_data(data)
    await interaction.response.send_message(f"🔄  **{old}** is no longer the Vice Captain.")
 
@bot.tree.command(name="showroster", description="Display the current team roster.")
async def cmd_showroster(interaction: discord.Interaction):
    data = load_data()
    await interaction.response.send_message(embed=build_roster_embed(data))
 
# ═════════════════════════════════════════════════════════════════════════════
#  LINEUP COMMANDS
# ═════════════════════════════════════════════════════════════════════════════
 
@bot.tree.command(name="showlineup", description="Display the current starting lineup.")
async def cmd_showlineup(interaction: discord.Interaction):
    data = load_data()
    sync_lineup_size(data)
    await interaction.response.send_message(embed=build_lineup_embed(data))
    msg  = await interaction.original_response()
    seen: set[str] = set()
    for pos in data["formation"]:
        if pos not in seen:
            try:
                await msg.add_reaction(pos_emoji(pos))
            except Exception:
                pass
            seen.add(pos)
 
@bot.tree.command(name="setformation", description="[Admin] Change the team formation (resets lineup).")
@app_commands.describe(positions="Space-separated positions e.g: ST ST CAM CM CM CDM WB WB CB CB GK")
async def cmd_setformation(interaction: discord.Interaction, positions: str):
    if not is_admin(interaction):
        await interaction.response.send_message("❌  Only admins can use this command.", ephemeral=True); return
    pos_list = [p.upper() for p in positions.strip().split()]
    if not pos_list:
        await interaction.response.send_message("❌  Provide at least one position.", ephemeral=True); return
    if len(pos_list) > 20:
        await interaction.response.send_message("❌  Maximum 20 positions.", ephemeral=True); return
    data = load_data()
    data["formation"] = pos_list
    data["lineup"]    = [None] * len(pos_list)
    save_data(data)
    preview = "  ".join(f"{pos_emoji(p)}`{p}`" for p in pos_list)
    await interaction.response.send_message(
        f"✅  Formation updated to **{len(pos_list)} slots** — lineup cleared.\n{preview}"
    )
 
@bot.tree.command(name="assign", description="[Admin] Assign a player to a lineup slot.")
@app_commands.describe(slot="Slot number (see /showlineup)", player="Player name to assign")
async def cmd_assign(interaction: discord.Interaction, slot: int, player: str):
    if not is_admin(interaction):
        await interaction.response.send_message("❌  Only admins can use this command.", ephemeral=True); return
    data = load_data()
    sync_lineup_size(data)
    if player not in data["players"]:
        await interaction.response.send_message(f"❌  **{player}** is not on the roster.", ephemeral=True); return
    if slot < 1 or slot > len(data["formation"]):
        await interaction.response.send_message(f"❌  Slot must be 1–{len(data['formation'])}.", ephemeral=True); return
    data["lineup"] = [None if p == player else p for p in data["lineup"]]
    data["lineup"][slot - 1] = player
    save_data(data)
    pos = data["formation"][slot - 1]
    await interaction.response.send_message(f"✅  **{player}** → slot #{slot:02d} {pos_emoji(pos)}`{pos}`")
 
@bot.tree.command(name="unassign", description="[Admin] Move a player from lineup back to bench.")
@app_commands.describe(player="Player to remove from the lineup.")
async def cmd_unassign(interaction: discord.Interaction, player: str):
    if not is_admin(interaction):
        await interaction.response.send_message("❌  Only admins can use this command.", ephemeral=True); return
    data = load_data()
    sync_lineup_size(data)
    if player not in data["lineup"]:
        await interaction.response.send_message(f"❌  **{player}** is not in the lineup.", ephemeral=True); return
    data["lineup"] = [None if p == player else p for p in data["lineup"]]
    save_data(data)
    await interaction.response.send_message(f"🔄  **{player}** moved to bench.")
 
@bot.tree.command(name="clearlineup", description="[Admin] Clear all lineup assignments.")
async def cmd_clearlineup(interaction: discord.Interaction):
    if not is_admin(interaction):
        await interaction.response.send_message("❌  Only admins can use this command.", ephemeral=True); return
    data = load_data()
    data["lineup"] = [None] * len(data.get("formation", DEFAULT_FORMATION))
    save_data(data)
    await interaction.response.send_message("🔄  Lineup cleared. All players moved to bench.")
 
@bot.tree.command(name="autofill", description="[Admin] Auto-assign players using Discord role priority.")
async def cmd_autofill(interaction: discord.Interaction):
    if not is_admin(interaction):
        await interaction.response.send_message("❌  Only admins can use this command.", ephemeral=True); return
    await interaction.response.defer()
    data           = load_data()
    sync_lineup_size(data)
    formation      = data["formation"]
    lineup         = [None] * len(formation)
    position_roles = data.get("position_roles", {})
    guild          = interaction.guild
 
    player_roles: dict[str, set[str]] = {}
    for player in data["players"]:
        member = discord.utils.find(
            lambda m, n=player: m.display_name.lower() == n.lower() or m.name.lower() == n.lower(),
            guild.members,
        )
        player_roles[player] = {r.name.upper() for r in member.roles} if member else set()
 
    assigned: set[str] = set()
 
    # Priority pass — role match
    for i, pos in enumerate(formation):
        if lineup[i]: continue
        priority = position_roles.get(pos.upper(), "").upper()
        for player in data["players"]:
            if player in assigned: continue
            roles = player_roles.get(player, set())
            if pos.upper() in roles or (priority and priority in roles):
                lineup[i] = player
                assigned.add(player)
                break
 
    # Fill remaining in roster order
    remaining = [p for p in data["players"] if p not in assigned]
    for i in range(len(formation)):
        if lineup[i] is None and remaining:
            lineup[i] = remaining.pop(0)
            assigned.add(lineup[i])
 
    data["lineup"] = lineup
    save_data(data)
    filled = sum(1 for p in lineup if p)
    bench  = len(data["players"]) - filled
    await interaction.followup.send(
        f"✅  Autofill complete!  **{filled}/{len(formation)}** in lineup  •  **{bench}** on bench.\n"
        "Use `/showlineup` to see the result."
    )
 
@bot.tree.command(name="setrole", description="[Admin] Map a Discord role to a position for autofill priority.")
@app_commands.describe(position="Position code e.g. ST, CM, GK", role="Discord role to prioritise for this position")
async def cmd_setrole(interaction: discord.Interaction, position: str, role: discord.Role):
    if not is_admin(interaction):
        await interaction.response.send_message("❌  Only admins can use this command.", ephemeral=True); return
    data = load_data()
    data["position_roles"][position.upper()] = role.name
    save_data(data)
    await interaction.response.send_message(
        f"✅  **@{role.name}** → {pos_emoji(position)}`{position.upper()}` priority set."
    )
 
@bot.tree.command(name="viewroles", description="Show position-to-role priority mappings.")
async def cmd_viewroles(interaction: discord.Interaction):
    data  = load_data()
    pr    = data.get("position_roles", {})
    embed = discord.Embed(title="🎭  Position Role Priorities", color=0x5865F2)
    if not pr:
        embed.description = "*No role priorities set yet. Use `/setrole` to configure.*"
    else:
        embed.description = "\n".join(f"{pos_emoji(pos)} `{pos}` → **@{role}**" for pos, role in pr.items())
    await interaction.response.send_message(embed=embed)
 
# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    TOKEN = os.getenv("DISCORD_TOKEN")
    if not TOKEN:
        raise RuntimeError("Set the DISCORD_TOKEN environment variable before running.")
    bot.run(TOKEN)
 
