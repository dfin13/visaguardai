#!/bin/bash

# VisaGuard AI Django Deployment Script for Hostinger VPS
# Run this script as root or with sudo privileges

set -e  # Exit on any error

echo "🚀 Starting VisaGuard AI deployment..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
DOMAIN="visaguardai.com"
PROJECT_DIR="/var/www/visaguardai"
NGINX_SITES_AVAILABLE="/etc/nginx/sites-available"
NGINX_SITES_ENABLED="/etc/nginx/sites-enabled"
SYSTEMD_SERVICE="/etc/systemd/system/visaguardai.service"

echo -e "${BLUE}📋 Deployment Configuration:${NC}"
echo "Domain: $DOMAIN"
echo "Project Directory: $PROJECT_DIR"
echo "Nginx Config: $NGINX_SITES_AVAILABLE/$DOMAIN"
echo "Systemd Service: $SYSTEMD_SERVICE"
echo ""

# Step 1: Update system packages
echo -e "${YELLOW}📦 Step 1: Updating system packages...${NC}"
apt update && apt upgrade -y

# Step 2: Install required packages
echo -e "${YELLOW}📦 Step 2: Installing required packages...${NC}"
apt install -y python3 python3-pip python3-venv nginx certbot python3-certbot-nginx ufw

# Step 3: Create project directory and setup permissions
echo -e "${YELLOW}📁 Step 3: Setting up project directory...${NC}"
mkdir -p $PROJECT_DIR
mkdir -p $PROJECT_DIR/logs
chown -R www-data:www-data $PROJECT_DIR
chmod -R 755 $PROJECT_DIR

# Step 4: Copy project files (assuming they're already uploaded to /var/www/visaguardai)
echo -e "${YELLOW}📁 Step 4: Setting up project files...${NC}"
# Note: Make sure your project files are already in $PROJECT_DIR
# If uploading from local machine, use scp or rsync:
# scp -r /path/to/local/visaguardai/* root@your-server-ip:/var/www/visaguardai/

# Step 5: Setup Python virtual environment and install dependencies
echo -e "${YELLOW}🐍 Step 5: Setting up Python environment...${NC}"
cd $PROJECT_DIR
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Step 6: Setup Django
echo -e "${YELLOW}⚙️  Step 6: Configuring Django...${NC}"
python manage.py collectstatic --noinput
python manage.py migrate

# Step 7: Create systemd service
echo -e "${YELLOW}🔧 Step 7: Creating systemd service...${NC}"
cp $PROJECT_DIR/visaguardai.service $SYSTEMD_SERVICE
systemctl daemon-reload
systemctl enable visaguardai.service

# Step 8: Configure Nginx
echo -e "${YELLOW}🌐 Step 8: Configuring Nginx...${NC}"
cp $PROJECT_DIR/nginx.conf $NGINX_SITES_AVAILABLE/$DOMAIN

# Remove default Nginx site if it exists
if [ -f "$NGINX_SITES_ENABLED/default" ]; then
    rm $NGINX_SITES_ENABLED/default
fi

# Enable the new site
ln -sf $NGINX_SITES_AVAILABLE/$DOMAIN $NGINX_SITES_ENABLED/$DOMAIN

# Test Nginx configuration
nginx -t

# Step 9: Configure firewall
echo -e "${YELLOW}🔥 Step 9: Configuring firewall...${NC}"
ufw allow 'Nginx Full'
ufw allow ssh
ufw --force enable

# Step 10: Start services
echo -e "${YELLOW}🚀 Step 10: Starting services...${NC}"
systemctl start visaguardai.service
systemctl restart nginx

# Step 11: Setup SSL with Let's Encrypt
echo -e "${YELLOW}🔒 Step 11: Setting up SSL certificate...${NC}"
certbot --nginx -d $DOMAIN -d www.$DOMAIN --non-interactive --agree-tos --email admin@$DOMAIN

# Step 12: Setup automatic SSL renewal
echo -e "${YELLOW}🔄 Step 12: Setting up SSL auto-renewal...${NC}"
(crontab -l 2>/dev/null; echo "0 12 * * * /usr/bin/certbot renew --quiet") | crontab -

# Step 13: Final service restart
echo -e "${YELLOW}🔄 Step 13: Final service restart...${NC}"
systemctl restart visaguardai.service
systemctl restart nginx

# Step 14: Verify deployment
echo -e "${GREEN}✅ Step 14: Verifying deployment...${NC}"
echo "Checking services status:"
systemctl status visaguardai.service --no-pager -l
systemctl status nginx --no-pager -l

echo ""
echo -e "${GREEN}🎉 Deployment completed successfully!${NC}"
echo ""
echo -e "${BLUE}📋 Next Steps:${NC}"
echo "1. Visit https://$DOMAIN to see your site"
echo "2. Check logs if needed:"
echo "   - Application: tail -f $PROJECT_DIR/logs/gunicorn_error.log"
echo "   - Nginx: tail -f /var/log/nginx/error.log"
echo "3. Monitor services:"
echo "   - systemctl status visaguardai.service"
echo "   - systemctl status nginx"
echo ""
echo -e "${BLUE}🛠️  Useful Commands:${NC}"
echo "- Restart app: systemctl restart visaguardai.service"
echo "- Restart Nginx: systemctl restart nginx"
echo "- View app logs: journalctl -u visaguardai.service -f"
echo "- View Nginx logs: tail -f /var/log/nginx/access.log"
echo ""
echo -e "${GREEN}🚀 Your VisaGuard AI is now live at https://$DOMAIN!${NC}"

