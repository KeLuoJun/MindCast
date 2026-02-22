# ── Stage 1: build ────────────────────────────────────────────────────────────
FROM node:18-alpine AS builder

WORKDIR /app

COPY package*.json ./
RUN npm ci --prefer-offline

COPY . .
RUN npm run build

# ── Stage 2: serve via nginx ──────────────────────────────────────────────────
FROM nginx:1.27-alpine AS runtime

# Remove default nginx site
RUN rm /etc/nginx/conf.d/default.conf

# Custom nginx config (includes /api proxy to backend service)
COPY nginx.conf /etc/nginx/conf.d/mindcast.conf

# Copy built SPA
COPY --from=builder /app/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
