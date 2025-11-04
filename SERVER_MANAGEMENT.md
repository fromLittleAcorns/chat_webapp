# Server Management Guide

Quick reference for day-to-day server operations and troubleshooting.

---

## Quick Commands Reference

### Service Management

```bash
# Restart app (after code changes)
sudo systemctl restart chat-app

# Check status
sudo systemctl status chat-app

# View live logs (Ctrl+C to exit)
sudo journalctl -u chat-app -f

# View recent logs (last 100 lines)
sudo journalctl -u chat-app -n 100

# Stop service
sudo systemctl stop chat-app

# Start service
sudo systemctl start chat-app

# Disable service (prevent auto-start on boot)
sudo systemctl disable chat-app

# Enable service (auto-start on boot)
sudo systemctl enable chat-app
```

### Database Operations

```bash
# Check database files exist
ls -lh /var/www/vhosts/therichmond4.co.uk/chat.therichmond4.co.uk/chat_webapp/data/

# Check database permissions
stat /var/www/vhosts/therichmond4.co.uk/chat.therichmond4.co.uk/chat_webapp/data/conversations.db

# Fix database permissions if needed
sudo chown therichmond4.co.uk_6213ltvyukj:psacln /var/www/vhosts/therichmond4.co.uk/chat.therichmond4.co.uk/chat_webapp/data/*.db
sudo chmod 644 /var/www/vhosts/therichmond4.co.uk/chat.therichmond4.co.uk/chat_webapp/data/*.db

# Check for database locks
sudo lsof /var/www/vhosts/therichmond4.co.uk/chat.therichmond4.co.uk/chat_webapp/data/conversations.db
```

### System Health Checks

```bash
# Check if app is listening on port 8000
sudo ss -tlnp | grep 8000
# or
sudo netstat -tlnp | grep 8000

# Test app locally
curl http://localhost:8000

# Test app externally
curl https://chat.therichmond4.co.uk

# Check nginx status
sudo systemctl status nginx

# Check disk space
df -h

# Check memory usage
free -h

# Check running processes
ps aux | grep python
```

---

## Common Workflows

### Deploy Code Updates

```bash
# 1. SSH to server
ssh john@217.154.63.51
sudo su -

# 2. Navigate to app directory
cd /var/www/vhosts/therichmond4.co.uk/chat.therichmond4.co.uk/chat_webapp

# 3. Pull latest code
git pull

# 4. If dependencies changed, update them
source venv/bin/activate
pip install -r requirements.txt

# 5. Restart app
systemctl restart chat-app

# 6. Verify it's running
systemctl status chat-app

# 7. Watch logs for any errors
journalctl -u chat-app -f
```

### Update Environment Variables

```bash
# 1. Edit .env file
cd /var/www/vhosts/therichmond4.co.uk/chat.therichmond4.co.uk/chat_webapp
nano .env

# 2. Restart app to pick up changes
systemctl restart chat-app

# 3. Verify changes took effect
journalctl -u chat-app -n 50
```

### Restart Everything (Full Restart)

```bash
# Restart app
sudo systemctl restart chat-app

# Restart nginx (if needed)
sudo systemctl restart nginx

# Check both are running
sudo systemctl status chat-app
sudo systemctl status nginx
```

### Check Application Health

```bash
# Quick health check
curl -I https://chat.therichmond4.co.uk

# Should return:
# HTTP/2 200
# content-type: text/html; charset=utf-8

# If it returns 502 Bad Gateway, app isn't running
# If it returns 404, nginx routing issue
# If connection refused, nginx isn't running
```

---

## Troubleshooting Guide

### Problem: App Won't Start

**Check the logs first:**
```bash
sudo journalctl -u chat-app -n 100
```

**Common causes:**

1. **Port 8000 already in use**
   ```bash
   # See what's using port 8000
   sudo lsof -i :8000
   
   # Kill the process if needed
   sudo kill -9 <PID>
   
   # Or change port in .env
   ```

2. **Permission errors**
   ```bash
   # Fix ownership
   cd /var/www/vhosts/therichmond4.co.uk/chat.therichmond4.co.uk
   sudo chown -R therichmond4.co.uk_6213ltvyukj:psacln chat_webapp/
   
   # Fix .env permissions
   sudo chmod 600 chat_webapp/.env
   ```

3. **Missing dependencies**
   ```bash
   cd /var/www/vhosts/therichmond4.co.uk/chat.therichmond4.co.uk/chat_webapp
   source venv/bin/activate
   pip install -r requirements.txt
   ```

