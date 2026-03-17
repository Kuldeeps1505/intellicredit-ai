# ── Stage 1: Build ────────────────────────────────────────────────────────
FROM node:20-alpine AS builder

WORKDIR /app

# Install dependencies first (better layer caching)
COPY package.json package-lock.json* ./
RUN npm ci

# Copy source and build
COPY . .
RUN npm run build          # outputs to /app/dist

# ── Stage 2: Serve ────────────────────────────────────────────────────────
FROM node:20-alpine

WORKDIR /app

# Use serve (lightweight static server) — no nginx needed
RUN npm install -g serve@14

COPY --from=builder /app/dist ./dist

EXPOSE 3000

# serve the Vite build output on port 3000
CMD ["serve", "-s", "dist", "-l", "3000"]