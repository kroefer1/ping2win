import socket
import json
import threading
import time
import re
import shutil
from os import system, path
from datetime import datetime
from collections import deque

class P2WServer:
    def __init__(self, port=5555):
        self.port = port
        self.config_file = "server_config.json"
        self.load_config()
        
        self.winners = []
        self.winners_file = f"winners_{port}.json"
        self.connected_players = {}
        self.ip_last_ping = {}
        self.ip_blacklist = set()
        self.total_pings = 0
        self.total_connections = 0
        self.server_start_time = time.time()
        self.lock = threading.RLock()
        self.last_backup = time.time()
        
        self.connection_semaphore = threading.Semaphore(self.config['max_connections'])
        self.rate_limit_window = deque(maxlen=10000)
        
        # Write queue to prevent JSON corruption
        self.save_queue = []
        self.save_lock = threading.Lock()
        self.save_pending = False
        
        self.load_winners()
        self.load_blacklist()
        
        threading.Thread(target=self.display_stats, daemon=True).start()
        threading.Thread(target=self.auto_backup, daemon=True).start()
        threading.Thread(target=self.cleanup_old_connections, daemon=True).start()
        threading.Thread(target=self.cleanup_inactive_players, daemon=True).start()
        threading.Thread(target=self.process_save_queue, daemon=True).start()
    
    def load_config(self):
        default_config = {
            "rate_limit_enabled": True,
            "rate_limit_seconds": 10,
            "max_connections": 1000,
            "backup_interval_seconds": 300,
            "player_timeout_seconds": 30,
            "max_username_length": 32,
            "stats_display_interval": 4
        }
        
        if path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    self.config = json.load(f)
                for key, value in default_config.items():
                    if key not in self.config:
                        self.config[key] = value
                print(f"Loaded config from {self.config_file}")
            except:
                print(f"Error loading config, using defaults")
                self.config = default_config
        else:
            self.config = default_config
            self.save_config()
            print(f"Created default config at {self.config_file}")
    
    def save_config(self):
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            print(f"Error saving config: {e}")
        
    def load_winners(self):
        try:
            with open(self.winners_file, 'r') as f:
                data = json.load(f)
                self.winners = data.get('winners', [])
                self.total_pings = data.get('total_pings', 0)
        except FileNotFoundError:
            self.winners = []
            self.total_pings = 0
        except json.JSONDecodeError:
            print(f"ERROR: Corrupted winners file. Creating backup...")
            try:
                shutil.copy(self.winners_file, f"{self.winners_file}.corrupted")
            except:
                pass
            self.winners = []
            self.total_pings = 0
    
    def save_winners(self):
        """Queue a save operation instead of writing directly"""
        with self.save_lock:
            if not self.save_pending:
                self.save_pending = True
                self.save_queue.append(time.time())
    
    def process_save_queue(self):
        """Process save queue - only one write at a time"""
        while True:
            time.sleep(0.1)  # Check queue every 100ms
            
            with self.save_lock:
                if self.save_pending:
                    self.save_pending = False
                    self.save_queue.clear()
                else:
                    continue
            
            # Actually write to file (outside lock so we don't block queue)
            try:
                with self.lock:
                    temp_file = f"{self.winners_file}.tmp"
                    with open(temp_file, 'w') as f:
                        json.dump({
                            'winners': self.winners,
                            'total_pings': self.total_pings
                        }, f, indent=2)
                    shutil.move(temp_file, self.winners_file)
            except Exception as e:
                print(f"ERROR saving winners: {e}")
    
    def load_blacklist(self):
        try:
            with open('blacklist.txt', 'r') as f:
                self.ip_blacklist = set(line.strip() for line in f if line.strip())
        except FileNotFoundError:
            self.ip_blacklist = set()
    
    def save_blacklist(self):
        with open('blacklist.txt', 'w') as f:
            for ip in self.ip_blacklist:
                f.write(f"{ip}\n")
    
    def auto_backup(self):
        while True:
            time.sleep(60)
            if time.time() - self.last_backup >= self.config['backup_interval_seconds']:
                self.backup_data()
                self.last_backup = time.time()
    
    def backup_data(self):
        try:
            backup_file = f"backup_{self.port}_{int(time.time())}.json"
            shutil.copy(self.winners_file, backup_file)
            print(f"Backup created: {backup_file}")
        except Exception as e:
            print(f"ERROR during backup: {e}")
    
    def cleanup_old_connections(self):
        while True:
            time.sleep(60)
            current_time = time.time()
            with self.lock:
                expired = [ip for ip, ts in self.ip_last_ping.items() 
                          if current_time - ts > 60]
                for ip in expired:
                    del self.ip_last_ping[ip]
    
    def cleanup_inactive_players(self):
        while True:
            time.sleep(10)
            current_time = time.time()
            with self.lock:
                inactive = [user for user, ts in self.connected_players.items() 
                           if current_time - ts > self.config['player_timeout_seconds']]
                for user in inactive:
                    del self.connected_players[user]
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] {user} removed (inactive)")
    
    def validate_username(self, username):
        if not username or len(username) > self.config['max_username_length']:
            return False
        if not re.match(r'^[a-zA-Z0-9_-]+$', username):
            return False
        return True
    
    def check_rate_limit(self, ip):
        current_time = time.time()
        with self.lock:
            if ip in self.ip_last_ping:
                time_since_last = current_time - self.ip_last_ping[ip]
                if time_since_last < self.config['rate_limit_seconds']:
                    return False, self.config['rate_limit_seconds'] - time_since_last
        return True, 0
    
    def handle_client(self, conn, addr):
        self.connection_semaphore.acquire()
        try:
            if addr[0] in self.ip_blacklist:
                conn.send("BLACKLISTED".encode('utf-8'))
                return
            
            conn.settimeout(5)
            data = conn.recv(1024).decode('utf-8', errors='ignore').strip()
            
            if not data:
                return
            
            self.total_connections += 1
            
            if data == "GET_STATS":
                with self.lock:
                    stats = {
                        'total_winners': len(self.winners),
                        'online_players': len(self.connected_players),
                        'total_pings': self.total_pings,
                        'uptime': int(time.time() - self.server_start_time),
                        'total_connections': self.total_connections
                    }
                conn.send(json.dumps(stats).encode('utf-8'))
                return
            
            elif data == "GET_LEADERBOARD":
                with self.lock:
                    leaderboard = {'winners': self.winners[:100]}
                conn.send(json.dumps(leaderboard).encode('utf-8'))
                return
            
            elif data.startswith("CONNECT:"):
                username = data.split("CONNECT:", 1)[1].strip()
                
                if not self.validate_username(username):
                    conn.send("INVALID_USERNAME".encode('utf-8'))
                    return
                
                with self.lock:
                    self.connected_players[username] = time.time()
                print(f"[{datetime.now().strftime('%H:%M:%S')}] {username} connected from {addr[0]}")
                conn.send("CONNECTED".encode('utf-8'))
                return
            
            elif data.startswith("HEARTBEAT:"):
                username = data.split("HEARTBEAT:", 1)[1].strip()
                with self.lock:
                    if username in self.connected_players:
                        self.connected_players[username] = time.time()
                conn.send("OK".encode('utf-8'))
                return
            
            elif data.startswith("DISCONNECT:"):
                username = data.split("DISCONNECT:", 1)[1].strip()
                with self.lock:
                    self.connected_players.pop(username, None)
                print(f"[{datetime.now().strftime('%H:%M:%S')}] {username} disconnected")
                conn.send("DISCONNECTED".encode('utf-8'))
                return
            
            elif data.startswith("P2W_PING:"):
                if self.config['rate_limit_enabled']:
                    can_ping, wait_time = self.check_rate_limit(addr[0])
                    if not can_ping:
                        response = f"RATE_LIMITED:{wait_time:.1f}"
                        conn.send(response.encode('utf-8'))
                        return
                
                parts = data.split("P2W_PING:", 1)[1].split("|")
                username = parts[0].strip()
                
                if not self.validate_username(username):
                    conn.send("INVALID_USERNAME".encode('utf-8'))
                    return
                
                try:
                    latency = float(parts[1]) if len(parts) > 1 else 0
                except (ValueError, IndexError):
                    latency = 0
                
                with self.lock:
                    self.ip_last_ping[addr[0]] = time.time()
                    self.total_pings += 1
                    
                    if username in [w['username'] for w in self.winners]:
                        response = "ALREADY_WON"
                    else:
                        rank = len(self.winners) + 1
                        
                        winner_data = {
                            'username': username,
                            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                            'ip': addr[0],
                            'rank': rank,
                            'latency': f"{latency:.2f}ms"
                        }
                        self.winners.append(winner_data)
                        response = f"WIN:{rank}"
                        print(f"[{datetime.now().strftime('%H:%M:%S')}] NEW WINNER #{rank}: {username} ({latency:.2f}ms)")
                
                # Queue save instead of async thread
                self.save_winners()
                conn.send(response.encode('utf-8'))
                return
            
            else:
                conn.send("INVALID_REQUEST".encode('utf-8'))
                
        except socket.timeout:
            pass
        except Exception as e:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] ERROR: {e}")
        finally:
            try:
                conn.close()
            except:
                pass
            self.connection_semaphore.release()
    
    def display_stats(self):
        while True:
            time.sleep(self.config['stats_display_interval'])
            system("clear||cls")
            print(f"\n{'='*60}")
            print(f"P2W Server Stats - {datetime.now().strftime('%H:%M:%S')}")
            print(f"{'='*60}")
            with self.lock:
                print(f"Port: {self.port}")
                print(f"Rate Limiting: {'ENABLED' if self.config['rate_limit_enabled'] else 'DISABLED'}")
                print(f"Total Winners: {len(self.winners)}")
                print(f"Players Online: {len(self.connected_players)}")
                print(f"Total Pings: {self.total_pings}")
                print(f"Total Connections: {self.total_connections}")
                print(f"Active Workers: {self.config['max_connections'] - self.connection_semaphore._value}")
                uptime = int(time.time() - self.server_start_time)
                print(f"Uptime: {uptime // 3600}h {(uptime % 3600) // 60}m {uptime % 60}s")
                if self.connected_players:
                    players = ', '.join(list(self.connected_players.keys())[:10])
                    if len(self.connected_players) > 10:
                        players += f" (+{len(self.connected_players) - 10} more)"
                    print(f"Online: {players}")
                print(f"Blacklisted IPs: {len(self.ip_blacklist)}")
            print(f"{'='*60}")
            print(f"Edit server_config.json to change settings")
            print(f"{'='*60}\n")

    def start(self):
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
        server.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        
        try:
            server.bind(('0.0.0.0', self.port))
            server.listen(1000)
            print(f"P2W Server started on port {self.port}")
            print(f"Max concurrent connections: {self.config['max_connections']}")
            print(f"Rate limiting: {'ENABLED' if self.config['rate_limit_enabled'] else 'DISABLED'}")
            if self.config['rate_limit_enabled']:
                print(f"Rate limit: 1 ping per {self.config['rate_limit_seconds']} seconds")
            print(f"Security: Username validation, IP blacklist")
            print(f"\nEdit server_config.json to change settings\n")

            while True:
                try:
                    conn, addr = server.accept()
                    thread = threading.Thread(target=self.handle_client, args=(conn, addr))
                    thread.daemon = True
                    thread.start()
                except Exception as e:
                    print(f"Accept error: {e}")
                    
        except KeyboardInterrupt:
            print("\nServer shutting down...")
            self.backup_data()
        finally:
            server.close()

if __name__ == "__main__":
    print("=== P2W (Ping 2 Win) Server ===\n")
    
    port = input("Enter port (default 5555): ").strip()
    port = int(port) if port else 5555
    
    server = P2WServer(port)
    server.start()