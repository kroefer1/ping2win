import socket
import threading
import time
import random
import string

class StressTest:
    def __init__(self, server_ip, server_port, num_clients=1000):
        self.server_ip = server_ip
        self.server_port = server_port
        self.num_clients = num_clients
        self.successful = 0
        self.failed = 0
        self.timeouts = 0
        self.rate_limited = 0
        self.lock = threading.Lock()
        self.start_time = None
        
    def generate_username(self):
        """Generate random username"""
        return ''.join(random.choices(string.ascii_letters + string.digits, k=random.randint(5, 15)))
    
    def send_ping(self, client_id):
        """Simulate a client pinging the server"""
        username = f"stress_test_{client_id}"
        
        try:
            # Connect
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client.settimeout(5)
            client.connect((self.server_ip, self.server_port))
            
            # Send CONNECT
            client.send(f"CONNECT:{username}".encode('utf-8'))
            response = client.recv(1024).decode('utf-8')
            client.close()
            
            if response != "CONNECTED":
                with self.lock:
                    self.failed += 1
                return
            
            # Send a heartbeat to keep connection alive
            try:
                hb_client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                hb_client.settimeout(2)
                hb_client.connect((self.server_ip, self.server_port))
                hb_client.send(f"HEARTBEAT:{username}".encode('utf-8'))
                hb_client.recv(1024)
                hb_client.close()
            except:
                pass
            
            # Small delay to simulate real usage
            time.sleep(random.uniform(0.01, 0.1))
            
            # Send PING
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client.settimeout(5)
            client.connect((self.server_ip, self.server_port))
            
            latency = random.uniform(10, 100)
            client.send(f"P2W_PING:{username}|{latency}".encode('utf-8'))
            response = client.recv(1024).decode('utf-8')
            client.close()
            
            # Send DISCONNECT
            try:
                client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                client.settimeout(2)
                client.connect((self.server_ip, self.server_port))
                client.send(f"DISCONNECT:{username}".encode('utf-8'))
                client.recv(1024)
                client.close()
            except:
                pass
            
            with self.lock:
                if response.startswith("WIN:") or response == "ALREADY_WON":
                    self.successful += 1
                elif response.startswith("RATE_LIMITED:"):
                    self.rate_limited += 1
                else:
                    self.failed += 1
                    
        except socket.timeout:
            with self.lock:
                self.timeouts += 1
        except Exception as e:
            with self.lock:
                self.failed += 1
    
    def stress_test_connect(self, client_id):
        """Test just connections"""
        username = f"connect_test_{client_id}"
        try:
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client.settimeout(3)
            client.connect((self.server_ip, self.server_port))
            client.send(f"CONNECT:{username}".encode('utf-8'))
            response = client.recv(1024).decode('utf-8')
            client.close()
            
            with self.lock:
                if response == "CONNECTED":
                    self.successful += 1
                else:
                    self.failed += 1
            
            # Send DISCONNECT
            try:
                client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                client.settimeout(2)
                client.connect((self.server_ip, self.server_port))
                client.send(f"DISCONNECT:{username}".encode('utf-8'))
                client.recv(1024)
                client.close()
            except:
                pass
        except socket.timeout:
            with self.lock:
                self.timeouts += 1
        except:
            with self.lock:
                self.failed += 1
    
    def stress_test_leaderboard(self):
        """Stress test leaderboard requests"""
        try:
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client.settimeout(3)
            client.connect((self.server_ip, self.server_port))
            client.send("GET_LEADERBOARD".encode('utf-8'))
            response = client.recv(4096).decode('utf-8')
            client.close()
            
            with self.lock:
                if response:
                    self.successful += 1
                else:
                    self.failed += 1
        except socket.timeout:
            with self.lock:
                self.timeouts += 1
        except:
            with self.lock:
                self.failed += 1
    
    def display_progress(self):
        """Display progress during test"""
        while self.running:
            with self.lock:
                elapsed = time.time() - self.start_time
                total = self.successful + self.failed + self.timeouts + self.rate_limited
                print(f"\r[{elapsed:.1f}s] Progress: {total}/{self.num_clients} | Success: {self.successful} | Failed: {self.failed} | Timeout: {self.timeouts} | Rate Limited: {self.rate_limited}", end='')
            time.sleep(0.5)
    
    def run_full_test(self):
        """Run full ping test"""
        print(f"\n{'='*60}")
        print(f"FULL STRESS TEST - Simulating {self.num_clients} players")
        print(f"Server: {self.server_ip}:{self.server_port}")
        print(f"{'='*60}\n")
        
        self.successful = 0
        self.failed = 0
        self.timeouts = 0
        self.rate_limited = 0
        self.start_time = time.time()
        self.running = True
        
        # Start progress display
        progress_thread = threading.Thread(target=self.display_progress, daemon=True)
        progress_thread.start()
        
        # Create threads
        threads = []
        for i in range(self.num_clients):
            t = threading.Thread(target=self.send_ping, args=(i,))
            threads.append(t)
            t.start()
            
            # Stagger starts slightly to avoid overwhelming instantly
            if i % 50 == 0:
                time.sleep(0.1)
        
        # Wait for all threads
        for t in threads:
            t.join()
        
        self.running = False
        elapsed = time.time() - self.start_time
        
        print(f"\n\n{'='*60}")
        print(f"RESULTS")
        print(f"{'='*60}")
        print(f"Total Clients: {self.num_clients}")
        print(f"Successful: {self.successful}")
        print(f"Failed: {self.failed}")
        print(f"Timeouts: {self.timeouts}")
        print(f"Rate Limited: {self.rate_limited}")
        print(f"Time Taken: {elapsed:.2f}s")
        print(f"Requests/sec: {self.num_clients/elapsed:.2f}")
        print(f"Success Rate: {(self.successful/self.num_clients)*100:.1f}%")
        print(f"{'='*60}\n")
    
    def run_connection_test(self):
        """Test rapid connections"""
        print(f"\n{'='*60}")
        print(f"CONNECTION STRESS TEST - {self.num_clients} connections")
        print(f"Server: {self.server_ip}:{self.server_port}")
        print(f"{'='*60}\n")
        
        self.successful = 0
        self.failed = 0
        self.timeouts = 0
        self.start_time = time.time()
        self.running = True
        
        progress_thread = threading.Thread(target=self.display_progress, daemon=True)
        progress_thread.start()
        
        threads = []
        for i in range(self.num_clients):
            t = threading.Thread(target=self.stress_test_connect, args=(i,))
            threads.append(t)
            t.start()
            
            if i % 100 == 0:
                time.sleep(0.05)
        
        for t in threads:
            t.join()
        
        self.running = False
        elapsed = time.time() - self.start_time
        
        print(f"\n\n{'='*60}")
        print(f"CONNECTION TEST RESULTS")
        print(f"{'='*60}")
        print(f"Total Connections: {self.num_clients}")
        print(f"Successful: {self.successful}")
        print(f"Failed: {self.failed}")
        print(f"Timeouts: {self.timeouts}")
        print(f"Time Taken: {elapsed:.2f}s")
        print(f"Connections/sec: {self.num_clients/elapsed:.2f}")
        print(f"Success Rate: {(self.successful/self.num_clients)*100:.1f}%")
        print(f"{'='*60}\n")
    
    def run_leaderboard_test(self, num_requests=500):
        """Spam leaderboard requests"""
        print(f"\n{'='*60}")
        print(f"LEADERBOARD STRESS TEST - {num_requests} requests")
        print(f"Server: {self.server_ip}:{self.server_port}")
        print(f"{'='*60}\n")
        
        self.successful = 0
        self.failed = 0
        self.timeouts = 0
        self.num_clients = num_requests
        self.start_time = time.time()
        self.running = True
        
        progress_thread = threading.Thread(target=self.display_progress, daemon=True)
        progress_thread.start()
        
        threads = []
        for i in range(num_requests):
            t = threading.Thread(target=self.stress_test_leaderboard)
            threads.append(t)
            t.start()
            
            if i % 50 == 0:
                time.sleep(0.05)
        
        for t in threads:
            t.join()
        
        self.running = False
        elapsed = time.time() - self.start_time
        
        print(f"\n\n{'='*60}")
        print(f"LEADERBOARD TEST RESULTS")
        print(f"{'='*60}")
        print(f"Total Requests: {num_requests}")
        print(f"Successful: {self.successful}")
        print(f"Failed: {self.failed}")
        print(f"Timeouts: {self.timeouts}")
        print(f"Time Taken: {elapsed:.2f}s")
        print(f"Requests/sec: {num_requests/elapsed:.2f}")
        print(f"Success Rate: {(self.successful/num_requests)*100:.1f}%")
        print(f"{'='*60}\n")

