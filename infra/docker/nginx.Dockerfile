# Build React (prod) then serve via Nginx
FROM node:20-alpine AS build-frontend
WORKDIR /app
COPY frontend/package.json ./
RUN npm install
COPY frontend/ .
RUN npm run build

FROM nginx:1.27-alpine
COPY infra/nginx/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build-frontend /app/build /usr/share/nginx/html

