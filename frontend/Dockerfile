FROM node:22-alpine AS build
WORKDIR /app
COPY frontend/package.json ./
COPY frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
COPY teams/index.html ./legacy/index.html
COPY teams/teams.js ./public/teams-assets/teams.js
COPY teams/teams.css ./public/teams-assets/teams.css
RUN npm run build
FROM node:22-alpine
WORKDIR /app
COPY --from=build /app ./
CMD ["npm", "start"]
