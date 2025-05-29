FROM node:20-alpine AS dev
WORKDIR /app
COPY frontend/package.json ./
RUN npm install

# copy the rest of the app
COPY frontend/ .
EXPOSE 3000
CMD ["npm", "start"]
