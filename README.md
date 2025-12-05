# P2W (Ping 2 Win)

A ridiculously simple multiplayer game where the objective is to ping a server. First person to successfully ping wins. That's it.

## What is this?

P2W is a lightweight client-server game built in Python. Players connect to a server, and the first one to send a ping wins. Each player can only win once per server, and all winners are tracked on a persistent leaderboard.

## Features

- **Minimalist gameplay**: Click a button to ping the server and win
- **Live statistics**: Real-time display of online players, total winners, and server uptime
- **Persistent leaderboard**: All winners are saved with timestamps and latency measurements
- **Rate limiting**: IP-based rate limiting (1 ping per 10 seconds) to prevent spam
- **Latency tracking**: Measures and displays connection latency for each player
- **Low resource usage**: Server runs on approximately 10MB of RAM
- **Cross-platform**: Works on Windows, Linux, and macOS

## Screenshots

*Coming soon*

## Requirements

- Python 3.7 or higher
- tkinter (usually included with Python)
- Standard library modules: socket, json, threading, time

## Installation

### Running from Source

1. Clone this repository:
```bash
git clone https://github.com/yourusername/p2w.git
cd p2w
```

2. No additional dependencies needed - uses only Python standard library

3. Start the server:
```bash
python server.py
```

4. Run the client:
```bash
python client.py
```

### Building Standalone Executables

To create standalone .exe files that don't require Python installation:

1. Install PyInstaller:
```bash
pip install pyinstaller
```

2. Build the server executable:
```bash
pyinstaller --onefile --name "P2W-Server" server.py
```

3. Build the client executable (with GUI, no console):
```bash
pyinstaller --onefile --name "P2W-Client" --windowed client.py
```

4. Find your executables in the `dist/` folder

Optional: Add a custom icon:
```bash
pyinstaller --onefile --icon=icon.ico --name "P2W-Client" --windowed client.py
```

## Usage

### Server Setup

1. Run the server and choose a port (default: 5555)
2. The server will display live statistics every 5 seconds
3. Winners are automatically saved to `winners_[port].json`
4. Server tracks connected players, total pings, and uptime

### Port Forwarding (for public servers)

If hosting publicly, you'll need to forward the port on your router:

**Router Configuration:**
- Protocol: TCP
- External Port: Your chosen port
- Internal IP: Your server's local IP
- Internal Port: Same as external port

**Windows Port Forwarding (if running behind another machine):**
```bash
netsh interface portproxy add v4tov4 listenport=6969 listenaddress=0.0.0.0 connectport=6969 connectaddress=192.168.x.x
```

### Client Usage

1. Launch the client
2. Enter your username
3. Enter the server IP and port
   - For local testing: `localhost` or `127.0.0.1`
   - For LAN: Server's local IP (e.g., `192.168.1.100`)
   - For internet: Server's public IP or domain
4. Click "Connect"
5. Click "PING" to attempt to win
6. View the leaderboard to see all winners
7. Use "Disconnect" to switch servers

## How It Works

### Server
- Listens for TCP connections on specified port
- Handles multiple request types: connection, ping, stats, leaderboard
- Implements IP-based rate limiting (10 second cooldown)
- Stores winner data in JSON format with rank, timestamp, and latency
- Multi-threaded to handle concurrent connections

### Client
- GUI built with tkinter
- Measures connection latency to server
- Updates live statistics every 3 seconds
- Tracks connection state and prevents multiple pings
- Displays leaderboard with sortable columns

### Protocol

The client-server communication uses simple text-based messages:
- `CONNECT:[username]` - Register connection
- `P2W_PING:[username]|[latency]` - Attempt to win
- `GET_STATS` - Request server statistics
- `GET_LEADERBOARD` - Request winner list
- `DISCONNECT:[username]` - Unregister connection

## Configuration

### Server
Edit these variables in `server.py`:
- Default port: Line with `port = int(port) if port else 5555`
- Rate limit duration: Line with `if time_since_last < 10`
- Stats update interval: Line with `time.sleep(5)`

### Client
Edit these variables in `client.py`:
- Default window size: `self.root.geometry("500x600")`
- Stats update interval: Line with `time.sleep(3)`
- Connection timeout: `client.settimeout(5)`

## File Structure

```
p2w/
├── server.py              # Server application
├── client.py              # Client application with GUI
├── winners_[port].json    # Auto-generated winner database
├── LICENSE               # GPL-3.0 License
└── README.md             # This file
```

## Troubleshooting

**Server won't start:**
- Check if the port is already in use
- Try a different port number
- Run with administrator privileges if using ports below 1024

**Client can't connect:**
- Verify server is running
- Check firewall settings on both client and server
- Confirm correct IP address and port
- Test with `localhost` first for local debugging

**Rate limited:**
- Wait 10 seconds between ping attempts
- Each IP address has its own cooldown timer

**Leaderboard won't load:**
- Ensure server is running and accessible
- Check network connectivity
- Verify `winners_[port].json` exists and is valid JSON

## Contributing

Contributions are welcome! Feel free to:
- Report bugs
- Suggest new features
- Submit pull requests
- Improve documentation

Please maintain the minimalist spirit of the project.

## License

This project is licensed under the GNU General Public License v3.0 - see the [LICENSE](LICENSE) file for details.

This means you can freely use, modify, and distribute this software, but any derivative works must also be open source under GPL-3.0.

## Credits

Created by [Your Name/Username]

Built with Python and way too much free time.

## Roadmap

Potential future features:
- Web-based client interface
- Multiple game modes
- Achievement system
- Team-based gameplay
- Docker containerization
- REST API for server stats

## FAQ

**Q: Why?**  
A: Why not?

**Q: Can I host a public server?**  
A: Yes! Just forward the port and share your IP/domain.

**Q: How many players can the server handle?**  
A: Theoretically thousands, though it hasn't been stress-tested at scale.

**Q: Can I modify the game?**  
A: Absolutely! Just follow the GPL-3.0 license terms.

**Q: Will you add [feature]?**  
A: Maybe! Open an issue or submit a PR.

## Support

For issues, questions, or suggestions, please open an issue on GitHub.

---

**P2W - Because sometimes the simplest ideas are the most fun.**
