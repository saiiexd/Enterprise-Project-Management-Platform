FROM node:20-alpine AS base

# Install dependencies only when needed
WORKDIR /app

# Install compat layer if needed
RUN apk add --no-cache libc6-compat

# Install dependencies
COPY package.json package-lock.json ./
RUN npm ci

# Copy sources
COPY . .

# Expose port and run dev
EXPOSE 3000
ENV PORT 3000
ENV HOSTNAME "0.0.0.0"

CMD ["npm", "run", "dev"]
