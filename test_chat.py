import subprocess
import time
import threading
import sys
import os
import datetime

def run_server():
    """Run chat server"""
    subprocess.run([sys.executable, 'server.py'])

def run_client(username):
    """Run chat client"""
    subprocess.run([sys.executable, 'client.py'])

def create_logs_readme():
    """Create a readme file for logs"""
    log_readme = """Chat Logs Information
================================

Log files are stored in the chat_logs/ directory:

Server Logs:
- server_YYYYMMDD_HHMMSS.log - Complete server activity log
- chat_history.txt - All decrypted messages in chronological order

Client Logs:
- client_[username]_history.txt - Individual client chat history

Log Format:
[Timestamp] [LOG_TYPE] Message

Log Types:
- CONNECT - Client connection events
- JOIN/LEAVE - User join/leave events  
- SENT - Messages sent by user
- RECEIVED - Messages received by user
- ENCRYPTED - Encrypted message preview
- SYSTEM - System notifications
- ERROR - Error events

All messages are encrypted using AES-256-CBC with PBKDF2 key derivation.
    """
    
    os.makedirs("chat_logs", exist_ok=True)
    with open("chat_logs/README.txt", "w", encoding="utf-8") as f:
        f.write(log_readme)
    print("Created chat_logs/README.txt - log information")

def show_test_instructions():
    """Display test instructions"""
    print("=" * 50)
    print("CHAT SYSTEM TEST INSTRUCTIONS")
    print("=" * 50)
    print()
    print("STEP 1: Start the Server")
    print("  - Open Terminal 1")
    print("  - Run: python server.py")
    print("  - Enter host, port, and shared password")
    print()
    print("STEP 2: Start Client 1")
    print("  - Open Terminal 2")
    print("  - Run: python client.py")
    print("  - Enter same host, port, username, and same password")
    print()
    print("STEP 3: Start Client 2")
    print("  - Open Terminal 3")
    print("  - Run: python client.py")
    print("  - Enter same host, port, different username, same password")
    print()
    print("STEP 4: Chat")
    print("  - Type messages in any client")
    print("  - Messages are encrypted before sending")
    print("  - Other clients see decrypted messages")
    print()
    print("STEP 5: Check Logs")
    print("  - Server logs: chat_logs/server_*.log")
    print("  - Chat history: chat_logs/chat_history.txt")
    print("  - Client logs: chat_logs/client_[username]_history.txt")
    print()
    print("=" * 50)
    print("Encryption Information")
    print("=" * 50)
    print("  Algorithm: AES-256-CBC")
    print("  Key Derivation: PBKDF2 (100,000 iterations)")
    print("  IV: Random 16 bytes per message")
    print("  Padding: PKCS7")
    print()
    print("To exit: Type '/quit' in any client or press Ctrl+C in server")
    print("=" * 50)

def quick_test():
    """Run automated quick test (optional)"""
    print("Running quick connectivity test...")
    
    # Check if required files exist
    required_files = ['server.py', 'client.py', 'crypto_utils.py']
    missing = [f for f in required_files if not os.path.exists(f)]
    
    if missing:
        print(f"Missing files: {missing}")
        print("Please ensure all files are in the same directory")
        return False
    
    print("All required files found")
    print("To test manually, follow the instructions above")
    return True

if __name__ == "__main__":
    print("=" * 50)
    print("CHAT SYSTEM TEST")
    print("=" * 50)
    
    # Create logs directory and readme
    create_logs_readme()
    
    print()
    print("Choose an option:")
    print("1. Show test instructions")
    print("2. Run quick file check")
    print("3. Exit")
    print()
    
    choice = input("Enter choice (1, 2, or 3): ").strip()
    
    if choice == '1':
        show_test_instructions()
    elif choice == '2':
        quick_test()
    else:
        print("Exiting. Run server.py and client.py manually to test the chat system.")
    
    print()
    print("Test completed. Check chat_logs/ directory for logs.")