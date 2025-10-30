#!/usr/bin/env python3
"""
Database Setup Script

Initializes databases and creates initial admin user using fasthtml-auth.
Run once after deployment to create admin user.

Usage:
    python setup_db.py
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

import config
from fasthtml_auth import AuthManager

def setup_database():
    """Initialize database and create admin user"""
    print("=" * 60)
    print("Database Setup - FastHTML MCP Chat")
    print("=" * 60)
    
    # Ensure directories exist
    config.DATA_DIR.mkdir(exist_ok=True)
    
    # Get admin credentials from environment
    if not config.ADMIN_USERNAME or not config.ADMIN_PASSWORD:
        print("\n❌ Error: Admin credentials not set in .env")
        print("\nAdd these to your .env file:")
        print("ADMIN_USERNAME=your_admin_username")
        print("ADMIN_PASSWORD=your_secure_password")
        print("ADMIN_EMAIL=admin@yourdomain.com  # optional")
        print("\nExample:")
        print("ADMIN_USERNAME=john")
        print("ADMIN_PASSWORD=VerySecurePassword123!")
        print("ADMIN_EMAIL=john@therichmond4.co.uk")
        sys.exit(1)
    
    print(f"\n📂 Users Database: {config.USERS_DB_PATH}")
    print(f"📂 Conversations Database: {config.CONVERSATIONS_DB_PATH}")
    print(f"👤 Admin User: {config.ADMIN_USERNAME}")
    
    try:
        # Initialize auth manager (creates users.db and tables)
        auth = AuthManager(
            db_path=str(config.USERS_DB_PATH),
            config={
                'allow_registration': config.ALLOW_REGISTRATION,
                'public_paths': [],
                'login_path': '/auth/login',
            }
        )
        
        # Initialize database
        db = auth.initialize()
        
        print("✅ Users database initialized")
        
        # Check if admin user already exists
        existing_users = db.execute("SELECT username FROM users").fetchall()
        existing_usernames = [row[0] for row in existing_users]
        
        if config.ADMIN_USERNAME in existing_usernames:
            print(f"\n⚠️  User '{config.ADMIN_USERNAME}' already exists")
            overwrite = input("Update password? (y/n): ").lower()
            if overwrite != 'y':
                print("Setup cancelled.")
                return
            
            # Update password using auth manager's method
            db.execute(
                "UPDATE users SET password_hash = ? WHERE username = ?",
                (auth.hash_password(config.ADMIN_PASSWORD), config.ADMIN_USERNAME)
            )
            db.commit()
            print(f"✅ Password updated for '{config.ADMIN_USERNAME}'")
        else:
            # Create new admin user
            # Use auth manager's user creation (it handles password hashing)
            db.execute(
                """INSERT INTO users (username, email, password_hash, is_admin, created_at)
                   VALUES (?, ?, ?, ?, datetime('now'))""",
                (
                    config.ADMIN_USERNAME,
                    config.ADMIN_EMAIL,
                    auth.hash_password(config.ADMIN_PASSWORD),
                    1  # is_admin = True
                )
            )
            db.commit()
            print(f"✅ Admin user '{config.ADMIN_USERNAME}' created successfully!")
        
        # Initialize conversations database
        from models import init_database
        init_database()
        print("✅ Conversations database initialized")
        
        print("\n📝 Next steps:")
        print("   1. Start your application:")
        print("      python app.py")
        print("      # Or in production: systemctl start chat-app")
        print("   2. Visit your site:")
        print("      Development: http://localhost:5001")
        print("      Production: https://chat.therichmond4.co.uk")
        print("   3. Login with the admin credentials from .env")
        print("   4. IMPORTANT: Change the admin password after first login!")
        print("\n🔒 Security reminders:")
        print("   - Keep .env secure (it's in .gitignore)")
        print("   - Change admin password through the app")
        print("   - Consider removing ADMIN_PASSWORD from .env after setup")
        
    except Exception as e:
        print(f"\n❌ Error during setup: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    print("\n🔍 Validating configuration...")
    try:
        config.validate_config()
        print("✅ Configuration is valid\n")
    except ValueError as e:
        print(f"❌ Configuration error: {e}")
        sys.exit(1)
    
    setup_database()
