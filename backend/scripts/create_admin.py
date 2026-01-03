"""Create the first admin user."""
import sys
from pathlib import Path
from getpass import getpass

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db.session import SessionLocal
from app.db.models import User
from app.core.security import get_password_hash


def create_admin():
    """Create admin user."""
    db = SessionLocal()
    
    print("=== Create Admin User ===")
    
    # Check if admin exists
    existing = db.query(User).filter(User.username == "admin").first()
    if existing:
        print("Admin user already exists!")
        overwrite = input("Overwrite? (y/N): ").lower()
        if overwrite != 'y':
            print("Cancelled.")
            return
        db.delete(existing)
        db.commit()
    
    # Get user input
    username = input("Username [admin]: ").strip() or "admin"
    email = input("Email [admin@example.com]: ").strip() or "admin@example.com"
    full_name = input("Full Name [Admin User]: ").strip() or "Admin User"
    
    # Get password
    while True:
        password = getpass("Password: ")
        password_confirm = getpass("Confirm Password: ")
        
        if password != password_confirm:
            print("Passwords don't match! Try again.")
            continue
        
        if len(password) < 8:
            print("Password must be at least 8 characters!")
            continue
        
        break
    
    # Create user
    admin = User(
        username=username,
        email=email,
        full_name=full_name,
        role="admin",
        password_hash=get_password_hash(password),
        is_active=True
    )
    
    db.add(admin)
    db.commit()
    
    print(f"\nAdmin user '{username}' created successfully!")
    print(f"Email: {email}")
    print("\nYou can now log in to the dashboard.")


if __name__ == "__main__":
    create_admin()
