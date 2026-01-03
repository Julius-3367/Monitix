"""Create a test server for development."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db.session import SessionLocal
from app.db.models import Server
from app.core.security import generate_api_key, hash_api_key
import uuid


def create_test_server():
    """Create a test server entry."""
    db = SessionLocal()
    
    print("=== Create Test Server ===")
    
    hostname = input("Hostname [test-server]: ").strip() or "test-server"
    ip_address = input("IP Address [127.0.0.1]: ").strip() or "127.0.0.1"
    
    # Generate API key
    api_key = generate_api_key()
    api_key_hash = hash_api_key(api_key)
    
    # Create server
    server = Server(
        server_id=str(uuid.uuid4()),
        hostname=hostname,
        ip_address=ip_address,
        api_key_hash=api_key_hash,
        status="offline",
        is_active=True
    )
    
    db.add(server)
    db.commit()
    db.refresh(server)
    
    print(f"\nTest server created successfully!")
    print(f"Server ID: {server.server_id}")
    print(f"Hostname: {hostname}")
    print(f"IP: {ip_address}")
    print(f"\nAPI Key (save this - it won't be shown again):")
    print(f"{api_key}")
    print(f"\nAdd this to your agent config.yaml:")
    print(f"  api_key: {api_key}")


if __name__ == "__main__":
    create_test_server()
