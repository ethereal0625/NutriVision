# Stage 1: Build
FROM node:22-alpine AS builder
WORKDIR /app
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ .
RUN npm run build

# Stage 2: Serve with Nginx
# nginx.conf is a template using BACKEND_HOST/BACKEND_PORT; the official
# nginx image runs envsubst on files in /etc/nginx/templates/ at startup,
# so the proxy target is configurable via env without rebuilding the image.
FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY frontend/nginx.conf /etc/nginx/templates/default.conf.template
ENV BACKEND_HOST=backend
ENV BACKEND_PORT=8000
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
