import socket
import threading
import json
import datetime
import os
from crypto_utils import AESChatCrypto

class ChatClient:
    def __init__(self, host='127.0.0.1', port=5555, username=None):
        self.host = host
        self.port = port
        self.username = username
        self.sock = None
        self.crypto = None
        self.running = False
    
    def log_message(self, message, msg_type="INFO"):
        """Save message to client log file"""
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_dir = "chat_logs"
        os.makedirs(log_dir, exist_ok=True)
        log_file = os.path.join(log_dir, f"client_{self.username}_history.txt")
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] [{msg_type}] {message}\n")
    
    def connect(self, password):
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((self.host, self.port))
            
            data = json.loads(self.sock.recv(4096).decode())
            if data['type'] == 'init':
                self.crypto = AESChatCrypto.from_salt(password, data['salt'])
                print("Encryption ready")
                self.log_message(f"Encryption ready connected to {self.host}:{self.port}", "CONNECT")
            
            self.sock.send(json.dumps({'type': 'join', 'username': self.username}).encode())
            self.running = True
            self.log_message(f"Joined chat as {self.username}", "JOIN")
            threading.Thread(target=self.receive, daemon=True).start()
            return True
        except Exception as e:
            print(f"Error: {e}")
            self.log_message(f"Connection error: {e}", "ERROR")
            return False
    
    def receive(self):
        while self.running:
            try:
                self.sock.settimeout(0.5)
                try:
                    data = self.sock.recv(4096).decode()
                    if not data: break
                    
                    msg = json.loads(data)
                    
                    if msg['type'] == 'system':
                        print(f"\n[System] {msg['message']}")
                        self.log_message(f"System: {msg['message']}", "SYSTEM")
                    elif msg['type'] == 'message':
                        try:
                            decrypted = self.crypto.decrypt(msg['payload'])
                            print(f"\n[{msg['username']}]: {decrypted}")
                            self.log_message(f"From {msg['username']}: {decrypted}", "RECEIVED")
                        except:
                            print(f"\n[ERROR] Decryption failed")
                            self.log_message(f"Failed to decrypt message from {msg['username']}", "ERROR")
                    print("\nYou: ", end='', flush=True)
                except socket.timeout:
                    continue
                except:
                    break
            except:
                break
        self.disconnect()
    
    def send(self, message):
        if not message.strip(): 
            return
        try:
            encrypted = self.crypto.encrypt(message)
            self.sock.send(json.dumps({'type': 'message', 'payload': encrypted}).encode())
            self.log_message(message, "SENT")
            self.log_message(f"[ENCRYPTED] {encrypted[:80]}...", "ENCRYPTED")
        except Exception as e:
            print(f"Send error: {e}")
            self.log_message(f"Send error: {e}", "ERROR")
            self.disconnect()
    
    def disconnect(self):
        self.running = False
        if self.sock:
            try:
                self.sock.send(json.dumps({'type': 'leave'}).encode())
                self.sock.close()
            except:
                pass
        self.log_message("Disconnected from server", "DISCONNECT")
        print("\nDisconnected")
    
    def run(self):
        print("\n" + "=" * 50)
        print("CHAT ACTIVE - Type messages below")
        print("Type '/quit' to exit")
        print("=" * 50)
        print("You: ", end='', flush=True)
        
        while self.running:
            try:
                msg = input().strip()
                if msg.lower() == '/quit':
                    break
                if msg:
                    self.send(msg)
                print("You: ", end='', flush=True)
            except KeyboardInterrupt:
                break
            except:
                break
        self.disconnect()

if __name__ == '__main__':
    import os
    os.makedirs("chat_logs", exist_ok=True)
    
    print("=" * 50)
    print("ENCRYPTED CHAT CLIENT")
    print("=" * 50)
    
    host = input("Server host (Enter for 127.0.0.1): ").strip() or '127.0.0.1'
    port = input("Server port (Enter for 5555): ").strip()
    port = int(port) if port else 5555
    username = input("Username: ").strip() or "User"
    password = input("Shared password: ").strip() or "test123"
    
    client = ChatClient(host, port, username)
    if client.connect(password):
        print(f"Connected to {host}:{port}")
        client.run()