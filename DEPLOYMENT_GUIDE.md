# Production Deployment Guide

## What Changed

### 1. Simplified app.py
- ✅ Removed `IS_PRODUCTION` checks
- ✅ Removed duplicate `load_dotenv()` (config.py handles it)
- ✅ All configuration now comes from config.py
- ✅ Uses `config.ALLOW_REGISTRATION` instead of hardcoded `True`
- ✅ Uses `config.HOST`, `config.PORT`, `config.RELOAD` in serve()

### 2. Enhanced config.py
- ✅ Added `ALLOW_REGISTRATION` setting
- ✅ Added `ADMIN_USERNAME`, `ADMIN_PASSWORD`, `ADMIN_EMAIL` for setup script

### 3. Created setup_db.py
- ✅ Initializes users database (via fasthtml-auth)
- ✅ Initializes conversations database
- ✅ Creates admin user from .env variables
- ✅ Can update admin password if user exists

### 4. Updated Environment Files
- ✅ `.env.example` - Complete template with all options documented
- ✅ `.env` - Your local development configuration
- ✅ `.prod_env` - Production template (keep locally, copy to server)

## Local Development Setup

### First Time Setup
```bash
# 1. Ensure you have .env configured
cp .env.example .env
nano .env  # Edit with your dev values

# 2. Run setup script to create databases and admin user
python setup_db.py

# 3. Start the app
python app.py

# 4. Visit http://localhost:5001
# Login with credentials from .env (admin/admin123)
```

### After Pulling Code Updates
```bash
git pull
pip install -r requirements.txt  # If dependencies changed
python app.py
```

## Production Deployment

### Initial Deployment

**On your local machine:**
```bash
# 1. Commit and push your changes
git add .
git commit -m "Prepare for production deployment"
git push
```

**On the production server:**
```bash
# 1. SSH into server
ssh john@217.154.63.51
sudo su -

# 2. Navigate to app directory
cd /var/www/vhosts/therichmond4.co.uk/chat.therichmond4.co.uk/chat_webapp

# 3. Pull latest code
git pull

# 4. Create/activate virtual environment (if not already done)
python3 -m venv venv
source venv/bin/activate

# 5. Install dependencies
pip install -r requirements.txt

# 6. Create production .env from your .prod_env template
# Copy .prod_env from your local machine to server, then:
mv .prod_env .env
nano .env  # Update any values that need changing (API keys, passwords, etc.)

# 7. Make setup_db.py executable
chmod +x setup_db.py

# 8. Run setup script to create databases and admin user
python setup_db.py

# 9. Create data and logs directories if needed
mkdir -p data logs

# 10. Fix ownership
cd ..
chown -R therichmond4.co.uk_6213ltvyukj:psacln chat_webapp/

# 11. Verify systemd service file exists
cat /etc/systemd/system/chat-app.service
# If it doesn't exist, create it (see systemd service section below)

# 12. Enable and start the service
systemctl daemon-reload
systemctl enable chat-app
systemctl start chat-app

# 13. Check status
systemctl status chat-app

# 14. View logs
journalctl -u chat-app -f
```

### Systemd Service File

Create `/etc/systemd/system/chat-app.service`:

```ini
[Unit]
Description=FastHTML Chat Application
After=network.target

[Service]
Type=simple
User=therichmond4.co.uk_6213ltvyukj
Group=psacln
WorkingDirectory=/var/www/vhosts/therichmond4.co.uk/chat.therichmond4.co.uk/chat_webapp
Environment="PATH=/var/www/vhosts/therichmond4.co.uk/chat.therichmond4.co.uk/chat_webapp/venv/bin"
ExecStart=/var/www/vhosts/therichmond4.co.uk/chat.therichmond4.co.uk/chat_webapp/venv/bin/python app.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### Nginx Configuration (Already in Plesk)

Should already be configured in Plesk under Apache & nginx Settings:

```nginx
location / {
    proxy_pass http://127.0.0.1:8000;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    
    # WebSocket support
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    
    # Timeouts
    proxy_connect_timeout 60s;
    proxy_send_timeout 60s;
    proxy_read_timeout 60s;
}
```

### Code Updates After Initial Deployment

```bash
# On server
cd /var/www/vhosts/therichmond4.co.uk/chat.therichmond4.co.uk/chat_webapp
git pull
systemctl restart chat-app
systemctl status chat-app
```

## Environment Variables Reference

### Development (.env)
- `ENVIRONMENT=development`
- `DEBUG=True`
- `PORT=5001`
- `RELOAD=True` (auto-reload on code changes)
- `HTTPS_ONLY=false`
- `ALLOW_REGISTRATION=True`

### Production (.prod_env → .env on server)
- `ENVIRONMENT=production`
- `DEBUG=False`
- `PORT=8000`
- `RELOAD=False` (stable, no auto-reload)
- `HTTPS_ONLY=true`
- `ALLOW_REGISTRATION=False` (invite-only)

## Troubleshooting

### Check if app is running
```bash
systemctl status chat-app
```

### View logs
```bash
# Live logs
journalctl -u chat-app -f

# Recent logs
journalctl -u chat-app -n 100
```

### Restart app
```bash
systemctl restart chat-app
```

### Check port 8000 is listening
```bash
ss -tlnp | grep 8000
# or
netstat -tlnp | grep 8000
```

### Test locally on server
```bash
curl http://localhost:8000
```

### Common Issues

**1. Permission denied on .env**
```bash
chown therichmond4.co.uk_6213ltvyukj:psacln .env
chmod 600 .env
```

**2. Database locked**
```bash
# Check if another process is using it
lsof data/users.db
```

**3. Port already in use**
```bash
# See what's using port 8000
lsof -i :8000
# Kill it or change port in .env
```

**4. Module not found errors**
```bash
# Ensure venv is activated and dependencies installed
source venv/bin/activate
pip install -r requirements.txt
```

## Security Checklist

- [ ] Changed `SECRET_KEY` to a secure random value
- [ ] Set strong `ADMIN_PASSWORD` in production .env
- [ ] Changed admin password after first login
- [ ] Set `HTTPS_ONLY=true` in production
- [ ] Set `ALLOW_REGISTRATION=False` if you want invite-only
- [ ] `.env` file has 600 permissions (only owner can read)
- [ ] API keys are set and kept secure
- [ ] Removed or commented `ADMIN_PASSWORD` from .env after setup

## Quick Reference

### Development
```bash
python app.py  # Runs on localhost:5001 with auto-reload
```

### Production
```bash
systemctl restart chat-app  # Restart after changes
systemctl status chat-app   # Check status
journalctl -u chat-app -f   # View logs
```

## File Locations

- **App code:** `/var/www/vhosts/therichmond4.co.uk/chat.therichmond4.co.uk/chat_webapp/`
- **Virtual env:** `chat_webapp/venv/`
- **Databases:** `chat_webapp/data/`
- **Config:** `chat_webapp/.env`
- **Service:** `/etc/systemd/system/chat-app.service`
- **Logs:** `journalctl -u chat-app` or `chat_webapp/logs/`

## Benefits of This Setup

✅ **Single codebase** - Same code in dev and prod
✅ **Environment-based config** - All settings in .env
✅ **No IS_PRODUCTION checks** - Cleaner, simpler code
✅ **Proper auth integration** - Uses fasthtml-auth correctly
✅ **Easy admin setup** - One script creates admin user
✅ **Secure by default** - Credentials in .env (gitignored)
✅ **Easy to deploy** - Copy .prod_env to server, rename to .env, run setup
