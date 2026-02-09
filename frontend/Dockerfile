# Multi-stage build for React + Vite frontend

FROM docker.io/library/node:22-slim AS build

# Build argument for API URL (default to Render prod)
ARG VITE_API_URL=/api

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci --only=production=false

# Copy source code
COPY . .

# Set environment variable
ENV VITE_API_URL=$VITE_API_URL

# Run linting and type checking
RUN npm run lint
RUN npm run typecheck

# Build production bundle
RUN npm run build


# Production stage with nginx
FROM docker.io/library/nginx:alpine AS production

# Copy built assets from build stage
COPY --from=build /app/dist /usr/share/nginx/html

# Copy nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Expose port 80
EXPOSE 80

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD wget --quiet --tries=1 --spider http://localhost/ || exit 1

# Start nginx
CMD ["nginx", "-g", "daemon off;"]
