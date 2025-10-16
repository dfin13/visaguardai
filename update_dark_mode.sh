#!/bin/bash
# Update all templates for instant dark mode rendering

cd /var/www/visaguardai/templates

echo "Updating templates for instant dark mode..."

# Update auth/login.html
sed -i 's|<html lang="en" class="scroll-smooth">|<html lang="en" class="scroll-smooth dark">|' auth/login.html
sed -i '/<head>/a\    <script>document.documentElement.classList.add('\''dark'\'');localStorage.setItem('\''theme'\'','\''dark'\'');</script>' auth/login.html

# Update auth/signup.html
sed -i 's|<html lang="en" class="scroll-smooth">|<html lang="en" class="scroll-smooth dark">|' auth/signup.html
sed -i '/<head>/a\    <script>document.documentElement.classList.add('\''dark'\'');localStorage.setItem('\''theme'\'','\''dark'\'');</script>' auth/signup.html

# Update auth/forgot_password.html  
sed -i 's|<html lang="en" class="scroll-smooth">|<html lang="en" class="scroll-smooth dark">|' auth/forgot_password.html
sed -i '/<head>/a\    <script>document.documentElement.classList.add('\''dark'\'');localStorage.setItem('\''theme'\'','\''dark'\'');</script>' auth/forgot_password.html

# Update auth/reset_password.html
sed -i 's|<html lang="en" class="scroll-smooth">|<html lang="en" class="scroll-smooth dark">|' auth/reset_password.html
sed -i '/<head>/a\    <script>document.documentElement.classList.add('\''dark'\'');localStorage.setItem('\''theme'\'','\''dark'\'');</script>' auth/reset_password.html

# Update dashboard/dashboard.html
sed -i 's|<html lang="en" class="scroll-smooth">|<html lang="en" class="scroll-smooth dark">|' dashboard/dashboard.html
sed -i '/<head>/a\    <script>document.documentElement.classList.add('\''dark'\'');localStorage.setItem('\''theme'\'','\''dark'\'');</script>' dashboard/dashboard.html

# Update dashboard/settings.html
sed -i 's|<html lang="en" class="scroll-smooth">|<html lang="en" class="scroll-smooth dark">|' dashboard/settings.html
sed -i '/<head>/a\    <script>document.documentElement.classList.add('\''dark'\'');localStorage.setItem('\''theme'\'','\''dark'\'');</script>' dashboard/settings.html

# Update dashboard/result.html
sed -i 's|<html lang="en" class="scroll-smooth">|<html lang="en" class="scroll-smooth dark">|' dashboard/result.html
sed -i '/<head>/a\    <script>document.documentElement.classList.add('\''dark'\'');localStorage.setItem('\''theme'\'','\''dark'\'');</script>' dashboard/result.html

# Update home.html
sed -i 's|<html lang="en" class="scroll-smooth">|<html lang="en" class="scroll-smooth dark">|' ../home.html
sed -i '/<head>/a\    <script>document.documentElement.classList.add('\''dark'\'');localStorage.setItem('\''theme'\'','\''dark'\'');</script>' ../home.html

# Update tos.html
sed -i 's|<html lang="en" class="dark">|<html lang="en" class="scroll-smooth dark">|' ../tos.html
sed -i '/<head>/a\    <script>document.documentElement.classList.add('\''dark'\'');localStorage.setItem('\''theme'\'','\''dark'\'');</script>' ../tos.html

echo "✅ All templates updated"

cd /var/www/visaguardai

# Restart services
echo "Restarting services..."
systemctl restart visaguardai.service nginx

sleep 3

echo "✅ Complete"







