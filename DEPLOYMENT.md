# 🚀 Deployment Guide

This guide covers deploying Bharat Biz-Agent to production for Neurathon 2026.

## Deployment Options

### Option 1: Railway (Recommended for Demo)
**Pros**: Free tier, easy setup, automatic HTTPS  
**Cons**: Limited resources on free tier

#### Steps:
1. Sign up at [railway.app](https://railway.app)
2. Click "New Project" → "Deploy from GitHub"
3. Connect your repository
4. Add environment variables:
   ```
   WHATSAPP_VERIFY_TOKEN=your_token
   WHATSAPP_TOKEN=your_whatsapp_token
   WHATSAPP_PHONE_NUMBER_ID=your_phone_id
   GEMINI_API_KEY=your_gemini_key
   ```
5. Deploy!
6. Copy the generated URL (e.g., `https://your-app.railway.app`)
7. Configure WhatsApp webhook with this URL

### Option 2: Render
**Pros**: Free tier with persistent storage, easy SSL  
**Cons**: Slower cold starts

#### Steps:
1. Go to [render.com](https://render.com)
2. New → Web Service
3. Connect GitHub repository
4. Configure:
   - **Build Command**: `pip install -r requirements.txt && python database.py`
   - **Start Command**: `uvicorn app:app --host 0.0.0.0 --port $PORT`
5. Add environment variables (same as above)
6. Create
7. Use the provided URL for WhatsApp webhook

### Option 3: Heroku
**Pros**: Well-documented, scalable  
**Cons**: Paid plans required for production

#### Additional Files Needed:

**Procfile**:
```
web: uvicorn app:app --host 0.0.0.0 --port $PORT
```

**runtime.txt**:
```
python-3.11.7
```

#### Steps:
1. Install Heroku CLI
2. Login: `heroku login`
3. Create app: `heroku create bharat-biz-agent`
4. Set environment variables:
   ```bash
   heroku config:set WHATSAPP_VERIFY_TOKEN=your_token
   heroku config:set WHATSAPP_TOKEN=your_token
   heroku config:set WHATSAPP_PHONE_NUMBER_ID=your_id
   heroku config:set GEMINI_API_KEY=your_key
   ```
5. Deploy:
   ```bash
   git push heroku main
   ```

### Option 4: AWS EC2 (For Production)
**Pros**: Full control, scalable  
**Cons**: More complex setup

#### Steps:

1. **Launch EC2 Instance**
   - AMI: Ubuntu 22.04 LTS
   - Instance type: t2.micro (free tier) or t2.small
   - Security group: Allow ports 22, 80, 443

2. **Connect and Setup**
   ```bash
   ssh -i your-key.pem ubuntu@your-ec2-ip
   
   # Update system
   sudo apt update && sudo apt upgrade -y
   
   # Install Python and dependencies
   sudo apt install python3.11 python3.11-venv python3-pip nginx -y
   
   # Clone your repo
   git clone https://github.com/your-repo/bharat-biz-agent.git
   cd bharat-biz-agent
   
   # Setup
   python3.11 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   
   # Create .env
   nano .env
   # (Add your credentials)
   
   # Initialize database
   python database.py
   ```

3. **Configure systemd Service**
   ```bash
   sudo nano /etc/systemd/system/bharat-biz-agent.service
   ```
   
   Add:
   ```ini
   [Unit]
   Description=Bharat Biz-Agent WhatsApp Service
   After=network.target

   [Service]
   Type=simple
   User=ubuntu
   WorkingDirectory=/home/ubuntu/bharat-biz-agent
   Environment="PATH=/home/ubuntu/bharat-biz-agent/venv/bin"
   ExecStart=/home/ubuntu/bharat-biz-agent/venv/bin/uvicorn app:app --host 0.0.0.0 --port 8000
   Restart=always

   [Install]
   WantedBy=multi-user.target
   ```

4. **Configure Nginx as Reverse Proxy**
   ```bash
   sudo nano /etc/nginx/sites-available/bharat-biz-agent
   ```
   
   Add:
   ```nginx
   server {
       listen 80;
       server_name your-domain.com;

       location / {
           proxy_pass http://127.0.0.1:8000;
           proxy_http_version 1.1;
           proxy_set_header Upgrade $http_upgrade;
           proxy_set_header Connection 'upgrade';
           proxy_set_header Host $host;
           proxy_cache_bypass $http_upgrade;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
       }
   }
   ```
   
   ```bash
   sudo ln -s /etc/nginx/sites-available/bharat-biz-agent /etc/nginx/sites-enabled/
   sudo nginx -t
   sudo systemctl restart nginx
   ```

5. **Setup SSL with Let's Encrypt**
   ```bash
   sudo apt install certbot python3-certbot-nginx -y
   sudo certbot --nginx -d your-domain.com
   ```

6. **Start Service**
   ```bash
   sudo systemctl start bharat-biz-agent
   sudo systemctl enable bharat-biz-agent
   sudo systemctl status bharat-biz-agent
   ```

### Option 5: DigitalOcean App Platform
**Pros**: Easy deployment, managed infrastructure  
**Cons**: Costs more than EC2

#### Steps:
1. Create account at [digitalocean.com](https://digitalocean.com)
2. Apps → Create App
3. Connect GitHub repository
4. Configure:
   - **Environment**: Python
   - **Build Command**: `pip install -r requirements.txt && python database.py`
   - **Run Command**: `uvicorn app:app --host 0.0.0.0 --port 8080`
5. Add environment variables
6. Deploy

## WhatsApp Configuration

After deployment, configure webhook in Meta Business:

1. Go to [developers.facebook.com](https://developers.facebook.com)
2. Your App → WhatsApp → Configuration
3. Webhook:
   - **Callback URL**: `https://your-domain.com/webhook`
   - **Verify Token**: (from your .env)
4. Subscribe to fields:
   - ✅ messages
5. Test by sending message to your WhatsApp Business number

## Database Backup Strategy

### Local Backup (Automated)
Create a cron job:

```bash
# Edit crontab
crontab -e

# Add daily backup at 2 AM
0 2 * * * cd /home/ubuntu/bharat-biz-agent && cp bharat_biz.db backups/bharat_biz_$(date +\%Y\%m\%d).db
```

### Cloud Backup (Recommended)
Add to your app:

```python
# backup.py
import boto3
from datetime import datetime

def backup_to_s3():
    s3 = boto3.client('s3')
    filename = f'bharat_biz_{datetime.now().strftime("%Y%m%d")}.db'
    s3.upload_file('bharat_biz.db', 'your-bucket', filename)
```

## Monitoring

### Option 1: Simple Health Check
Add to your crontab:
```bash
*/5 * * * * curl -f https://your-domain.com/ || echo "Service down!" | mail -s "Alert" your@email.com
```

### Option 2: UptimeRobot (Free)
1. Sign up at [uptimerobot.com](https://uptimerobot.com)
2. Add monitor:
   - Type: HTTP(s)
   - URL: `https://your-domain.com/`
   - Interval: 5 minutes
3. Configure alerts (email/SMS)

### Option 3: Sentry (Error Tracking)
```bash
pip install sentry-sdk
```

```python
# Add to app.py
import sentry_sdk
sentry_sdk.init(dsn="your-sentry-dsn")
```

## Performance Optimization

### 1. Enable Caching
```python
# Add to app.py
from functools import lru_cache

@lru_cache(maxsize=100)
def get_customer_cached(name: str):
    return get_customer_by_name(name)
```

### 2. Database Indexing
```python
# Add to database.py
cursor.execute("CREATE INDEX IF NOT EXISTS idx_customer_name ON customers(name)")
cursor.execute("CREATE INDEX IF NOT EXISTS idx_invoice_date ON invoices(invoice_date)")
```

### 3. Connection Pooling
```python
# Use connection pool for high traffic
import sqlite3
from contextlib import contextmanager

pool = []

@contextmanager
def get_db():
    conn = pool.pop() if pool else sqlite3.connect(DATABASE_PATH)
    try:
        yield conn
    finally:
        pool.append(conn)
```

## Security Checklist

- [ ] Environment variables are set (not in code)
- [ ] Webhook verify token is strong and secret
- [ ] HTTPS is enabled (SSL certificate)
- [ ] WhatsApp token has appropriate permissions only
- [ ] Database file is not in public directory
- [ ] Regular backups are automated
- [ ] Logs are rotated and monitored
- [ ] Rate limiting is configured
- [ ] Error messages don't expose sensitive info

## Scaling Considerations

### For High Traffic:
1. **Move to PostgreSQL**
   - Better concurrency
   - ACID compliance
   - Cloud hosting options

2. **Add Redis for Caching**
   - Session storage
   - Message queue
   - Rate limiting

3. **Use Celery for Background Tasks**
   - Async invoice generation
   - Scheduled reminders
   - Heavy processing

4. **Load Balancing**
   - Multiple app instances
   - Nginx or AWS ELB
   - Session stickiness

## Cost Estimates

### Free Tier (Demo/Testing)
- Railway: Free
- Render: Free
- Total: **₹0/month**

### Production (Small Business)
- DigitalOcean Droplet ($12/month): ₹1,000
- Domain + SSL (free with DigitalOcean): ₹0
- WhatsApp Business API: Free for basic usage
- Gemini API: Pay-as-you-go (~₹500/month for 1000 requests/day)
- Total: **~₹1,500/month**

### Production (Medium Business)
- AWS EC2 t2.small: ₹1,500
- RDS PostgreSQL: ₹2,000
- S3 Storage: ₹200
- CloudWatch: ₹300
- Total: **~₹4,000/month**

## Troubleshooting

### Issue: Webhook not receiving messages
**Solution:**
```bash
# Check if server is running
curl https://your-domain.com/

# Check logs
tail -f /var/log/nginx/error.log
journalctl -u bharat-biz-agent -f

# Verify WhatsApp webhook subscription
# In Meta Developer Console
```

### Issue: Database locked errors
**Solution:**
```python
# Increase timeout
conn = sqlite3.connect(DATABASE_PATH, timeout=30.0)

# Or migrate to PostgreSQL for production
```

### Issue: Slow response times
**Solution:**
- Enable caching
- Add database indexes
- Use async processing for heavy tasks
- Monitor with APM tool

## Demo Day Checklist

Before presenting at Neurathon:

- [ ] Server is deployed and accessible
- [ ] WhatsApp webhook is configured and tested
- [ ] Sample data is loaded in database
- [ ] Test all key features (invoice, payment, summary)
- [ ] Prepare demo script in Hindi/Hinglish
- [ ] Screenshots/videos ready
- [ ] Fallback plan (local demo) ready
- [ ] Team knows credentials and recovery steps

## Support

For deployment issues:
- Check logs first
- Verify environment variables
- Test API endpoints manually
- Review Meta developer console

Good luck with Neurathon 2026! 🚀
