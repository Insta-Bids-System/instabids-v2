# Frontend Dockerfile for InstaBids
FROM node:20-alpine

WORKDIR /app

# Copy package files first for better caching
COPY package*.json ./
RUN npm install

# Copy source code
COPY . .

# Expose port
EXPOSE 5173

# Development command (overridden in docker-compose)
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]