4. **Database locked**
   ```bash
   # Check what's using the database
   sudo lsof data/conversations.db
   
   # If another process is using it, stop the app first
   sudo systemctl stop chat-app
   # Wait a few seconds
   sudo systemctl start chat-app
   ```

### Problem: 502 Bad Gateway

**Meaning:** Nginx can't reach your app

**Solutions:**
```bash
# 1. Check if app is running
sudo systemctl status chat-app

# 2. Check if port 8000 is listening
sudo ss -tlnp | grep 8000

# 3. If not running, check why
sudo journalctl -u chat-app -n 50

# 4. Restart app
sudo systemctl restart chat-app

# 5. Test directly
curl http://localhost:8000
```

### Problem: 404 Not Found

**Meaning:** Nginx is running but not routing correctly

**Solutions:**
```bash
# Check nginx configuration
sudo nginx -t

# Check nginx is running
sudo systemctl status nginx

# Restart nginx
sudo systemctl restart nginx

# Check nginx logs
sudo tail -f /var/www/vhosts/system/chat.therichmond4.co.uk/logs/proxy_error_log
```

### Problem: SSL Certificate Errors

**Check certificate status:**
```bash
# View certificate details
sudo certbot certificates

# Check certificate expiry
openssl s_client -connect chat.therichmond4.co.uk:443 -servername chat.therichmond4.co.uk < /dev/null 2>/dev/null | openssl x509 -noout -dates

# Test renewal (dry run)
sudo certbot renew --dry-run
```

**Manual renewal if needed:**
```bash
# Force renewal
sudo certbot renew --force-renewal

# Combine certificate and key for Plesk
sudo cat /etc/letsencrypt/live/chat.therichmond4.co.uk/fullchain.pem \
         /etc/letsencrypt/live/chat.therichmond4.co.uk/privkey.pem \
         > /tmp/combined.pem

# Upload to Plesk via UI
```

### Problem: "Unable to Open Database File"

**Check database location and permissions:**
```bash
# Verify database exists
ls -lh /var/lib/chat_webapp/product_db/db_for_prod_search.db

# Check permissions
stat /var/lib/chat_webapp/product_db/db_for_prod_search.db

# Fix permissions
sudo chown therichmond4.co.uk_6213ltvyukj:psacln /var/lib/chat_webapp/product_db/db_for_prod_search.db
sudo chmod 644 /var/lib/chat_webapp/product_db/db_for_prod_search.db

# Verify .env has correct path
cat /var/www/vhosts/therichmond4.co.uk/chat.therichmond4.co.uk/chat_webapp/.env | grep PRODUCT_DB_PATH
```

### Problem: Empty Messages in Conversation

**Check and clean database:**
```bash
# Connect to database
sqlite3 /var/www/vhosts/therichmond4.co.uk/chat.therichmond4.co.uk/chat_webapp/data/conversations.db

# Find empty messages
SELECT id, conversation_id, role, length(content) FROM messages WHERE length(trim(content)) = 0;

# Delete empty messages
DELETE FROM messages WHERE length(trim(content)) = 0;

# Exit
.quit
```

### Problem: High Memory Usage

**Check memory:**
```bash
# Overall memory
free -h

# App memory usage
ps aux | grep python | grep app.py

# If high, restart app
sudo systemctl restart chat-app
```

---

## File Locations Reference

| Purpose | Path |
|---------|------|
| **App root** | `/var/www/vhosts/therichmond4.co.uk/chat.therichmond4.co.uk/chat_webapp/` |
| **Main application** | `chat_webapp/app.py` |
| **Configuration** | `chat_webapp/.env` |
| **Conversation DB** | `chat_webapp/data/conversations.db` |
| **User DB** | `chat_webapp/data/users.db` |
| **Product DB** | `/var/lib/chat_webapp/product_db/db_for_prod_search.db` |
| **Virtual environment** | `chat_webapp/venv/` |
| **Systemd service** | `/etc/systemd/system/chat-app.service` |
| **SSL certificates** | `/etc/letsencrypt/live/chat.therichmond4.co.uk/` |
| **Nginx config** | `/etc/nginx/plesk.conf.d/vhosts/chat.therichmond4.co.uk.conf` |
| **Nginx logs** | `/var/www/vhosts/system/chat.therichmond4.co.uk/logs/` |

---

## Access URLs

| Purpose | URL |
|---------|-----|
| **Production app** | https://chat.therichmond4.co.uk |
| **Admin panel** | https://chat.therichmond4.co.uk/auth/admin |
| **User management** | https://chat.therichmond4.co.uk/auth/admin/users |
| **Login page** | https://chat.therichmond4.co.uk/login |

