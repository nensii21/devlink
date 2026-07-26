# Stage 1 - Build
FROM node:20 AS builder

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .
# Build for a standard Node.js server rather than the Cloudflare default
ENV NITRO_PRESET=node-server
RUN npm run build

# Stage 2 - Production
FROM node:20-alpine

WORKDIR /app

# Copy built output from stage 1
COPY --from=builder /app/.output ./.output
COPY package*.json ./

# Install curl for healthcheck
RUN apk add --no-cache curl

EXPOSE 3000

ENV PORT=3000
ENV NODE_ENV=production

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD curl -f http://localhost:3000/ || exit 1

CMD ["node", ".output/server/index.mjs"]
