# Build stage
FROM docker.io/library/node:22-slim AS build

# ARG permite override: docker build --build-arg BUILD_MODE=production
ARG BUILD_MODE=development

WORKDIR /app

COPY package*.json ./
RUN npm ci --legacy-peer-deps

COPY . .

# Usa a variável BUILD_MODE para decidir o tipo de build
RUN npx ng build --configuration ${BUILD_MODE}

# Serve stage
FROM docker.io/library/nginx:alpine

# The build goes to dist/ because of angular.json outputPath settings
COPY --from=build /app/dist /usr/share/nginx/html

# Add custom nginx config for SPA routing
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
