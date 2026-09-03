FROM node:20-slim AS builder

WORKDIR /app

COPY src/frontend/package*.json ./
RUN npm ci

COPY src/frontend .
RUN npm run build

FROM nginx:1.27-alpine

WORKDIR /app

COPY --from=builder /app/dist .
COPY --from=builder /app/dist /usr/share/nginx/html
COPY docker/frontend/nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 3000

CMD ["nginx", "-g", "daemon off;"]
