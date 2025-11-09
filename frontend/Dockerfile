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
# Ensures client-side routing works
RUN rm /etc/nginx/conf.d/default.conf
COPY <<EOF /etc/nginx/conf.d/default.conf
server {
    listen 80;
    server_name _;
    root /usr/share/nginx/html;
    index index.html;
    
    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css text/xml text/javascript application/x-javascript application/xml+rss application/json;
    
    location / {
        try_files \$uri /index.html;
    }
}
EOF

# Expose port 80
EXPOSE 80

# Run nginx
CMD ["nginx", "-g", "daemon off;"]

