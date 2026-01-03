# Build stage
FROM docker.io/library/node:20-slim AS build

WORKDIR /app

COPY package*.json ./
RUN npm install --legacy-peer-deps

COPY . .
RUN npm run build

# Serve stage
FROM docker.io/library/nginx:alpine

# The build goes to dist/ because of angular.json outputPath settings
COPY --from=build /app/dist /usr/share/nginx/html

# Add custom nginx config for SPA routing
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
