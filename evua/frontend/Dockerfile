FROM node:20-alpine AS builder

WORKDIR /app

# Build-time argument (baked into the Vite bundle)
ARG VITE_API_BASE_URL=http://localhost:8000
ENV VITE_API_BASE_URL=${VITE_API_BASE_URL}

# Install dependencies
COPY package.json ./
RUN npm install

# Copy source and build
COPY . .
RUN npm run build

# --- Production image ---
FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html

# Nginx config: serve SPA (all routes → index.html) and proxy /api
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
