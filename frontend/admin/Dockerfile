# Build stage
FROM docker.io/library/node:22-slim AS build

WORKDIR /app

# Copy root package files and install (needed for shared components)
COPY package*.json ./
RUN npm ci

# Copy admin package files and install
COPY admin/package*.json ./admin/
WORKDIR /app/admin
RUN npm ci

# Go back to /app to copy everything
WORKDIR /app
COPY . .

# Build from admin directory
WORKDIR /app/admin
ARG VITE_ADMIN_API_URL=/api
ENV VITE_ADMIN_API_URL=$VITE_ADMIN_API_URL

ARG VITE_ADMIN_SECRET_KEY
ENV VITE_ADMIN_SECRET_KEY=$VITE_ADMIN_SECRET_KEY

RUN npm run build

# Production stage
FROM docker.io/library/nginx:alpine AS production

COPY --from=build /app/admin/dist /usr/share/nginx/html
COPY admin/nginx.conf /etc/nginx/templates/default.conf.template

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD wget --quiet --tries=1 --spider http://localhost/ || exit 1

CMD ["nginx", "-g", "daemon off;"]
