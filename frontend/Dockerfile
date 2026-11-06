# Build stage
FROM node:20-alpine AS builder

WORKDIR /usr/src/covakeel

# Copy package files
COPY package.json package-lock.json ./

# Install the locked dependencies used by the local build
RUN npm ci

# Copy source code
COPY . .

# Accept build arguments
ARG VITE_API_BASE_URL
ENV VITE_API_BASE_URL=${VITE_API_BASE_URL}

# Build the application
RUN npm run build && test -s dist/index.html && test -s dist/app/index.html && test -s dist/admin/index.html

# Production stage
FROM nginx:alpine

# Copy built files from builder stage
COPY --from=builder /usr/src/covakeel/dist /usr/share/nginx/html

# Copy custom nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Expose port
EXPOSE 80

# Start nginx
CMD ["nginx", "-g", "daemon off;"]
