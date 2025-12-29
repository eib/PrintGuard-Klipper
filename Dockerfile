# =============================================================================
# Stage 1: Build WebUI
# =============================================================================
FROM node:20-slim AS webui-builder

WORKDIR /app/webui
COPY webui/package*.json ./
RUN npm ci
COPY webui/ ./
RUN npm run build

# =============================================================================
# Stage 2: Python Builder
# =============================================================================
FROM python:3.13-slim-bookworm AS python-builder

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl build-essential pkg-config \
    libavdevice-dev libavfilter-dev libopus-dev libvpx-dev libsrtp2-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
ENV UV_COMPILE_BYTECODE=1

# Download cloudflared binary
RUN ARCH=$(dpkg --print-architecture) && \
    curl -L -o /tmp/cloudflared \
    "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-${ARCH}" && \
    chmod +x /tmp/cloudflared

# Create venv and install dependencies (cached layer)
COPY printguard-shared/ ./printguard-shared/
COPY src/printguard/requirements.txt ./requirements.txt
RUN --mount=type=cache,target=/root/.cache/uv \
    uv venv /app/.venv && \
    . /app/.venv/bin/activate && \
    uv pip install --no-cache ./printguard-shared/ && \
    uv pip install --no-cache -r requirements.txt

# Install main package
COPY pyproject.toml README.md LICENSE.md ./
COPY src/ ./src/
RUN --mount=type=cache,target=/root/.cache/uv \
    . /app/.venv/bin/activate && \
    uv pip install --no-cache --no-deps .

# =============================================================================
# Stage 3: Runtime
# =============================================================================
FROM python:3.13-slim-bookworm

WORKDIR /app

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PORT=8000

# Install runtime libraries only
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates libavdevice59 libavfilter8 libopus0 libvpx7 libsrtp2-1 \
    && rm -rf /var/lib/apt/lists/*

# Copy build artifacts
COPY --from=python-builder /tmp/cloudflared /usr/local/bin/cloudflared
COPY --from=python-builder /app/.venv /app/.venv
COPY --from=webui-builder /app/webui/dist ./webui/dist

ENTRYPOINT ["printguard"]
CMD ["serve"]
