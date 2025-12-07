# P2W (Ping 2 Win)

A ridiculously simple multiplayer game where the goal is to ping a server.  
The first person to successfully ping wins. That's literally the whole game.

---

## Table of Contents
1. [Overview](#overview)  
2. [Features](#features)  
3. [How It Works](#how-it-works)  
4. [Requirements](#requirements)  
5. [Installation](#installation)  
6. [Usage](#usage)  
7. [Configuration](#configuration)  
8. [File Structure](#file-structure)  
9. [Troubleshooting](#troubleshooting)  
10. [Contributing](#contributing)  
11. [License](#license)  
12. [Credits](#credits)  
13. [To-Do](#to-do)  
14. [FAQ](#faq)  
15. [Support](#support)
> NOTE: This README.md may contain outdated information, i tried to update it as good as possible since i dont have much time (i have a life) and my english writing isnt that good. Most of this stuff will be moved to Wiki to keep the readme minimal and understandable.
---

## Overview

P2W is a lightweight Python client–server game.  
Players connect to a server, and the **first one to send a ping wins**.  
Each player can only win once per server, and winners are stored in a persistent leaderboard.

---

## Features

- **Minimalist gameplay** — one button, one ping, one win  
- **Live statistics** — real-time online players, server uptime, total winners  
- **Persistent leaderboard** — stored with timestamps + latency  
- **Rate limiting** — IP-based (1 ping per 10 seconds)  
- **Latency tracking** — per-player measurement  
- **Low resource usage** — ~10MB RAM server  
- **Cross-platform** — Windows, Linux (Planned), macOS (Planned)

---

## How It Works

### Server
- Listens for TCP connections  
- Handles: connect, ping, stats, leaderboard, disconnect  
- IP-based rate limiting (10 seconds)  
- Stores winners in JSON (`winners_[port].json`)  
- Multi-threaded to handle concurrent clients  

### Client
- tkinter GUI  
- Displays latency + live server statistics  
- Prevents multiple pings  
- Leaderboard with sortable columns  
- Updates stats every 3 seconds  

### Protocol Messages

- `CONNECT:[username]`  
- `P2W_PING:[username]|[latency]`  
- `GET_STATS`  
- `GET_LEADERBOARD`  
- `DISCONNECT:[username]`

---

## Requirements

- Python 3.7+  
- tkinter  
- Standard library modules: `socket`, `json`, `threading`, `time`

> If using the compiled `.exe` from Releases, all you need is Windows and electricity.

---

## Installation

### Running from Source

1. Clone the repository:
```bash
git clone https://github.com/kroefer1/ping2win.git
cd ping2win
```

2. No dependencies needed — uses only the Python standard library.

3. Start the server:
```bash
python server.py
```

4. Start the client:
```bash
python client.py
```

---

### Building Standalone Executables

1. Install PyInstaller:
```bash
pip install pyinstaller
```

2. Build server executable:
```bash
pyinstaller --onefile --name "P2W-Server" server.py
```

3. Build client executable (GUI mode):
```bash
pyinstaller --onefile --name "P2W-Client" --windowed client.py
```

4. Output will appear in the `dist/` folder.

---

## Usage

### Server Setup

1. Run server → pick a port (default: 5555)
2. Server Generates [server_config.json](#server-serverpy) you can edit this if needed.
3. Server prints live stats every 5 seconds  
4. Leaderboard auto-saves to `winners_[port].json`  
5. Tracks players, pings, uptime, etc.

### Port Forwarding (for public hosting)

- Protocol: TCP  
- External Port: your chosen port  
- Internal IP: your server’s ip address  
- Internal Port: same as external  

### Client Usage

1. Launch the client  
2. Enter your username  
3. Enter server IP + port  
4. Click **Connect**
5. Client Generates [p2w_config.json](#client-clientpy) which saves your username, and the last server you connected to.
6. Click **PING** to attempt to win  
7. View leaderboard  
8. Disconnect to switch servers  

---

## Configuration

### Server (`server.py`)
- This is now the server_config.json file when you run the server once.

```
{
  "rate_limit_enabled": true,
  "rate_limit_seconds": 10,
  "max_connections": 1000,
  "backup_interval_seconds": 300,
  "player_timeout_seconds": 30,
  "max_username_length": 32,
  "stats_display_interval": 4
}
```

### Client (`client.py`)
- This is now the p2w_config.json file when you run the client once.

```
{"last_ip": "localhost", "last_port": "5555", "last_username": "user"}
```

---

## File Structure

```
p2w/
├── server.py              # Server application
├── client.py              # Client application (tkinter GUI)
├── winners_[port].json    # Auto-generated leaderboard file
├── LICENSE                # GPL-3.0 License
└── README.md              # This file
```

---

## Troubleshooting

**Server won't start**  
- Port already in use  
- Try a different port  
- Use administrator rights for ports <1024  

**Client cannot connect**  
- Server not running  
- Firewall blocking connection  
- Wrong IP/port  
- Test with `localhost` first  

**Rate limited**  
- Wait 10 seconds  
- Each IP has its own cooldown  

**Leaderboard not loading**  
- Ensure server is running  
- Check network connection  
- Verify JSON file exists + valid  

---

## Contributing

You are welcome to:  
- Report bugs  
- Suggest features  
- Submit PRs  
- Improve documentation  

Please keep the minimalist vibe of the project.

---

## License

Licensed under **GPL-3.0**.  
You may use, modify, share, and fork the project, but all derivative works must stay open source.

---

## Credits

Created by [kroefer1](https://github.com/kroefer1)  
Built with Python and way too much free time.

---

## To-Do

- [ ] Make Linux, macOS, Web, and Android clients  
- [ ] Allow more than 100 leaderboard entries  
- [ ] Anti-botting (server)  
- [ ] Do something (placeholder)  
- [X] Stress test tool  
- [X] UI tweaks  
- [X] Improved server security  

---

## FAQ

**Q: Why?**  
A: I was bored, had an idea, and it spiraled.

**Q: Can I host a public server?**  
A: Yes — just port forward.

**Q: Max players?**  
A: Stress tested to around 50k (limited by single-machine testing).  
Multiple users on different IPs = even more.

**Q: Can I modify the game?**  
A: Yes — follow GPL-3.0.

**Q: Will you add my feature?**  
A: Very likely. Open an issue or PR.

---

## Support

For issues or suggestions, open an issue on GitHub.
