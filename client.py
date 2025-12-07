import tkinter as tk
from tkinter import messagebox, ttk
import socket
import json
import time
import threading
import os

class P2WClient:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("P2W - Ping 2 Win")
        self.root.geometry("500x600")
        self.root.resizable(False, False)
        
        self.username = ""
        self.server_ip = ""
        self.server_port = ""
        self.has_pinged = False
        self.is_connected = False
        self.stats = {}
        self.config_file = "p2w_config.json"
        self.stats_thread = None
        self.heartbeat_thread = None
        self.connection_status = "disconnected"
        
        self.load_config()
        self.setup_shortcuts()
        self.show_connection_screen()
        
    def load_config(self):
        """Load last used server settings"""
        try:
            with open(self.config_file, 'r') as f:
                config = json.load(f)
                self.last_ip = config.get('last_ip', 'localhost')
                self.last_port = config.get('last_port', '5555')
                self.last_username = config.get('last_username', '')
        except:
            self.last_ip = 'localhost'
            self.last_port = '5555'
            self.last_username = ''
    
    def save_config(self):
        """Save server settings for next time"""
        try:
            config = {
                'last_ip': self.server_ip,
                'last_port': self.server_port,
                'last_username': self.username
            }
            with open(self.config_file, 'w') as f:
                json.dump(config, f)
        except:
            pass
    
    def setup_shortcuts(self):
        """Setup keyboard shortcuts"""
        self.root.bind('<Return>', lambda e: self.handle_enter_key())
        self.root.bind('<space>', lambda e: self.handle_space_key())
    
    def handle_enter_key(self):
        if not self.is_connected:
            self.connect_to_server()
    
    def handle_space_key(self):
        if self.is_connected and not self.has_pinged:
            self.ping_server()
    
    def send_request(self, message, timeout=5):
        """Helper to send requests to server with proper error handling"""
        try:
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client.settimeout(timeout)
            client.connect((self.server_ip, int(self.server_port)))
            client.send(message.encode('utf-8'))
            
            # Read ALL data until connection closes
            response_data = b''
            while True:
                chunk = client.recv(4096)
                if not chunk:
                    break
                response_data += chunk
            
            client.close()
            return response_data.decode('utf-8', errors='ignore')
        except socket.timeout:
            return "TIMEOUT"
        except ConnectionRefusedError:
            return "REFUSED"
        except socket.gaierror:
            return "DNS_ERROR"
        except Exception as e:
            return f"ERROR:{str(e)}"
    
    def measure_latency(self):
        """Measure ping latency to server"""
        try:
            start = time.time()
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client.settimeout(2)
            client.connect((self.server_ip, int(self.server_port)))
            client.close()
            latency = (time.time() - start) * 1000
            return latency
        except:
            return 0
    
    def update_stats(self):
        """Update server stats in background"""
        while self.is_connected:
            response = self.send_request("GET_STATS", timeout=3)
            if response and not response.startswith("ERROR") and response != "TIMEOUT":
                try:
                    self.stats = json.loads(response)
                    if hasattr(self, 'stats_label'):
                        stats_text = f"Online: {self.stats.get('online_players', 0)} | Winners: {self.stats.get('total_winners', 0)} | Pings: {self.stats.get('total_pings', 0)}"
                        self.stats_label.config(text=stats_text)
                    self.connection_status = "connected"
                except:
                    pass
            else:
                self.connection_status = "unstable"
            time.sleep(3)
    
    def send_heartbeat(self):
        """Send periodic heartbeat to stay connected"""
        while self.is_connected:
            try:
                response = self.send_request(f"HEARTBEAT:{self.username}", timeout=2)
                if response != "OK":
                    self.connection_status = "unstable"
            except:
                self.connection_status = "unstable"
            time.sleep(15)  # Send heartbeat every 15 seconds
    
    def show_connection_screen(self):
        for widget in self.root.winfo_children():
            widget.destroy()
        
        title = tk.Label(self.root, text="P2W - Ping 2 Win", font=("Arial", 24, "bold"), fg="#2196F3")
        title.pack(pady=30)
        
        # Username with tooltip
        username_frame = tk.Frame(self.root)
        username_frame.pack(pady=5)
        tk.Label(username_frame, text="Username:", font=("Arial", 12)).pack()
        tk.Label(username_frame, text="(alphanumeric, max 32 chars)", font=("Arial", 8), fg="gray").pack()
        
        self.username_entry = tk.Entry(self.root, font=("Arial", 12), width=30)
        self.username_entry.insert(0, self.last_username)
        self.username_entry.pack(pady=5)
        
        # Server IP
        tk.Label(self.root, text="Server IP:", font=("Arial", 12)).pack(pady=5)
        self.ip_entry = tk.Entry(self.root, font=("Arial", 12), width=30)
        self.ip_entry.insert(0, self.last_ip)
        self.ip_entry.pack(pady=5)
        
        # Server Port
        tk.Label(self.root, text="Server Port:", font=("Arial", 12)).pack(pady=5)
        self.port_entry = tk.Entry(self.root, font=("Arial", 12), width=30)
        self.port_entry.insert(0, self.last_port)
        self.port_entry.pack(pady=5)
        
        # Connect Button
        connect_btn = tk.Button(
            self.root, 
            text="Connect (Enter)", 
            font=("Arial", 14, "bold"),
            bg="#4CAF50",
            fg="white",
            width=20,
            height=2,
            command=self.connect_to_server
        )
        connect_btn.pack(pady=30)
        
        # Status tip
        tk.Label(self.root, text="Tip: Press Enter to connect", font=("Arial", 9), fg="gray").pack()
    
    def validate_input(self):
        """Validate user input"""
        if not self.username:
            messagebox.showerror("Error", "Please enter a username!")
            return False
        
        if len(self.username) > 32:
            messagebox.showerror("Error", "Username too long (max 32 characters)")
            return False
        
        if not self.username.replace('_', '').replace('-', '').isalnum():
            messagebox.showerror("Error", "Username can only contain letters, numbers, _ and -")
            return False
        
        if not self.server_ip:
            messagebox.showerror("Error", "Please enter server IP!")
            return False
        
        if not self.server_port.isdigit():
            messagebox.showerror("Error", "Port must be a number!")
            return False
        
        return True
    
    def connect_to_server(self):
        self.username = self.username_entry.get().strip()
        self.server_ip = self.ip_entry.get().strip()
        self.server_port = self.port_entry.get().strip()
        
        if not self.validate_input():
            return
        
        # Test connection and send CONNECT message
        response = self.send_request(f"CONNECT:{self.username}")
        
        if response == "CONNECTED":
            self.is_connected = True
            self.save_config()
            # Start stats update thread
            self.stats_thread = threading.Thread(target=self.update_stats, daemon=True)
            self.stats_thread.start()
            # Start heartbeat thread
            self.heartbeat_thread = threading.Thread(target=self.send_heartbeat, daemon=True)
            self.heartbeat_thread.start()
            self.show_game_screen()
        elif response == "INVALID_USERNAME":
            messagebox.showerror("Error", "Invalid username! Use only letters, numbers, _ and -")
        elif response == "BLACKLISTED":
            messagebox.showerror("Error", "Your IP has been blacklisted from this server!")
        elif response == "TIMEOUT":
            messagebox.showerror("Error", "Connection timeout! Server not responding.")
        elif response == "REFUSED":
            messagebox.showerror("Error", "Connection refused! Is the server running?")
        elif response == "DNS_ERROR":
            messagebox.showerror("Error", "Could not resolve hostname! Check server IP.")
        else:
            messagebox.showerror("Error", f"Connection failed: {response}")
    
    def disconnect(self):
        if self.is_connected:
            self.send_request(f"DISCONNECT:{self.username}")
            self.is_connected = False
        self.has_pinged = False
        self.connection_status = "disconnected"
        self.show_connection_screen()
    
    def copy_server_address(self):
        """Copy server address to clipboard"""
        address = f"{self.server_ip}:{self.server_port}"
        self.root.clipboard_clear()
        self.root.clipboard_append(address)
        messagebox.showinfo("Copied", f"Server address copied: {address}")
    
    def show_game_screen(self):
        for widget in self.root.winfo_children():
            widget.destroy()
        
        # Title
        title = tk.Label(self.root, text="P2W - Ping 2 Win", font=("Arial", 20, "bold"), fg="#2196F3")
        title.pack(pady=15)
        
        # Info with connection indicator
        info_frame = tk.Frame(self.root)
        info_frame.pack(pady=5)
        
        self.status_indicator = tk.Label(info_frame, text="●", font=("Arial", 12), fg="green")
        self.status_indicator.pack(side=tk.LEFT, padx=5)
        
        info = tk.Label(
            info_frame,
            text=f"{self.username} @ {self.server_ip}:{self.server_port}",
            font=("Arial", 11)
        )
        info.pack(side=tk.LEFT)
        
        # Stats bar
        self.stats_label = tk.Label(
            self.root,
            text="Loading stats...",
            font=("Arial", 9),
            fg="gray"
        )
        self.stats_label.pack(pady=5)
        
        # Latency display
        latency = self.measure_latency()
        self.latency_label = tk.Label(
            self.root,
            text=f"Latency: {latency:.2f}ms",
            font=("Arial", 10, "bold"),
            fg="green" if latency < 50 else "orange" if latency < 150 else "red"
        )
        self.latency_label.pack(pady=5)
        
        # Refresh latency button
        refresh_btn = tk.Button(
            self.root,
            text="Refresh Latency",
            font=("Arial", 9),
            command=self.refresh_latency
        )
        refresh_btn.pack(pady=2)
        
        # Ping Button
        self.ping_btn = tk.Button(
            self.root,
            text="PING (Space)",
            font=("Arial", 18, "bold"),
            bg="#2196F3",
            fg="white",
            width=15,
            height=3,
            command=self.ping_server
        )
        self.ping_btn.pack(pady=20)
        
        # Status label
        self.status_label = tk.Label(
            self.root,
            text="Press PING or Space to win!",
            font=("Arial", 10),
            fg="gray"
        )
        self.status_label.pack(pady=5)
        
        # Button frame
        btn_frame = tk.Frame(self.root)
        btn_frame.pack(pady=10)
        
        # Leaderboard Button
        leaderboard_btn = tk.Button(
            btn_frame,
            text="Leaderboard",
            font=("Arial", 11),
            bg="#FF9800",
            fg="white",
            width=12,
            command=self.show_leaderboard
        )
        leaderboard_btn.pack(side=tk.LEFT, padx=3)
        
        # Copy address button
        copy_btn = tk.Button(
            btn_frame,
            text="Copy Address",
            font=("Arial", 11),
            bg="#9C27B0",
            fg="white",
            width=12,
            command=self.copy_server_address
        )
        copy_btn.pack(side=tk.LEFT, padx=3)
        
        # Disconnect Button
        disconnect_btn = tk.Button(
            btn_frame,
            text="Disconnect",
            font=("Arial", 11),
            bg="#f44336",
            fg="white",
            width=12,
            command=self.disconnect
        )
        disconnect_btn.pack(side=tk.LEFT, padx=3)
        
        # Start connection monitor
        self.monitor_connection()
    
    def monitor_connection(self):
        """Monitor connection status and update indicator"""
        if self.is_connected:
            if self.connection_status == "connected":
                self.status_indicator.config(fg="green")
            elif self.connection_status == "unstable":
                self.status_indicator.config(fg="orange")
            else:
                self.status_indicator.config(fg="red")
            self.root.after(1000, self.monitor_connection)
    
    def refresh_latency(self):
        """Refresh latency measurement"""
        latency = self.measure_latency()
        self.latency_label.config(
            text=f"Latency: {latency:.2f}ms",
            fg="green" if latency < 50 else "orange" if latency < 150 else "red"
        )
    
    def ping_server(self):
        if self.has_pinged:
            messagebox.showinfo("Info", "You can only ping once!")
            return
        
        try:
            # Measure latency
            latency = self.measure_latency()
            
            # Send ping with username and latency
            message = f"P2W_PING:{self.username}|{latency}"
            response = self.send_request(message)
            
            if response == "TIMEOUT":
                messagebox.showerror("Error", "Request timed out! Server not responding.")
                return
            elif response == "REFUSED":
                messagebox.showerror("Error", "Connection refused! Server might be down.")
                return
            elif response.startswith("ERROR"):
                messagebox.showerror("Error", f"Connection error: {response}")
                return
            
            if response.startswith("RATE_LIMITED:"):
                wait_time = response.split(":")[1]
                messagebox.showwarning("Rate Limited", f"Please wait {wait_time}s before pinging again!\n\nThis server limits pings to prevent spam.")
                return
            
            self.has_pinged = True
            self.ping_btn.config(state="disabled", bg="gray")
            
            if response.startswith("WIN:"):
                rank = response.split(":")[1]
                self.status_label.config(
                    text=f"YOU WIN! Rank #{rank}",
                    fg="green",
                    font=("Arial", 14, "bold")
                )
                messagebox.showinfo("Success", f"Congratulations {self.username}!\n\nYou are winner #{rank}!\nLatency: {latency:.2f}ms")
            elif response == "ALREADY_WON":
                self.status_label.config(
                    text="Already Won",
                    fg="orange",
                    font=("Arial", 12, "bold")
                )
                messagebox.showwarning("Already Won", "You already won on this server!")
            elif response == "INVALID_USERNAME":
                messagebox.showerror("Error", "Invalid username!")
                self.has_pinged = False
                self.ping_btn.config(state="normal", bg="#2196F3")
            else:
                self.status_label.config(text="Invalid response", fg="red")
                messagebox.showerror("Error", "Invalid server response!")
                
        except Exception as e:
            messagebox.showerror("Error", f"Connection error: {str(e)}")
    
    def show_leaderboard(self):
        # Create leaderboard window
        lb_window = tk.Toplevel(self.root)
        lb_window.title("P2W Leaderboard")
        lb_window.geometry("600x500")
        
        title_frame = tk.Frame(lb_window)
        title_frame.pack(pady=10)
        
        title = tk.Label(title_frame, text="Leaderboard", font=("Arial", 18, "bold"))
        title.pack(side=tk.LEFT, padx=10)
        
        refresh_lb_btn = tk.Button(
            title_frame,
            text="Refresh",
            font=("Arial", 10),
            command=lambda: self.refresh_leaderboard(lb_window)
        )
        refresh_lb_btn.pack(side=tk.LEFT)
        
        # Get leaderboard data
        response = self.send_request("GET_LEADERBOARD")
        
        if response == "TIMEOUT":
            tk.Label(lb_window, text="Request timed out", fg="red").pack()
            return
        elif not response or response.startswith("ERROR"):
            tk.Label(lb_window, text="Failed to load leaderboard", fg="red").pack()
            return
        
        try:
            data = json.loads(response)
            winners = data.get('winners', [])
            
            if not winners:
                tk.Label(lb_window, text="No winners yet! Be the first!", font=("Arial", 12)).pack(pady=50)
                return
            
            # Create treeview
            frame = tk.Frame(lb_window)
            frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            scrollbar = ttk.Scrollbar(frame)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            
            tree = ttk.Treeview(frame, columns=("Rank", "Username", "Time", "Latency"), show="headings", yscrollcommand=scrollbar.set)
            scrollbar.config(command=tree.yview)
            
            tree.heading("Rank", text="Rank")
            tree.heading("Username", text="Username")
            tree.heading("Time", text="Time")
            tree.heading("Latency", text="Latency")
            
            tree.column("Rank", width=60, anchor="center")
            tree.column("Username", width=150, anchor="center")
            tree.column("Time", width=180, anchor="center")
            tree.column("Latency", width=100, anchor="center")
            
            for winner in winners:
                tree.insert("", tk.END, values=(
                    f"#{winner['rank']}",
                    winner['username'],
                    winner['timestamp'],
                    winner.get('latency', 'N/A')
                ))
            
            tree.pack(fill=tk.BOTH, expand=True)
            
        except Exception as e:
            tk.Label(lb_window, text=f"Error: {str(e)}", fg="red").pack()
    
    def refresh_leaderboard(self, window):
        """Refresh leaderboard data"""
        window.destroy()
        self.show_leaderboard()
    
    def run(self):
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.mainloop()
    
    def on_closing(self):
        """Clean shutdown"""
        if self.is_connected:
            self.send_request(f"DISCONNECT:{self.username}")
        self.root.destroy()

if __name__ == "__main__":
    client = P2WClient()
    client.run()