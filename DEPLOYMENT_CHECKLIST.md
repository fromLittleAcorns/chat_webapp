# Quick Deployment Checklist

Use this as a quick reference when deploying to production.

## Pre-Deployment (On Local Machine)

- [ ] All code changes committed and pushed to GitHub
- [ ] `.prod_env` updated with correct production values
- [ ] `ADMIN_PASSWORD` in `.prod_env` is strong and secure
- [ ] `ANTHROPIC_API_KEY` in `.prod_env` is correct

## Deployment (On Production Server)

```bash
# 1. Connect and become root
ssh john@217.154.63.51
sudo su -

# 2. Navigate to app directory
cd /var/www/vhosts/therichmond4.co.uk/chat.therichmond4.co.uk/chat_webapp

# 3. Pull latest code
git pull

# 4. Setup venv (if not already done)
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 5. Setup .env (first time only)
# Upload .prod_env from local machine via SFTP, then:
cp .prod_env .env
nano .env  # Verify/update values

# 6. Run database setup (first time only)
python setup_db.py

# 7. Fix ownership
cd ..
chown -R therichmond4.co.uk_6213ltvyukj:psacln chat_webapp/

# 8. Setup systemd service (first time only)
# Create /etc/systemd/system/chat-app.service (see DEPLOYMENT_GUIDE.md)

# 9. Start/restart service
systemctl daemon-reload
systemctl enable chat-app
systemctl restart chat-app

# 10. Check status
systemctl status chat-app
journalctl -u chat-app -n 20
```

## Post-Deployment Verification

- [ ] Service shows "active (running)": `systemctl status chat-app`
- [ ] No errors in logs: `journalctl -u chat-app -n 50`
- [ ] Port 8000 is listening: `ss -tlnp | grep 8000`
- [ ] Can access via browser: https://chat.therichmond4.co.uk
- [ ] Can login with admin credentials from .env
- [ ] WebSocket connections work (test chat functionality)

## Post-First-Login Security

- [ ] Login to app with admin credentials
- [ ] Change admin password through the app UI
- [ ] Optionally remove `ADMIN_PASSWORD` from production .env:
  ```bash
  nano /var/www/vhosts/.../chat_webapp/.env
  # Comment out or remove ADMIN_PASSWORD line
  ```

## Future Code Updates

```bash
# Simple 3-step update process:
cd /var/www/vhosts/therichmond4.co.uk/chat.therichmond4.co.uk/chat_webapp
git pull
systemctl restart chat-app
```

## Troubleshooting Quick Reference

### Service won't start
```bash
journalctl -u chat-app -n 50  # Check error logs
systemctl status chat-app     # Check service status
```

### Permission errors
```bash
chown -R therichmond4.co.uk_6213ltvyukj:psacln /var/www/.../chat_webapp/
chmod 600 .env
```

### Can't connect to site
```bash
systemctl status chat-app     # Is service running?
ss -tlnp | grep 8000          # Is port listening?
curl http://localhost:8000    # Test locally
# Check nginx config in Plesk
```

### Database errors
```bash
ls -la data/                  # Check database files exist
# Re-run setup if needed:
python setup_db.py
```

## Key File Locations

| What | Where |
|------|-------|
| App code | `/var/www/vhosts/therichmond4.co.uk/chat.therichmond4.co.uk/chat_webapp/` |
| Config | `chat_webapp/.env` |
| Databases | `chat_webapp/data/` |
| Venv | `chat_webapp/venv/` |
| Service file | `/etc/systemd/system/chat-app.service` |
| Logs | `journalctl -u chat-app` |

## Important Commands

| Task | Command |
|------|---------|
| Restart app | `systemctl restart chat-app` |
| Check status | `systemctl status chat-app` |
| View logs | `journalctl -u chat-app -f` |
| Check port | `ss -tlnp \| grep 8000` |
| Test locally | `curl http://localhost:8000` |
| Fix ownership | `chown -R therichmond4.co.uk_6213ltvyukj:psacln chat_webapp/` |
