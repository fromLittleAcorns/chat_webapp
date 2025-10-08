# FastHTML MCP Chat

Web-based chat interface for the MCP WooCommerce server, providing secure, authenticated access to product search capabilities via Claude.

## Features

- 🔒 **Secure Authentication** - Built with fasthtml-auth
- 💬 **Real-time Streaming** - Streaming responses via Server-Sent Events
- 🎨 **Markdown Support** - Rich text formatting and code highlighting
- 💾 **Conversation Management** - Save, load, and organize chats
- 📱 **Responsive Design** - Works on desktop and mobile
- 🔍 **Evidence-Based Search** - Reliable product information with source attribution
- 🚀 **No Local Setup for Users** - Browser-only access

## Architecture

```
┌─────────────────────────────────────┐
│         User Browser                │
│     (HTML/JavaScript/HTMX)          │
└──────────────┬──────────────────────┘
               │ HTTPS
               ▼
┌─────────────────────────────────────┐
│    FastHTML Web Application         │
│  ┌────────────┐  ┌───────────────┐  │
│  │fasthtml-auth│  │  Chat UI     │  │
│  └────────────┘  └───────────────┘  │
│  ┌───────────────────────────────┐  │
│  │   Anthropic SDK (MCP Client)  │  │
│  └───────────────────────────────┘  │
└──────────────┬──────────────────────┘
               │ Local stdio
               ▼
┌─────────────────────────────────────┐
│    MCP WooCommerce Server           │
│         (SQLite Database)           │
└─────────────────────────────────────┘
```

## Prerequisites

- Python 3.10+
- Working MCP WooCommerce server (separate project)
- Anthropic API key

## Quick Start

### 1. Clone Repository

```bash
git clone <your-repo-url> fasthtml-mcp-chat
cd fasthtml-mcp-chat
```

### 2. Create Virtual Environment

```bash
python -m venv venv

# Activate
# On Linux/Mac:
source venv/bin/activate
# On Windows:
venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment

```bash
# Copy example config
cp .env.example .env

# Edit .env with your settings
nano .env  # or use your preferred editor
```

**Required `.env` settings:**

```env
# CRITICAL: Change in production!
SECRET_KEY=your-random-secret-key-here

# Path to MCP server (relative or absolute)
MCP_SERVER_PATH=../mcp-woocommerce-server

# Anthropic API key
ANTHROPIC_API_KEY=sk-ant-...your-key-here

# Optional
DEBUG=True
PORT=5000
SESSION_EXPIRY=3600
```

### 5. Initialize Databases

```bash
python -c "from models import init_database; init_database()"
```

### 6. Validate Configuration

```bash
python config.py
```

Should output:
```
✓ Configuration is valid
============================================================
FastHTML MCP Chat Configuration
...
```

### 7. Run Application

**Development:**
```bash
python app.py
```

**Production:**
```bash
# Using uvicorn directly
uvicorn app:app --host 0.0.0.0 --port 5000 --workers 4
```

### 8. Access Application

Open browser to: `http://localhost:5000`

## Project Structure

