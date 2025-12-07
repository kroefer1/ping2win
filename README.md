# P2W (Ping 2 Win)

A ridiculously simple multiplayer game where the goal is to ping a server.  
The first person to successfully ping wins. That's literally the whole game.

---

## Table of Contents

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

## Troubleshooting

**Server won't start**  
- Port already in use  
- Try a different port  
- Use administrator rights for ports <1024  

**Client cannot connect**  
- Server not running
- Firewall blocking connection
- Wrong IP/port

**Rate limited**  
- Wait 10 seconds  
- Each IP has its own cooldown  

**Leaderboard not loading**  
- Ensure server is running  
- Check network connection  
- Verify JSON file exists + valid (if you do not have access to the server's Leaderboard json, contact the server administrator)

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
- [ ] Add a Serverlist
- [ ] Make Linux, macOS, Web, and Android clients  
- [ ] Add Ability to read more then 100 Leaderboard Entries (the json file can store over 100 entries but the client is capped at 100 entries, and i wanna change that)
- [ ] Anti-botting (server)
- [X] Move most of the stuff in this README into the [Wiki](https://github.com/kroefer1/ping2win/wiki)
- [X] Stress test tool  
- [X] UI tweaks  
- [X] Improved server security  

---

## Support

For issues or suggestions, open an issue on GitHub.
