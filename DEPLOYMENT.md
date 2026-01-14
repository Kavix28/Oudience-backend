# 🚀 Deployment Guide

## Quick Deployment Steps

### 1. Local Development

```bash
# Clone repository
git clone https://github.com/yourusername/oudience-ai-assistant.git
cd oudience-ai-assistant

# Setup virtual environment
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Run application
python app.py
```

### 2. Production Deployment

#### Using Waitress (Recommended)

Already included in `requirements.txt`. Modify `app.py`:

```python
if __name__ == "__main__":
    from waitress import serve
    print("🚀 Starting Oudience AI Assistant on port 5002...")
    serve(app, host='0.0.0.0', port=5002, threads=4)
```

#### Using Gunicorn (Linux)

```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5002 app:app
```

### 3. Environment Variables

Create `.env` file:

```env
ADMIN_TOKEN=your-super-secure-token-here
FLASK_SECRET_KEY=your-secret-key-here
PORT=5002
UPLOAD_DIR=uploads_exp
KB_FILE=knowledge_base_exp.json
```

Update `app.py` to use environment variables:

```python
import os
from dotenv import load_dotenv

load_dotenv()

ADMIN_TOKEN = os.getenv('ADMIN_TOKEN', 'admin123')
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'oudience-secret-key')
```

### 4. Nginx Configuration

```nginx
server {
    listen 80;
    server_name yourdomain.com;

    location / {
        proxy_pass http://127.0.0.1:5002;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static {
        alias /path/to/oudience-ai-assistant/static;
        expires 30d;
    }
}
```

### 5. SSL with Let's Encrypt

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d yourdomain.com
```

### 6. Systemd Service (Linux)

Create `/etc/systemd/system/oudience.service`:

```ini
[Unit]
Description=Oudience AI Assistant
After=network.target

[Service]
User=www-data
WorkingDirectory=/path/to/oudience-ai-assistant
Environment="PATH=/path/to/oudience-ai-assistant/.venv/bin"
ExecStart=/path/to/oudience-ai-assistant/.venv/bin/python app.py
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl enable oudience
sudo systemctl start oudience
sudo systemctl status oudience
```

### 7. Docker Deployment

Create `Dockerfile`:

```dockerfile
FROM python:3.9-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Create necessary directories
RUN mkdir -p uploads_exp flask_sessions data/processed data/raw

# Expose port
EXPOSE 5002

# Run application
CMD ["python", "app.py"]
```

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  oudience:
    build: .
    ports:
      - "5002:5002"
    volumes:
      - ./uploads_exp:/app/uploads_exp
      - ./flask_sessions:/app/flask_sessions
      - ./knowledge_base_exp.json:/app/knowledge_base_exp.json
      - ./upload_logs.json:/app/upload_logs.json
    environment:
      - ADMIN_TOKEN=${ADMIN_TOKEN}
      - FLASK_SECRET_KEY=${FLASK_SECRET_KEY}
    restart: unless-stopped
```

Deploy:

```bash
docker-compose up -d
```

### 8. Cloud Deployment

#### Heroku

```bash
# Install Heroku CLI
heroku login
heroku create oudience-ai-assistant

# Add Procfile
echo "web: python app.py" > Procfile

# Deploy
git push heroku main
```

#### AWS EC2

1. Launch EC2 instance (Ubuntu)
2. SSH into instance
3. Install dependencies:
```bash
sudo apt update
sudo apt install python3-pip python3-venv nginx
```
4. Clone repository and setup
5. Configure Nginx as reverse proxy
6. Setup systemd service

#### DigitalOcean

Similar to AWS EC2, use their App Platform for easier deployment.

### 9. Monitoring

#### Setup Logging

Add to `app.py`:

```python
import logging
from logging.handlers import RotatingFileHandler

if not app.debug:
    file_handler = RotatingFileHandler('oudience.log', maxBytes=10240, backupCount=10)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)
    app.logger.info('Oudience startup')
```

#### Health Check Endpoint

Add to `app.py`:

```python
@app.route("/health")
def health_check():
    return jsonify({
        "status": "healthy",
        "timestamp": time.time(),
        "kb_loaded": kb_embeddings is not None,
        "total_chunks": len(kb_docs)
    })
```

### 10. Backup Strategy

```bash
#!/bin/bash
# backup.sh

BACKUP_DIR="/backups/oudience"
DATE=$(date +%Y%m%d_%H%M%S)

# Backup knowledge base
cp knowledge_base_exp.json "$BACKUP_DIR/kb_$DATE.json"

# Backup upload logs
cp upload_logs.json "$BACKUP_DIR/logs_$DATE.json"

# Backup PDFs
tar -czf "$BACKUP_DIR/pdfs_$DATE.tar.gz" uploads_exp/

# Keep only last 30 days
find $BACKUP_DIR -mtime +30 -delete
```

Add to crontab:
```bash
0 2 * * * /path/to/backup.sh
```

### 11. Performance Optimization

#### Enable Caching

```python
from flask_caching import Cache

cache = Cache(app, config={'CACHE_TYPE': 'simple'})

@app.route("/query", methods=["POST"])
@cache.cached(timeout=300, query_string=True)
def query():
    # ... existing code
```

#### Use Redis for Sessions

```python
app.config["SESSION_TYPE"] = "redis"
app.config["SESSION_REDIS"] = redis.from_url("redis://localhost:6379")
```

### 12. Security Checklist

- [ ] Change default admin token
- [ ] Use HTTPS in production
- [ ] Enable CORS properly
- [ ] Add rate limiting
- [ ] Implement CSRF protection
- [ ] Use environment variables
- [ ] Regular security updates
- [ ] Monitor logs for suspicious activity
- [ ] Backup data regularly
- [ ] Use strong session secrets

### 13. Troubleshooting

**Port already in use:**
```bash
# Windows
netstat -ano | findstr :5002
taskkill /PID <PID> /F

# Linux
lsof -i :5002
kill -9 <PID>
```

**Permission errors:**
```bash
sudo chown -R $USER:$USER /path/to/oudience-ai-assistant
chmod -R 755 /path/to/oudience-ai-assistant
```

**Memory issues:**
```python
# Reduce model size or use quantization
embedder = SentenceTransformer("all-MiniLM-L6-v2", device='cpu')
```

---

**Need help?** Open an issue on GitHub!
