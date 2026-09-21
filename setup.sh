#!/bin/bash

set -e

echo "==========================================="
echo "   Hines Django Project VPS Setup Script   "
echo "==========================================="

# Ask for domain
read -p "Enter the domain name or IP address for this site (e.g. hines.example.com or 123.45.67.89): " DOMAIN

echo "Generating random Django secret key..."
SECRET_KEY=$(openssl rand -base64 48 | tr -dc 'a-zA-Z0-9' | head -c 50)

echo "Creating .env file..."
cat <<EOF > .env
DJANGO_DEBUG=false
DJANGO_SECRET_KEY=${SECRET_KEY}
DJANGO_ALLOWED_HOSTS=${DOMAIN},127.0.0.1,localhost
EOF

echo "Checking if Docker is installed..."
if ! command -v docker &> /dev/null
then
    echo "Docker not found. Installing Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    rm get-docker.sh
else
    echo "Docker is already installed."
fi

echo "Checking if Docker Compose is installed..."
if ! command -v docker-compose &> /dev/null
then
    echo "Docker Compose not found. Installing..."
    sudo apt-get update -y
    sudo apt-get install -y docker-compose || sudo apt-get install -y docker-compose-plugin
else
    echo "Docker Compose is already installed."
fi

echo "Building and starting Docker containers..."
sudo docker-compose up -d --build

echo "==========================================="
read -p "Do you want to configure Nginx as a reverse proxy for port 80? (y/n): " CONFIGURE_NGINX

if [ "$CONFIGURE_NGINX" = "y" ] || [ "$CONFIGURE_NGINX" = "Y" ]; then
    echo "Installing Nginx if not present..."
    sudo apt-get update -y && sudo apt-get install -y nginx
    
    NGINX_CONF="/etc/nginx/sites-available/hines"
    echo "Creating Nginx configuration block at ${NGINX_CONF}..."
    
    cat <<EOF | sudo tee ${NGINX_CONF}
server {
    listen 80;
    server_name ${DOMAIN};

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF
    echo "Enabling the Nginx site..."
    sudo ln -sf ${NGINX_CONF} /etc/nginx/sites-enabled/
    
    echo "Restarting Nginx..."
    sudo systemctl restart nginx
    echo "Nginx configured successfully!"
fi

echo "================================================="
echo " Deployment Complete!"
echo " Your site should now be accessible at http://${DOMAIN}"
echo " If you configured Nginx, it is proxied on port 80."
echo " If not, it is running directly on port 8000."
echo "================================================="
