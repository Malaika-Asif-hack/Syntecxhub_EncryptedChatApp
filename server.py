import socket
import threading
import logging
import json
import os  # Added this import
from datetime import datetime
from typing import Dict, Set
from crypto_utils import AESChatCrypto

class ChatServer:
    """Multi-client encrypted chat server"""
    
    def __init__(self, host: str = '127.0.0.1', port: int = 5555, password: str = None):
        self.host = host
        self.port = port
        self.server_socket = None
        self.clients: Dict[socket.socket, str] = {}  # socket -> username
        self.usernames: Set[str] = set()
        self.lock = threading.Lock()
        
        # Setup crypto for server logging (so server can read messages)
        if password is None:
            password = "default_secure_password_change_me"
        self.crypto = AESChatCrypto(password)
        
        # Setup logging
        os.makedirs("chat_logs", exist_ok=True)
        log_filename = f'chat_logs/server_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(message)s',
            handlers=[
                logging.FileHandler(log_filename),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
    def start(self):
        """Start the chat server"""
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(10)
        
        self.logger.info(f"Server started on {self.host}:{self.port}")
        self.logger.info(f"Encryption enabled with AES-CBC (PBKDF2 key derivation)")
        
        # Export salt for clients
        salt = self.crypto.export_salt()
        self.logger.info(f"Key salt: {salt}")
        
        try:
            while True:
                client_socket, address = self.server_socket.accept()
                self.logger.info(f"New connection from {address}")
                
                # Send salt to client
                client_socket.send(json.dumps({
                    'type': 'init',
                    'salt': salt
                }).encode('utf-8'))
                
                # Handle client in new thread
                client_thread = threading.Thread(
                    target=self.handle_client,
                    args=(client_socket, address)
                )
                client_thread.daemon = True
                client_thread.start()
                
        except KeyboardInterrupt:
            self.logger.info("Server shutting down...")
        finally:
            self.stop()
    
    def handle_client(self, client_socket: socket.socket, address):
        """Handle individual client connection"""
        username = None
        
        try:
            while True:
                # Receive encrypted message
                data = client_socket.recv(4096).decode('utf-8')
                if not data:
                    break
                
                message = json.loads(data)
                
                # Handle different message types
                if message['type'] == 'join':
                    username = message['username']
                    with self.lock:
                        if username in self.usernames:
                            client_socket.send(json.dumps({
                                'type': 'error',
                                'message': 'Username already taken'
                            }).encode('utf-8'))
                            continue
                        
                        self.clients[client_socket] = username
                        self.usernames.add(username)
                    
                    self.logger.info(f"[JOIN] {username} joined the chat")
                    
                    # Notify others
                    self.broadcast({
                        'type': 'system',
                        'message': f"{username} joined the chat",
                        'timestamp': datetime.now().isoformat()
                    }, exclude=client_socket)
                    
                    # Send welcome
                    client_socket.send(json.dumps({
                        'type': 'system',
                        'message': f"Welcome {username}! You are now in the encrypted chat.",
                        'timestamp': datetime.now().isoformat()
                    }).encode('utf-8'))
                    
                elif message['type'] == 'message':
                    # Decrypt the message for logging
                    try:
                        decrypted_msg = self.crypto.decrypt(message['payload'])
                        self.logger.info(f"[MESSAGE] {username}: {decrypted_msg}")
                        
                        # Also log to separate chat history file
                        with open("chat_logs/chat_history.txt", "a", encoding="utf-8") as f:
                            f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [{username}]: {decrypted_msg}\n")
                    except Exception as e:
                        self.logger.error(f"Failed to decrypt message: {e}")
                        with open("chat_logs/chat_history.txt", "a", encoding="utf-8") as f:
                            f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [ERROR] Failed to decrypt message from {username}\n")
                    
                    # Forward encrypted message to all other clients
                    self.broadcast({
                        'type': 'message',
                        'username': username,
                        'payload': message['payload'],  # Forward encrypted payload
                        'timestamp': datetime.now().isoformat()
                    }, exclude=client_socket)
                    
                elif message['type'] == 'leave':
                    self.logger.info(f"[LEAVE] {username} left the chat")
                    with open("chat_logs/chat_history.txt", "a", encoding="utf-8") as f:
                        f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [SYSTEM] {username} left the chat\n")
                    break
                    
        except Exception as e:
            self.logger.error(f"Error handling client {address}: {e}")
        finally:
            # Clean up disconnected client
            if client_socket in self.clients:
                username = self.clients[client_socket]
                with self.lock:
                    del self.clients[client_socket]
                    self.usernames.discard(username)
                
                self.logger.info(f"[LEAVE] {username} left the chat")
                self.broadcast({
                    'type': 'system',
                    'message': f"{username} left the chat",
                    'timestamp': datetime.now().isoformat()
                }, exclude=client_socket)
            
            client_socket.close()
    
    def broadcast(self, message: dict, exclude: socket.socket = None):
        """Broadcast message to all connected clients"""
        with self.lock:
            for client in list(self.clients.keys()):
                if client != exclude:
                    try:
                        client.send(json.dumps(message).encode('utf-8'))
                    except:
                        pass
    
    def stop(self):
        """Stop the server and close all connections"""
        with self.lock:
            for client in list(self.clients.keys()):
                try:
                    client.close()
                except:
                    pass
            self.clients.clear()
        
        if self.server_socket:
            self.server_socket.close()
        
        self.logger.info("Server stopped")


def main():
    """Main entry point for server"""
    import sys
    
    # Create logs directory
    os.makedirs("chat_logs", exist_ok=True)
    
    print("=" * 50)
    print("Encrypted Chat Server")
    print("=" * 50)
    
    host = input("Server host (default: 127.0.0.1): ").strip() or '127.0.0.1'
    port = input("Server port (default: 5555): ").strip()
    port = int(port) if port else 5555
    
    password = input("Shared password for encryption: ").strip()
    if not password:
        password = "default_secure_password_change_me"
        print("Using default password. Change it for production.")
    
    server = ChatServer(host, port, password)
    
    try:
        server.start()
    except KeyboardInterrupt:
        print("\nShutting down...")
        server.stop()

if __name__ == "__main__":
    main()