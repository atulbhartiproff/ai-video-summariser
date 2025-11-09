# ---- Build Stage ----
FROM oven/bun:1.3.1 AS build

WORKDIR /frontend

# Build argument for API URL
ARG VITE_API_URL=http://localhost:5000
ENV VITE_API_URL=$VITE_API_URL

# Copy dependency manifests first (for caching)
COPY package*.json ./

# Install dependencies
RUN bun install --ignore-scripts

# Copy the rest of the frontend source code
COPY . .

# Build static production files (Vite output)
RUN bun run build

# ---- Serve Stage ----
FROM nginx:alpine

# Copy compiled output from build stage to nginx html folder
COPY --from=build /frontend/dist /usr/share/nginx/html

# Custom nginx config for single-page apps (React/Vite)
# Includes reverse proxy for API calls (configurable at runtime)
RUN rm /etc/nginx/conf.d/default.conf

# Create nginx config template that will be processed at runtime
COPY <<EOF /etc/nginx/templates/default.conf.template
server {
    listen 80;
    server_name _;
    root /usr/share/nginx/html;
    index index.html;
    
    # Increase max upload size (default is 1MB, set to 500MB for video files)
    client_max_body_size 500M;
    
    # Increase buffer sizes for large uploads
    client_body_buffer_size 128k;
    
    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css text/xml text/javascript application/x-javascript application/xml+rss application/json;
    
    # Proxy API requests to backend
    # __BACKEND_URL__ will be replaced at runtime via sed
    location /api/ {
        proxy_pass __BACKEND_URL__/api/;
        proxy_redirect off;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_cache_bypass \$http_upgrade;
        proxy_read_timeout 300s;
        proxy_connect_timeout 75s;
        
        # Increase timeouts for large file uploads
        proxy_request_buffering off;
        proxy_buffering off;
    }
    
    # Proxy health check endpoint
    location /health {
        proxy_pass __BACKEND_URL__/health;
        proxy_redirect off;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
    }
    
    # Serve frontend files
    location / {
        try_files \$uri /index.html;
    }
}
EOF

# Create entrypoint script to generate nginx config from template
COPY <<'SCRIPT' /docker-entrypoint.sh
#!/bin/sh
set -e

# Default backend URL (can be overridden via environment variable)
export BACKEND_URL=${BACKEND_URL:-http://localhost:5000}

# Validate BACKEND_URL is set and not empty
if [ -z "$BACKEND_URL" ]; then
    echo "ERROR: BACKEND_URL environment variable is not set!"
    exit 1
fi

# Remove trailing slash from BACKEND_URL if present
BACKEND_URL=$(echo "$BACKEND_URL" | sed 's|/$||')
export BACKEND_URL

echo "Using BACKEND_URL: $BACKEND_URL"

# Replace BACKEND_URL placeholder in nginx config template
# Use sed to replace __BACKEND_URL__ placeholder with actual value
sed "s|__BACKEND_URL__|$BACKEND_URL|g" /etc/nginx/templates/default.conf.template > /etc/nginx/conf.d/default.conf

# Validate generated nginx config
if ! nginx -t; then
    echo "ERROR: Generated nginx configuration is invalid!"
    echo "Generated config:"
    cat /etc/nginx/conf.d/default.conf
    exit 1
fi

echo "Nginx configuration validated successfully"

# Start nginx
exec nginx -g 'daemon off;'
SCRIPT

RUN chmod +x /docker-entrypoint.sh

# Expose port 80
EXPOSE 80

# Use custom entrypoint
ENTRYPOINT ["/docker-entrypoint.sh"]

