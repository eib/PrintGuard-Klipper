# Stage 1: Build WebUI
FROM node:20-slim AS webui-builder
WORKDIR /app/webui
COPY webui/package*.json ./
RUN npm install
COPY webui/ ./
RUN npm run build

# Stage 2: Runtime
FROM python:3.13-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive \
    PORT=8000

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    gnupg \
    build-essential \
    libavdevice-dev \
    libavfilter-dev \
    libopus-dev \
    libvpx-dev \
    pkg-config \
    libsrtp2-dev \
    && ARCH=$(dpkg --print-architecture) \
    && curl -L -o /tmp/cloudflared.deb "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-${ARCH}.deb" \
    && dpkg -i /tmp/cloudflared.deb \
    && rm /tmp/cloudflared.deb \
    && rm -rf /var/lib/apt/lists/*

# Set work directory
WORKDIR /app

# Copy project configuration files
COPY pyproject.toml .
COPY src/printguard/requirements.txt src/printguard/requirements.txt

# Copy printguard-shared (required for local dependency)
COPY printguard-shared/ ./printguard-shared/

# Install printguard-shared first
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir ./printguard-shared/

# Copy source code (needed to build the main package)
COPY src/ ./src/

# Install Python dependencies and main package
RUN pip install --no-cache-dir .

# Copy built WebUI from Stage 1
COPY --from=webui-builder /app/webui/dist ./webui/dist

# Copy the rest of the application
COPY . .

# Install the project in editable mode or just ensure scripts are installed
RUN pip install --no-cache-dir .

# Expose the port the app runs on
EXPOSE $PORT

# Command to run the application
ENTRYPOINT ["printguard"]
CMD ["serve"]