---

## Monitoring Tips

### Daily Health Check

```bash
# Quick status check
sudo systemctl status chat-app

# Check recent errors in logs
sudo journalctl -u chat-app --since "1 hour ago" | grep -i error

# Check disk space
df -h | grep vhosts

# Check memory
free -h

# Check SSL certificate expiry
sudo certbot certificates | grep -A2 chat.therichmond4
```

### Log Monitoring

```bash
# Watch live logs (useful during debugging)
sudo journalctl -u chat-app -f

# Search for specific errors
sudo journalctl -u chat-app | grep "ERROR"

# View logs from specific time
sudo journalctl -u chat-app --since "2024-11-03 14:00:00"

# Export logs to file
sudo journalctl -u chat-app --since today > /tmp/chat-app-logs.txt
```

### Performance Monitoring

```bash
# Check request times
sudo tail -f /var/www/vhosts/system/chat.therichmond4.co.uk/logs/proxy_access_ssl_log

# Monitor active connections
sudo ss -tn | grep :8000 | wc -l

# Watch CPU usage
top -p $(pgrep -f "python app.py")
```

---

## Backup Procedures

### Backup Databases

```bash
# Backup conversation database
sqlite3 /var/www/vhosts/therichmond4.co.uk/chat.therichmond4.co.uk/chat_webapp/data/conversations.db ".backup /tmp/conversations-$(date +%Y%m%d).db"

# Backup user database
sqlite3 /var/www/vhosts/therichmond4.co.uk/chat.therichmond4.co.uk/chat_webapp/data/users.db ".backup /tmp/users-$(date +%Y%m%d).db"

# Download backups to local machine
scp john@217.154.63.51:/tmp/*-$(date +%Y%m%d).db ~/backups/
```

### Backup Configuration

```bash
# Backup .env file
sudo cp /var/www/vhosts/therichmond4.co.uk/chat.therichmond4.co.uk/chat_webapp/.env \
        /tmp/chat-app-env-$(date +%Y%m%d).backup

# Download to local machine
scp john@217.154.63.51:/tmp/chat-app-env-$(date +%Y%m%d).backup ~/backups/
```

### Automated Backup Script

Create `/root/backup-chat-app.sh`:

```bash
#!/bin/bash
DATE=$(date +%Y%m%d)
BACKUP_DIR="/root/backups"
APP_DIR="/var/www/vhosts/therichmond4.co.uk/chat.therichmond4.co.uk/chat_webapp"

mkdir -p $BACKUP_DIR

# Backup databases
sqlite3 $APP_DIR/data/conversations.db ".backup $BACKUP_DIR/conversations-$DATE.db"
sqlite3 $APP_DIR/data/users.db ".backup $BACKUP_DIR/users-$DATE.db"

# Backup .env
cp $APP_DIR/.env $BACKUP_DIR/env-$DATE.backup

# Keep only last 7 days
find $BACKUP_DIR -name "*.db" -mtime +7 -delete
find $BACKUP_DIR -name "*.backup" -mtime +7 -delete

echo "Backup completed: $DATE"
```

Make executable and add to crontab:
```bash
chmod +x /root/backup-chat-app.sh

# Add to crontab (daily at 2am)
echo "0 2 * * * /root/backup-chat-app.sh >> /var/log/chat-app-backup.log 2>&1" | sudo crontab -
```

---

## Environment Variables Quick Reference

### Development (.env - local)
```bash
ENVIRONMENT=development
DEBUG=True
PORT=5001
RELOAD=True
HTTPS_ONLY=false
ALLOW_REGISTRATION=True
```

### Production (.env - server)
```bash
ENVIRONMENT=production
DEBUG=False
PORT=8000
RELOAD=False
HTTPS_ONLY=true
ALLOW_REGISTRATION=False
ANTHROPIC_API_KEY=sk-ant-...
SECRET_KEY=...
PRODUCT_DB_PATH=/var/lib/chat_webapp/product_db/db_for_prod_search.db
SYSTEM_INSTRUCTIONS_PATH=/opt/mcp_server
```

---

## Useful Nginx Commands

```bash
# Test nginx configuration
sudo nginx -t

# Reload nginx (pick up config changes)
sudo systemctl reload nginx

# Restart nginx
sudo systemctl restart nginx

# View nginx error logs
sudo tail -f /var/log/nginx/error.log

# View access logs for your domain
sudo tail -f /var/www/vhosts/system/chat.therichmond4.co.uk/logs/proxy_access_ssl_log
```

