#!/usr/bin/env python3
"""
Production server runner for FastHTML app
"""
import os
from dotenv import load_dotenv

load_dotenv()

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app:app",  # Your app module
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", 8000)),
        workers=int(os.getenv("WORKERS", 4)),
        log_level="info",
        access_log=True,
        proxy_headers=True,
        forwarded_allow_ips="*"  # Plesk reverse proxy
    )