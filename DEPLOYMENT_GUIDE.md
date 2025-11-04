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

### SSL/TLS Certificate Setup (Let's Encrypt)

After initial deployment, you need to secure the site with HTTPS using Let's Encrypt.

#### Prerequisites

**1. Verify DNS is configured:**
```bash
# Check DNS resolves to your server
nslookup chat.therichmond4.co.uk
# Should return: 217.154.63.51 (your server IP)
```

**2. Ensure Nginx proxy is working:**
```bash
# Test HTTP access
curl http://chat.therichmond4.co.uk
# Should return your app's HTML, not 404
```

#### Step 1: Create Let's Encrypt Directory

Plesk's auto-generated nginx config expects ACME challenge files in a specific location:

```bash
# Create the directory where Plesk looks for ACME challenges
sudo mkdir -p /var/www/vhosts/default/htdocs/.well-known/acme-challenge

# Set proper ownership and permissions
sudo chown -R www-data:www-data /var/www/vhosts/default/htdocs/.well-known
sudo chmod -R 755 /var/www/vhosts/default/htdocs/.well-known

# Test it's accessible
echo "test" | sudo tee /var/www/vhosts/default/htdocs/.well-known/acme-challenge/test.txt
curl http://chat.therichmond4.co.uk/.well-known/acme-challenge/test.txt
# Should return: test
```

#### Step 2: Use Certbot to Get Certificate

Plesk's built-in Let's Encrypt often tries to use DNS validation which requires manual TXT records. Instead, use certbot directly with HTTP validation:

```bash
# Install certbot if not already installed
sudo apt update
sudo apt install certbot

# Request certificate using HTTP validation
sudo certbot certonly --webroot \
    -w /var/www/vhosts/default/htdocs \
    -d chat.therichmond4.co.uk \
    --agree-tos \
    --email your-email@example.com

# Certificate files will be created in:
# /etc/letsencrypt/live/chat.therichmond4.co.uk/
```

#### Step 3: Prepare Certificate for Plesk

Plesk requires the certificate and private key in a single file:

```bash
# Combine certificate and key into one file
sudo cat /etc/letsencrypt/live/chat.therichmond4.co.uk/fullchain.pem \
         /etc/letsencrypt/live/chat.therichmond4.co.uk/privkey.pem \
         > /tmp/combined.pem

# Copy to a location you can download from
sudo cp /tmp/combined.pem /var/www/vhosts/therichmond4.co.uk/chat.therichmond4.co.uk/
sudo chown therichmond4.co.uk_6213ltvyukj:psacln /var/www/vhosts/therichmond4.co.uk/chat.therichmond4.co.uk/combined.pem
```

#### Step 4: Upload Certificate to Plesk

**Option A: Using Plesk UI (Recommended)**

1. Download `combined.pem` to your local machine (using scp or Plesk file manager)
2. In Plesk, go to **Websites & Domains** → `chat.therichmond4.co.uk`
3. Click **SSL/TLS Certificates**
4. Click **Upload Certificate Files** or **Add SSL/TLS Certificate**
5. Upload the `combined.pem` file
6. Activate the certificate for your domain

**Option B: Using Plesk CLI**

```bash
# Install certificate directly via command line
sudo /usr/local/psa/bin/certificate \
    --create chat-letsencrypt \
    -cert-file /etc/letsencrypt/live/chat.therichmond4.co.uk/fullchain.pem \
    -key-file /etc/letsencrypt/live/chat.therichmond4.co.uk/privkey.pem

# Assign it to your domain
sudo /usr/local/psa/bin/subscription \
    --update chat.therichmond4.co.uk \
    -certificate-name chat-letsencrypt
```

#### Step 5: Enable HTTPS Redirect

In Plesk:
1. Go to **Websites & Domains** → `chat.therichmond4.co.uk`
2. Click **Hosting Settings**
3. Find **Security** section
4. Enable: ✅ **Permanent SEO-safe 301 redirect from HTTP to HTTPS**
5. Click **OK**

#### Step 6: Set Up Auto-Renewal

Let's Encrypt certificates expire every 90 days. Certbot usually sets up automatic renewal:

```bash
# Test renewal (dry run - doesn't actually renew)
sudo certbot renew --dry-run

# Check if auto-renewal timer is active
sudo systemctl status certbot.timer

# If timer is not active, enable it
sudo systemctl enable certbot.timer
sudo systemctl start certbot.timer

# View renewal history
sudo certbot certificates
```

