import socket
import json
import threading
import time
from os import system
from datetime import datetime

class P2WServer:
    def __init__(self, port=5555):
        self.port = port
        self.winners = []
        self.winners_file = f"winners_{port}.json"
        self.connected_players = set()
        self.ip_last_ping = {}  # IP rate limiting
        self.total_pings = 0
        self.server_start_time = time.time()
        self.load_winners()
        
        # Start stats display thread
        threading.Thread(target=self.display_stats, daemon=True).start()
        
    def load_winners(self):
        try:
            with open(self.winners_file, 'r') as f:
                data = json.load(f)
                self.winners = data.get('winners', [])
                self.total_pings = data.get('total_pings', 0)
        except FileNotFoundError:
            self.winners = []
            self.total_pings = 0
    
    def save_winners(self):
        with open(self.winners_file, 'w') as f:
            json.dump({
                'winners': self.winners,
                'total_pings': self.total_pings
            }, f, indent=2)
    
    def check_rate_limit(self, ip):
        current_time = time.time()
        if ip in self.ip_last_ping:
            time_since_last = current_time - self.ip_last_ping[ip]
            if time_since_last < 10:
                return False, 10 - time_since_last
        return True, 0
    
    def handle_client(self, conn, addr):
        try:
            data = conn.recv(1024).decode('utf-8')
            
            # Handle different request types
            if data == "GET_STATS":
                stats = {
                    'total_winners': len(self.winners),
                    'online_players': len(self.connected_players),
                    'total_pings': self.total_pings,
                    'uptime': int(time.time() - self.server_start_time)
                }
                conn.send(json.dumps(stats).encode('utf-8'))
                return
            
            elif data == "GET_LEADERBOARD":
                leaderboard = {
                    'winners': self.winners[:100]  # Top 100
                }
                conn.send(json.dumps(leaderboard).encode('utf-8'))
                return
            
            elif data.startswith("CONNECT:"):
                username = data.split("CONNECT:")[1].strip()
                self.connected_players.add(username)
                print(f"{username} connected from {addr[0]}")
                conn.send("CONNECTED".encode('utf-8'))
                return
            
            elif data.startswith("DISCONNECT:"):
                username = data.split("DISCONNECT:")[1].strip()
                self.connected_players.discard(username)
                print(f"{username} disconnected")
                conn.send("DISCONNECTED".encode('utf-8'))
                return
            
            elif data.startswith("P2W_PING:"):
                # Rate limiting check
                can_ping, wait_time = self.check_rate_limit(addr[0])
                if not can_ping:
                    response = f"RATE_LIMITED:{wait_time:.1f}"
                    conn.send(response.encode('utf-8'))
                    return
                
                # Update rate limit
                self.ip_last_ping[addr[0]] = time.time()
                self.total_pings += 1
                
                parts = data.split("P2W_PING:")[1].split("|")
                username = parts[0].strip()
                latency = float(parts[1]) if len(parts) > 1 else 0
                
                # Check if user already won
                if username in [w['username'] for w in self.winners]:
                    response = "ALREADY_WON"
                else:
                    # Calculate rank
                    rank = len(self.winners) + 1
                    
                    # Add winner
                    winner_data = {
                        'username': username,
                        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        'ip': addr[0],
                        'rank': rank,
                        'latency': f"{latency:.2f}ms"
                    }
                    self.winners.append(winner_data)
                    self.save_winners()
                    response = f"WIN:{rank}"
                    print(f"NEW WINNER #{rank}: {username} from {addr[0]} (Latency: {latency:.2f}ms)")
                
                conn.send(response.encode('utf-8'))
                return
            
            else:
                conn.send("INVALID_REQUEST".encode('utf-8'))
                
        except Exception as e:
            print(f"Error handling client: {e}")
        finally:
            conn.close()
    
    def display_stats(self):
        while True:
            time.sleep(4)
            system("clear||cls")
            print(f"\n{'='*50}")
            print(f"Server Stats - {datetime.now().strftime('%H:%M:%S')}")
            print(f"{'='*50}")
            print(f"Total Winners: {len(self.winners)}")
            print(f"Players Online: {len(self.connected_players)}")
            print(f"Total Pings: {self.total_pings}")
            uptime = int(time.time() - self.server_start_time)
            print(f"Uptime: {uptime // 3600}h {(uptime % 3600) // 60}m {uptime % 60}s")
            if self.connected_players:
                print(f"Online: {', '.join(list(self.connected_players)[:5])}")
            print(f"{'='*50}\n")

    def start(self):
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        try:
            server.bind(('0.0.0.0', self.port))
            server.listen(10)
            print(f"P2W Server started on port {self.port}")

            while True:
                conn, addr = server.accept()
                thread = threading.Thread(target=self.handle_client, args=(conn, addr))
                thread.daemon = True
                thread.start()
        except KeyboardInterrupt:
            print("\nServer shutting down...")
        finally:
            server.close()

if __name__ == "__main__":
    print("=== P2W (Ping 2 Win) Server ===\n")
    
    port = input("Enter port (default 5555): ").strip()
    port = int(port) if port else 5555
    
    server = P2WServer(port)
    server.start()