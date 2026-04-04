FROM node:20-alpine AS build

WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .

# --- Test stage ---
FROM build AS test
RUN npm run test -- --run --reporter=verbose

# --- Dev stage ---
FROM build AS dev
EXPOSE 5173
CMD ["npm", "run", "dev"]