#### Verification

**1. Test in browser:**
- Visit `https://chat.therichmond4.co.uk`
- Click the padlock icon
- Should show "Let's Encrypt" as issuer
- Certificate should be valid

**2. Test SSL configuration:**
```bash
# Check certificate details
openssl s_client -connect chat.therichmond4.co.uk:443 -servername chat.therichmond4.co.uk < /dev/null 2>/dev/null | openssl x509 -noout -text | grep -A2 "Issuer"

# Should show: Issuer: C = US, O = Let's Encrypt
```

**3. Test auto-redirect:**
```bash
curl -I http://chat.therichmond4.co.uk
# Should return: HTTP/1.1 301 Moved Permanently
# Location: https://chat.therichmond4.co.uk/
```

#### Troubleshooting SSL Issues

**Problem: "unable to open database file" errors after SSL setup**
- The database might need proper permissions for the systemd user
- See "Product Database Setup" section below

**Problem: Certificate shows as self-signed/Plesk certificate**
- The new certificate wasn't activated in Plesk
- Go to SSL/TLS Certificates and ensure the Let's Encrypt cert is selected

**Problem: certbot fails with "Connection refused"**
- Port 80 might not be accessible
- Check firewall: `sudo ufw status`
- Check nginx is running: `sudo systemctl status nginx`

**Problem: "Mixed content" warnings in browser**
- Some resources loading via HTTP instead of HTTPS
- Check browser console for details
- Ensure all links and resources use HTTPS or relative URLs

**Problem: Certificate renewal fails**
- Check renewal logs: `sudo cat /var/log/letsencrypt/letsencrypt.log`
- Verify `.well-known` directory is still accessible
- Manually renew: `sudo certbot renew --force-renewal`

#### Manual Certificate Renewal

If auto-renewal fails:

```bash
# Force renewal
sudo certbot renew --force-renewal

# Then update in Plesk (repeat Step 3-4)
```

### Product Database Setup

If you encounter database connection issues, ensure the product database is accessible:

```bash
# Option 1: Fix permissions on existing location
sudo chmod 755 /home/john
sudo chmod 755 /home/john/data
sudo chmod 755 /home/john/data/pbt_database
sudo chmod 644 /home/john/data/pbt_database/db_for_prod_search.db

# Option 2: Move to standard system location (recommended)
sudo mkdir -p /var/lib/chat_webapp/product_db
sudo cp /home/john/data/pbt_database/db_for_prod_search.db \
    /var/lib/chat_webapp/product_db/
sudo chown -R therichmond4.co.uk_6213ltvyukj:psacln /var/lib/chat_webapp
sudo chmod 755 /var/lib/chat_webapp
sudo chmod 755 /var/lib/chat_webapp/product_db
sudo chmod 644 /var/lib/chat_webapp/product_db/db_for_prod_search.db

# Update .env file
nano /var/www/vhosts/therichmond4.co.uk/chat.therichmond4.co.uk/chat_webapp/.env
# Change PRODUCT_DB_PATH to: /var/lib/chat_webapp/product_db/db_for_prod_search.db

# Restart app
systemctl restart chat-app
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
- [ ] SSL/TLS certificate installed and auto-renewal configured

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
- **Product DB:** `/var/lib/chat_webapp/product_db/db_for_prod_search.db` (or `/home/john/data/pbt_database/db_for_prod_search.db`)
- **Config:** `chat_webapp/.env`
- **Service:** `/etc/systemd/system/chat-app.service`
- **Logs:** `journalctl -u chat-app` or `chat_webapp/logs/`
- **SSL Certificates:** `/etc/letsencrypt/live/chat.therichmond4.co.uk/`

## Benefits of This Setup

✅ **Single codebase** - Same code in dev and prod
✅ **Environment-based config** - All settings in .env
✅ **No IS_PRODUCTION checks** - Cleaner, simpler code
✅ **Proper auth integration** - Uses fasthtml-auth correctly
✅ **Easy admin setup** - One script creates admin user
✅ **Secure by default** - Credentials in .env (gitignored)
✅ **Easy to deploy** - Copy .prod_env to server, rename to .env, run setup
✅ **HTTPS secured** - Let's Encrypt SSL with auto-renewal
