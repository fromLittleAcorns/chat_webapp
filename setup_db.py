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
        
        # Initialize database (this creates the 'user' table and default admin)
        db = auth.initialize()
        
        print("✅ Users database initialized")
        print("✅ Default 'admin' user created by fasthtml-auth")
        
        # Check if our custom admin user already exists
        custom_admin = auth.get_user(config.ADMIN_USERNAME)
        
        if custom_admin:
            print(f"\n⚠️  User '{config.ADMIN_USERNAME}' already exists")
            overwrite = input("Update password? (y/n): ").lower()
            if overwrite != 'y':
                print("Setup cancelled.")
                return
            
            # Update password using the user repository
            success = auth.user_repo.update(
                custom_admin.id,
                password=config.ADMIN_PASSWORD,
                email=config.ADMIN_EMAIL or custom_admin.email
            )
            
            if success:
                print(f"✅ Password updated for '{config.ADMIN_USERNAME}'")
            else:
                print(f"❌ Failed to update password for '{config.ADMIN_USERNAME}'")
                
        else:
            # Create new custom admin user using the repository
            print(f"\n👤 Creating custom admin user '{config.ADMIN_USERNAME}'...")
            
            new_admin = auth.user_repo.create(
                username=config.ADMIN_USERNAME,
                email=config.ADMIN_EMAIL or f"{config.ADMIN_USERNAME}@system.local",
                password=config.ADMIN_PASSWORD,
                role='admin'
            )
            
            if new_admin:
                print(f"✅ Admin user '{config.ADMIN_USERNAME}' created successfully!")
            else:
                print(f"❌ Failed to create admin user '{config.ADMIN_USERNAME}'")
                sys.exit(1)
        
        # Initialize conversations database
        from models import init_database
        init_database()
        print("✅ Conversations database initialized")
        
        # Show all users (for verification)
        all_users = auth.user_repo.list_all()
        print(f"\n📊 Total users in database: {len(all_users)}")
        for user in all_users:
            print(f"   - {user.username} ({user.role}) - Email: {user.email}")
        
        print("\n📝 Next steps:")
        print("   1. Start your application:")
        print("      python app.py")
        print("      # Or in production: systemctl start chat-app")
        print("   2. Visit your site:")
        print("      Development: http://localhost:5001")
        print("      Production: https://chat.therichmond4.co.uk")
        print(f"   3. Login with username: {config.ADMIN_USERNAME}")
        print("   4. IMPORTANT: Change the admin password after first login!")
        print("\n🔒 Security reminders:")
        print("   - Keep .env secure (it's in .gitignore)")
        print("   - Change admin password through the app")
        print("   - Consider removing ADMIN_PASSWORD from .env after setup")
        print("   - Delete the default 'admin' user if you created a custom admin")
        
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