```
fasthtml-mcp-chat/
├── app.py                    # Main application entry point
├── config.py                 # Configuration management
├── requirements.txt          # Python dependencies
├── .env                      # Environment variables (create from .env.example)
│
├── data/                     # Database files (auto-created)
│   ├── users.db             # User accounts
│   └── conversations.db     # Chat history
│
├── models/                   # Database models (fastlite)
│   ├── __init__.py          # Conversation & Message models
│
├── routes/                   # Route handlers
│   ├── __init__.py
│   ├── chat.py              # Chat interface routes
│   └── api.py               # API endpoints
│
├── services/                 # Business logic
│   ├── __init__.py
│   └── mcp_client.py        # MCP server connection
│
├── templates/                # UI components
│   ├── chat.py              # Chat page template
│   └── components.py        # Reusable components
│
├── static/                   # Static assets
│   └── css/
│       └── custom.css       # Custom styling
│
└── utils/                    # Utilities
    └── __init__.py
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `SECRET_KEY` | Session encryption key | MUST SET IN PRODUCTION |
| `MCP_SERVER_PATH` | Path to MCP server directory | `../mcp-woocommerce-server` |
| `ANTHROPIC_API_KEY` | Anthropic API key | Required |
| `DEBUG` | Debug mode | `False` |
| `HOST` | Server host | `0.0.0.0` |
| `PORT` | Server port | `5000` |
| `SESSION_EXPIRY` | Session timeout (seconds) | `3600` |
| `MAX_MESSAGE_LENGTH` | Max message characters | `10000` |
| `STREAMING_ENABLED` | Enable response streaming | `True` |

### Security

**CRITICAL for Production:**

1. **Change SECRET_KEY**: Generate random key:
   ```bash
   python -c "import secrets; print(secrets.token_hex(32))"
   ```

2. **Use HTTPS**: Deploy behind reverse proxy (nginx/Caddy)

3. **Set DEBUG=False**: Disable debug mode

4. **Secure database files**: Restrict file permissions:
   ```bash
   chmod 600 data/*.db
   ```

## Deployment

### Using systemd (Linux)

Create `/etc/systemd/system/mcp-chat.service`:

```ini
[Unit]
Description=FastHTML MCP Chat
After=network.target

[Service]
Type=simple
User=youruser
WorkingDirectory=/home/youruser/fasthtml-mcp-chat
Environment="PATH=/home/youruser/fasthtml-mcp-chat/venv/bin"
ExecStart=/home/youruser/fasthtml-mcp-chat/venv/bin/uvicorn app:app --host 0.0.0.0 --port 5000 --workers 4
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable mcp-chat
sudo systemctl start mcp-chat
sudo systemctl status mcp-chat
```

### Nginx Reverse Proxy

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # For SSE streaming
        proxy_buffering off;
        proxy_cache off;
        proxy_set_header Connection '';
        proxy_http_version 1.1;
        chunked_transfer_encoding off;
    }
}
```

### Docker (Optional)

Create `Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "5000"]
```

Build and run:
```bash
docker build -t mcp-chat .
docker run -p 5000:5000 -v $(pwd)/data:/app/data -e ANTHROPIC_API_KEY=your-key mcp-chat
```

## Usage

### For Users

1. **Register/Login**: Create account at `/register`
2. **Start Chat**: Click "New Chat" button
3. **Ask Questions**: Type product queries in the input box
4. **Review Responses**: Claude searches the database and provides evidence-based answers
5. **Manage Conversations**: 
   - Switch conversations from sidebar
   - Delete old conversations
   - Conversations auto-save

### Search Tips

**Good queries:**
- "polished chrome euro cylinder 70mm"
- "fire rated door handle lever rose"
- "marine grade 316 stainless steel pull"

**What makes queries work:**
- Core product type (cylinder, handle, hinge)
- Key specs (size, finish, material)
- Avoid overly generic terms

**Understanding responses:**
- ✓ CONFIRMED: Information verified in database
- ✗ NOT FOUND: Not in database
- ? REQUIRES VERIFICATION: Check with supplier

## Development

### Adding Features

1. **New route**: Add to `routes/chat.py` or `routes/api.py`
2. **Database model**: Extend `models/__init__.py`
3. **UI component**: Add to `templates/components.py`
4. **Styling**: Update `static/css/custom.css`

### Running Tests

```bash
# TODO: Add test suite
pytest tests/
```

### Code Style

```bash
# Format code
black .

# Type checking
mypy app.py models/ routes/ services/
```

## Troubleshooting

### MCP Server Not Found

**Error:** `MCP server path does not exist`

**Fix:** Update `MCP_SERVER_PATH` in `.env`:
```env
MCP_SERVER_PATH=/absolute/path/to/mcp-woocommerce-server
```

### Database Errors

**Error:** `table conversations already exists`

**Fix:** Delete and recreate:
```bash
rm data/conversations.db
python -c "from models import init_database; init_database()"
```

### Streaming Not Working

**Symptoms:** Responses appear all at once, not progressively

**Fix:** Check nginx buffering settings:
```nginx
proxy_buffering off;
proxy_cache off;
```

### Session Expires Too Quickly

**Fix:** Increase timeout in `.env`:
```env
SESSION_EXPIRY=7200  # 2 hours
```

## Maintenance

### Backup Databases

```bash
# Automated backup script
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
tar -czf backup_${DATE}.tar.gz data/*.db
```

### Clean Old Conversations

```python
from models import cleanup_old_conversations

# Delete conversations inactive for 90 days
deleted = cleanup_old_conversations(days=90)
print(f"Deleted {deleted} old conversations")
```

### Monitor Logs

```bash
# Application logs
tail -f app.log

# Systemd logs
journalctl -u mcp-chat -f
```

## API Reference

### Authentication Endpoints

- `GET /login` - Login page
- `POST /login` - Submit login
- `GET /register` - Registration page
- `POST /register` - Submit registration
- `GET /logout` - Logout

### Chat Endpoints

- `GET /chat` - Main chat interface
- `GET /chat/{id}` - Load specific conversation
- `POST /api/chat/send` - Send message
- `GET /api/chat/stream` - Stream response (SSE)

### Conversation Management

- `POST /api/conversations/new` - Create conversation
- `DELETE /api/conversations/{id}` - Delete conversation
- `POST /api/conversations/{id}/rename` - Rename conversation
- `GET /api/conversations/list` - List conversations

## License

[Your License Here]

## Support

For issues or questions:
- GitHub Issues: [Your Repo]
- Email: [Your Email]

## Acknowledgments

- Built with [FastHTML](https://fastht.ml/)
- Authentication via [fasthtml-auth](https://pypi.org/project/fasthtml-auth/)
- AI by [Anthropic Claude](https://anthropic.com/)
- Styling with [Pico CSS](https://picocss.com/)