---

## Security Maintenance

### Update SSL Certificate (Manual)

If auto-renewal fails:
```bash
# Force renewal
sudo certbot renew --force-renewal

# Prepare combined file for Plesk
sudo cat /etc/letsencrypt/live/chat.therichmond4.co.uk/fullchain.pem \
         /etc/letsencrypt/live/chat.therichmond4.co.uk/privkey.pem \
         > /tmp/combined.pem

# Upload via Plesk UI
```

### Update Dependencies

```bash
cd /var/www/vhosts/therichmond4.co.uk/chat.therichmond4.co.uk/chat_webapp
source venv/bin/activate

# Update all packages
pip list --outdated
pip install --upgrade package-name

# Or update requirements.txt and install
pip install -r requirements.txt

# Restart app
sudo systemctl restart chat-app
```

### Check for Security Updates

```bash
# System updates
sudo apt update
sudo apt list --upgradable

# Apply security updates
sudo apt upgrade

# Reboot if kernel updated
sudo reboot
```

---

## Emergency Procedures

### App is Down - Quick Recovery

```bash
# 1. Check status
sudo systemctl status chat-app

# 2. View recent errors
sudo journalctl -u chat-app -n 50

# 3. Try restart
sudo systemctl restart chat-app

# 4. If still failing, check logs
sudo journalctl -u chat-app -f

# 5. Nuclear option - stop everything and restart
sudo systemctl stop chat-app
sleep 5
sudo systemctl start chat-app
```

### Rollback to Previous Code Version

```bash
cd /var/www/vhosts/therichmond4.co.uk/chat.therichmond4.co.uk/chat_webapp

# View recent commits
git log --oneline -10

# Rollback to specific commit
git reset --hard <commit-hash>

# Restart app
sudo systemctl restart chat-app

# If this fixes it, update the remote
git push --force
```

### Database Corruption Recovery

```bash
# 1. Stop app
sudo systemctl stop chat-app

# 2. Check database integrity
sqlite3 /var/www/vhosts/therichmond4.co.uk/chat.therichmond4.co.uk/chat_webapp/data/conversations.db "PRAGMA integrity_check;"

# 3. If corrupted, restore from backup
cp /root/backups/conversations-YYYYMMDD.db /var/www/vhosts/therichmond4.co.uk/chat.therichmond4.co.uk/chat_webapp/data/conversations.db

# 4. Fix permissions
sudo chown therichmond4.co.uk_6213ltvyukj:psacln /var/www/vhosts/therichmond4.co.uk/chat.therichmond4.co.uk/chat_webapp/data/conversations.db

# 5. Restart app
sudo systemctl start chat-app
```

---

## Performance Optimization

### Clear Old Logs

```bash
# Clear systemd journal (keep last 7 days)
sudo journalctl --vacuum-time=7d

# Check journal size
sudo journalctl --disk-usage
```

### Database Maintenance

```bash
# Vacuum databases to reclaim space and improve performance
cd /var/www/vhosts/therichmond4.co.uk/chat.therichmond4.co.uk/chat_webapp/data

sqlite3 conversations.db "VACUUM;"
sqlite3 users.db "VACUUM;"

# Analyze databases for better query performance
sqlite3 conversations.db "ANALYZE;"
sqlite3 users.db "ANALYZE;"
```

---

## Contact Information for Support

- **Hosting Provider:** Plesk (217.154.63.51)
- **Domain Registrar:** (Check DNS records)
- **SSL Provider:** Let's Encrypt (free, auto-renew)
- **App Repository:** Check git remote for URL

---

## Quick Checklist for Common Tasks

### ✅ Deploying Code Update
- [ ] `ssh` to server
- [ ] `cd` to app directory
- [ ] `git pull`
- [ ] `systemctl restart chat-app`
- [ ] `systemctl status chat-app`

### ✅ Checking App Health
- [ ] `systemctl status chat-app`
- [ ] `curl https://chat.therichmond4.co.uk`
- [ ] `journalctl -u chat-app -n 50`

### ✅ SSL Certificate Check
- [ ] `certbot certificates`
- [ ] Check expiry date
- [ ] Verify auto-renewal is enabled

### ✅ Monthly Maintenance
- [ ] Check disk space: `df -h`
- [ ] Check memory: `free -h`
- [ ] Review logs for errors
- [ ] Verify backups exist
- [ ] Check SSL certificate expiry
- [ ] Update system packages: `apt update && apt upgrade`
