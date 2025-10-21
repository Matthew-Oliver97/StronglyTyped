<div align="center">

# Strongly Typed

Command-line multiplayer typing race that works reliably across restrictive networks (firewalls, VPNs, NAT). Challenge a friend to a real‑time duel right in your terminal.
</div>

## 1. Features
- Real-time competition: Live Words Per Minute (WPM), accuracy, and progress for both players.
- Robust networking: Uses a public MQTT relay server to traverse firewalls/VPNs—no port forwarding needed.
- Clean terminal UI: Built with Python's `curses` for smooth input & live updates.
- Zero-friction setup: One shell script creates a virtual environment & installs dependencies.
- Cross-platform: Works anywhere Python 3 runs (macOS, Linux; Windows via WSL).
- Deterministic race text (or future customizable passages).

## 2. How It Works
Direct peer-to-peer connections often fail behind NAT, firewalls, or corporate VPNs. Terminal Velocity avoids this by having both players connect to a neutral public MQTT broker. Each player publishes their state (progress, WPM, accuracy) on a private topic and subscribes to the opponent's topic. The game code (e.g. `typing-game/a4f1c8e0`) namespaces these topics so only the two participants see each other's updates.

Data exchanged:
- Session handshake (game code confirmation)
- Per-keystroke or timed progress snapshots
- Computed metrics (WPM, accuracy, completion flag)

No sensitive personal data is sent; only gameplay stats. When both players finish (or one finishes first), a completion message is published and the session ends.

## 3. Requirements
- Python 3.8+ (recommended)
- macOS users: Homebrew if you need to install Python (`brew install python`)

## 4. Installation
Make sure these two files are in the same directory:

```
.
├── runTypingGame.sh
└── typing_game.py
```

Give the script execute permission (one-time):

```bash
chmod +x runTypingGame.sh
```

## 5. Usage (Host & Join)
Start the game script (creates venv & installs `paho-mqtt` automatically):

```bash
./runTypingGame.sh
```
```bash
chmod +x runTypingGame.sh
```

## 5. Usage (Host & Join)
Start the game script (creates venv & installs `paho-mqtt` automatically):

```bash
./runTypingGame.sh
```bash
./runTypingGame.sh
```

In the menu:

### Host (Player 1)
1. Press `1` for Create Game.
2. Note the generated game code (example: `typing-game/a4f1c8e0`).
3. Share the code with your friend.
4. Wait—game starts when they join.

### Join (Player 2)
1. Press `2` for Join Game.
2. Paste the exact game code you received.
3. Press Enter to connect.
4. Game launches simultaneously for both players.

Winning condition: First player to correctly type the entire passage. Accuracy influences bragging rights but not winner selection (winner determined by completion time).

## 6. Gameplay UI
Example (illustrative only):

```
Type the following text:

    The quick brown fox jumps over the lazy dog.

    The quikc brown f|
---------------------------------------------------------------
Your Stats   -> WPM: 45 | Progress: 35% | Accuracy: 95.0%
Opponent     -> WPM: 42 | Progress: 32% | Accuracy: 98.0%
```

UI Regions:
- Passage display
- Live partially typed input (cursor bar shows current position)
- Status panel with self vs opponent metrics

## 7. Troubleshooting
- `python3` not found: Script defaults to Apple Silicon path `/opt/homebrew/bin/python3`. On Intel macOS adjust `PYTHON_CMD` in `runTypingGame.sh` to `/usr/local/bin/python3`.
- Dependency install failed: Ensure network access to PyPI and MQTT broker; try deleting the `.venv` folder and rerunning.
- Terminal size issues: Increase window width; `curses` layout expects ~80 columns.
- High latency: Public brokers can vary; future version may allow custom broker selection.