if __name__ == "__main__":
    print("=== P2W Server Stress Test Tool ===\n")
    
    server_ip = input("Server IP (default: localhost): ").strip() or "localhost"
    server_port = input("Server Port (default: 5555): ").strip() or "5555"
    
    print("\nSelect test type:")
    print("1. Full Test (Connect + Ping)")
    print("2. Connection Test Only")
    print("3. Leaderboard Spam Test")
    print("4. All Tests")
    
    test_type = input("\nChoice (1-4): ").strip()
    
    if test_type in ['1', '2', '4']:
        num_clients = input("Number of clients (default: 1000): ").strip()
        num_clients = int(num_clients) if num_clients else 1000
    else:
        num_clients = 1000
    
    tester = StressTest(server_ip, int(server_port), num_clients)
    
    print("\nStarting stress test in 3 seconds...")
    time.sleep(3)
    
    if test_type == '1':
        tester.run_full_test()
    elif test_type == '2':
        tester.run_connection_test()
    elif test_type == '3':
        num_req = input("Number of leaderboard requests (default: 500): ").strip()
        num_req = int(num_req) if num_req else 500
        tester.run_leaderboard_test(num_req)
    elif test_type == '4':
        print("\n>>> Running ALL TESTS <<<\n")
        tester.run_connection_test()
        time.sleep(2)
        tester.run_full_test()
        time.sleep(2)
        tester.run_leaderboard_test(500)
    else:
        print("Invalid choice!")
    
    print("\nStress test complete!")