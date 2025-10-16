#!/bin/bash

# Fix Gunicorn service to use correct directory

echo "🔧 Updating Gunicorn service configuration..."

sudo tee /etc/systemd/system/gunicorn.service > /dev/null << 'SERVICE'
[Unit]
Description=gunicorn daemon
After=network.target

[Service]
User=root
Group=www-data
WorkingDirectory=/var/www/visaguardai
ExecStart=/var/www/visaguardai/venv/bin/gunicorn \
        --access-logfile - \
        --workers 3 \
        --bind unix:/run/gunicorn.sock \
        visaguardai.wsgi:application

[Install]
WantedBy=multi-user.target
SERVICE

echo "✅ Service file updated"

echo "🔄 Reloading systemd and restarting services..."
sudo systemctl daemon-reload
sudo systemctl restart gunicorn nginx

echo "📊 Service status:"
sudo systemctl status gunicorn --no-pager | head -10

echo ""
echo "✅ DONE! Gunicorn now runs from /var/www/visaguardai"
echo ""
echo "🧪 Test Twitter analysis now at: https://visaguardai.com/dashboard/"
