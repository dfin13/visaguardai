# VisaGuard AI - Production Deployment Guide

This guide will help you deploy your Django application to a Hostinger VPS with Gunicorn, Nginx, and SSL.

## 🚀 Quick Deployment

### Prerequisites
- Hostinger VPS with Ubuntu/Debian
- Root access or sudo privileges
- Domain `visaguardai.com` pointing to your server IP
- Your project files uploaded to `/var/www/visaguardai`

### Step-by-Step Commands

#### 1. Upload Your Project Files
```bash
# From your local machine, upload the project to your server
scp -r /Users/davidfinney/Downloads/visaguardai/* root@your-server-ip:/var/www/visaguardai/
```

#### 2. Connect to Your Server
```bash
ssh root@your-server-ip
```

#### 3. Run the Deployment Script
```bash
cd /var/www/visaguardai
chmod +x deploy.sh
./deploy.sh
```

## 📋 Manual Deployment Steps

If you prefer to run commands manually:

### Step 1: System Setup
```bash
# Update system
apt update && apt upgrade -y

# Install required packages
apt install -y python3 python3-pip python3-venv nginx certbot python3-certbot-nginx ufw
```

### Step 2: Project Setup
```bash
# Create project directory
mkdir -p /var/www/visaguardai/logs
chown -R www-data:www-data /var/www/visaguardai
chmod -R 755 /var/www/visaguardai

# Navigate to project directory
cd /var/www/visaguardai

# Setup Python environment
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### Step 3: Django Configuration
```bash
# Collect static files
python manage.py collectstatic --noinput

# Run migrations
python manage.py migrate
```

### Step 4: Systemd Service
```bash
# Copy service file
cp visaguardai.service /etc/systemd/system/

# Enable and start service
systemctl daemon-reload
systemctl enable visaguardai.service
systemctl start visaguardai.service
```

### Step 5: Nginx Configuration
```bash
# Copy Nginx config
cp nginx.conf /etc/nginx/sites-available/visaguardai.com

# Remove default site
rm /etc/nginx/sites-enabled/default

# Enable new site
ln -s /etc/nginx/sites-available/visaguardai.com /etc/nginx/sites-enabled/

# Test and restart Nginx
nginx -t
systemctl restart nginx
```

### Step 6: SSL Certificate
```bash
# Get SSL certificate
certbot --nginx -d visaguardai.com -d www.visaguardai.com --non-interactive --agree-tos --email admin@visaguardai.com

# Setup auto-renewal
(crontab -l 2>/dev/null; echo "0 12 * * * /usr/bin/certbot renew --quiet") | crontab -
```

### Step 7: Firewall Setup
```bash
# Configure firewall
ufw allow 'Nginx Full'
ufw allow ssh
ufw --force enable
```

## 🔧 Configuration Files

### Gunicorn Configuration (`gunicorn.conf.py`)
- Socket communication: `unix:/var/www/visaguardai/visaguardai.sock`
- Worker processes: CPU cores * 2 + 1
- Logging to `/var/www/visaguardai/logs/`

### Nginx Configuration (`nginx.conf`)
- Reverse proxy to Gunicorn socket
- Static files served directly by Nginx
- SSL termination with Let's Encrypt
- Security headers included

### Systemd Service (`visaguardai.service`)
- Auto-restart on failure
- Runs as `www-data` user
- Automatic startup on boot

## 📊 Monitoring & Maintenance

### Check Service Status
```bash
# Check application status
systemctl status visaguardai.service

# Check Nginx status
systemctl status nginx

# View application logs
journalctl -u visaguardai.service -f

# View Nginx logs
tail -f /var/log/nginx/access.log
tail -f /var/log/nginx/error.log
```

### Restart Services
```bash
# Restart application
systemctl restart visaguardai.service

# Restart Nginx
systemctl restart nginx

# Restart both
systemctl restart visaguardai.service nginx
```

### Update Application
```bash
# Navigate to project directory
cd /var/www/visaguardai

# Activate virtual environment
source venv/bin/activate

# Pull latest changes (if using Git)
# git pull origin main

# Update dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Collect static files
python manage.py collectstatic --noinput

# Restart services
systemctl restart visaguardai.service
```

## 🔒 Security Considerations

1. **Firewall**: Only ports 22 (SSH), 80 (HTTP), and 443 (HTTPS) are open
2. **SSL**: Automatic HTTPS redirect and HSTS headers
3. **User Permissions**: Application runs as `www-data` user
4. **Static Files**: Served directly by Nginx for performance
5. **Logs**: Comprehensive logging for monitoring

## 🚨 Troubleshooting

### Common Issues

1. **Permission Denied**
   ```bash
   chown -R www-data:www-data /var/www/visaguardai
   chmod -R 755 /var/www/visaguardai
   ```

2. **Port Already in Use**
   ```bash
   # Check what's using port 80/443
   netstat -tulpn | grep :80
   netstat -tulpn | grep :443
   
   # Stop conflicting services
   systemctl stop apache2  # if Apache is running
   ```

3. **SSL Certificate Issues**
   ```bash
   # Check certificate status
   certbot certificates
   
   # Renew certificate manually
   certbot renew --dry-run
   ```

4. **Static Files Not Loading**
   ```bash
   # Check static files collection
   python manage.py collectstatic --noinput
   
   # Check Nginx configuration
   nginx -t
   ```

## 📈 Performance Optimization

1. **Enable Gzip Compression** (already configured in Nginx)
2. **Static File Caching** (already configured)
3. **Database Optimization**: Consider PostgreSQL for production
4. **CDN**: Use CloudFlare or similar for static assets
5. **Monitoring**: Set up monitoring with tools like New Relic or DataDog

## 🔄 Backup Strategy

```bash
# Database backup
python manage.py dumpdata > backup_$(date +%Y%m%d).json

# Media files backup
tar -czf media_backup_$(date +%Y%m%d).tar.gz media/

# Full project backup
tar -czf project_backup_$(date +%Y%m%d).tar.gz /var/www/visaguardai/
```

Your VisaGuard AI application is now production-ready! 🎉

