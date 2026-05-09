# 🏆 Team Roster Discord Bot

A slash-command Discord bot for managing a team roster of up to 20 players with Captain and Vice Captain roles.

---

## Setup

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Create a Discord Application & Bot
1. Go to https://discord.com/developers/applications
2. Click **New Application** → give it a name
3. Go to **Bot** → click **Add Bot**
4. Under **Token**, click **Reset Token** and copy it
5. Under **Privileged Gateway Intents**, enable what you need (none required for slash commands)
6. Go to **OAuth2 → URL Generator**
   - Scopes: `bot`, `applications.commands`
   - Bot Permissions: `Send Messages`, `Embed Links`
7. Open the generated URL and invite the bot to your server

### 3. Set your token & run
```bash
# macOS/Linux
export DISCORD_TOKEN="your-token-here"
python bot.py

# Windows (CMD)
set DISCORD_TOKEN=your-token-here
python bot.py

# Windows (PowerShell)
$env:DISCORD_TOKEN="your-token-here"
python bot.py
```

> ⚠️ The first run syncs slash commands globally — it may take up to **1 hour** for them to appear in Discord. For faster testing, use guild-specific sync (see note in code).

---

## Commands

| Command | Description |
|---|---|
| `/roster <player>` | Add a player to the roster (max 20) |
| `/cut <player>` | Remove a player from the roster |
| `/setcaptain <player>` | Assign a player as 👑 Captain |
| `/setvice <player>` | Assign a player as 🥈 Vice Captain |
| `/removevice` | Remove the Vice Captain designation |
| `/showroster` | Display the full roster embed |

---

## File Structure
```
roster_bot/
├── bot.py          # Main bot code
├── roster.json     # Persistent roster data (auto-created/updated)
├── requirements.txt
└── README.md
```

The `roster.json` file is pre-loaded with your 13 current players. Edit it directly if needed, or use bot commands to manage the roster.

---

## Tips
- The roster persists to `roster.json` — it survives bot restarts.
- Cutting a player who holds Captain or Vice also clears that role automatically.
- Assigning a player Captain automatically removes their Vice tag if they had one.
- The roster embed numbers each player `01–20` and highlights roles inline.
