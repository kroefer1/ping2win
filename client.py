import tkinter as tk
from tkinter import messagebox, ttk
import socket
import json
import time
import threading

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
        
        self.show_connection_screen()
        
    def send_request(self, message):
        """Helper to send requests to server"""
        try:
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client.settimeout(5)
            client.connect((self.server_ip, int(self.server_port)))
            client.send(message.encode('utf-8'))
            response = client.recv(4096).decode('utf-8')
            client.close()
            return response
        except Exception as e:
            return None
    
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
            response = self.send_request("GET_STATS")
            if response:
                try:
                    self.stats = json.loads(response)
                    if hasattr(self, 'stats_label'):
                        stats_text = f"👥 Online: {self.stats.get('online_players', 0)} | 🏆 Winners: {self.stats.get('total_winners', 0)} | 📡 Pings: {self.stats.get('total_pings', 0)}"
                        self.stats_label.config(text=stats_text)
                except:
                    pass
            time.sleep(3)
    
    def show_connection_screen(self):
        for widget in self.root.winfo_children():
            widget.destroy()
        
        title = tk.Label(self.root, text="P2W - Ping 2 Win", font=("Arial", 24, "bold"), fg="#2196F3")
        title.pack(pady=30)
        
        # Username
        tk.Label(self.root, text="Username:", font=("Arial", 12)).pack(pady=5)
        self.username_entry = tk.Entry(self.root, font=("Arial", 12), width=30)
        self.username_entry.pack(pady=5)
        
        # Server IP
        tk.Label(self.root, text="Server IP:", font=("Arial", 12)).pack(pady=5)
        self.ip_entry = tk.Entry(self.root, font=("Arial", 12), width=30)
        self.ip_entry.insert(0, "localhost")
        self.ip_entry.pack(pady=5)
        
        # Server Port
        tk.Label(self.root, text="Server Port:", font=("Arial", 12)).pack(pady=5)
        self.port_entry = tk.Entry(self.root, font=("Arial", 12), width=30)
        self.port_entry.insert(0, "5555")
        self.port_entry.pack(pady=5)
        
        # Connect Button
        connect_btn = tk.Button(
            self.root, 
            text="Connect", 
            font=("Arial", 14, "bold"),
            bg="#4CAF50",
            fg="white",
            width=20,
            height=2,
            command=self.connect_to_server
        )
        connect_btn.pack(pady=30)
    
    def connect_to_server(self):
        self.username = self.username_entry.get().strip()
        self.server_ip = self.ip_entry.get().strip()
        self.server_port = self.port_entry.get().strip()
        
        if not self.username:
            messagebox.showerror("Error", "Please enter a username!")
            return
        
        if not self.server_ip:
            messagebox.showerror("Error", "Please enter server IP!")
            return
        
        if not self.server_port.isdigit():
            messagebox.showerror("Error", "Port must be a number!")
            return
        
        # Test connection and send CONNECT message
        response = self.send_request(f"CONNECT:{self.username}")
        if response == "CONNECTED":
            self.is_connected = True
            # Start stats update thread
            threading.Thread(target=self.update_stats, daemon=True).start()
            self.show_game_screen()
        else:
            messagebox.showerror("Error", "Could not connect to server!\nIs it running?")
    
    def disconnect(self):
        if self.is_connected:
            self.send_request(f"DISCONNECT:{self.username}")
            self.is_connected = False
        self.has_pinged = False
        self.show_connection_screen()
    
    def show_game_screen(self):
        for widget in self.root.winfo_children():
            widget.destroy()
        
        # Title
        title = tk.Label(self.root, text="P2W - Ping 2 Win", font=("Arial", 20, "bold"), fg="#2196F3")
        title.pack(pady=15)
        
        # Info
        info = tk.Label(
            self.root,
            text=f"👤 {self.username} @ {self.server_ip}:{self.server_port}",
            font=("Arial", 11)
        )
        info.pack(pady=5)
        
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
            text=f"📡 Latency: {latency:.2f}ms",
            font=("Arial", 10, "bold"),
            fg="green" if latency < 50 else "orange" if latency < 150 else "red"
        )
        self.latency_label.pack(pady=5)
        
        # Ping Button
        self.ping_btn = tk.Button(
            self.root,
            text="🎯 PING",
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
            text="Click PING to win!",
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
            text="🏆 Leaderboard",
            font=("Arial", 11),
            bg="#FF9800",
            fg="white",
            width=15,
            command=self.show_leaderboard
        )
        leaderboard_btn.pack(side=tk.LEFT, padx=5)
        
        # Disconnect Button
        disconnect_btn = tk.Button(
            btn_frame,
            text="🔌 Disconnect",
            font=("Arial", 11),
            bg="#f44336",
            fg="white",
            width=15,
            command=self.disconnect
        )
        disconnect_btn.pack(side=tk.LEFT, padx=5)
    
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
            
            if not response:
                messagebox.showerror("Error", "Connection failed!")
                return
            
            if response.startswith("RATE_LIMITED:"):
                wait_time = response.split(":")[1]
                messagebox.showwarning("Rate Limited", f"Please wait {wait_time}s before pinging again!")
                return
            
            self.has_pinged = True
            self.ping_btn.config(state="disabled", bg="gray")
            
            if response.startswith("WIN:"):
                rank = response.split(":")[1]
                self.status_label.config(
                    text=f"🎉 YOU WIN! Rank #{rank} 🎉",
                    fg="green",
                    font=("Arial", 14, "bold")
                )
                messagebox.showinfo("Success", f"🎉 Congratulations {self.username}!\n\nYou are winner #{rank}!\nLatency: {latency:.2f}ms")
            elif response == "ALREADY_WON":
                self.status_label.config(
                    text="❌ Already Won",
                    fg="orange",
                    font=("Arial", 12, "bold")
                )
                messagebox.showwarning("Already Won", "You already won on this server!")
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
        
        title = tk.Label(lb_window, text="🏆 Leaderboard", font=("Arial", 18, "bold"))
        title.pack(pady=10)
        
        # Get leaderboard data
        response = self.send_request("GET_LEADERBOARD")
        if not response:
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
    
    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    client = P2WClient()
    client.run()