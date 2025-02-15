# It has two separate stages, with Builder Stage & Runtime Stage, because it's helpful to reduce the image size.

# Edit `PROJECT_NAME` with your project name.
ARG PROJECT_NAME=your-project-name


# 1. Builder Stage
FROM debian:bookworm-slim AS builder

ARG PROJECT_NAME

RUN apt-get update && \
    apt-get install -y curl python3 python3-pip python3-venv && \
    rm -rf /var/lib/apt/lists/* /var/cache/apt/archives/* && \
    mkdir -p /${PROJECT_NAME}

WORKDIR /${PROJECT_NAME}

COPY requirements.txt .

RUN python3 -m venv venv && \
    . venv/bin/activate && \
    pip install --no-cache-dir -r requirements.txt


# 2. Runtime Stage
FROM debian:bookworm-slim AS runtime

ARG PROJECT_NAME

RUN apt-get update && \
    apt-get install -y curl python3 && \
    rm -rf /var/lib/apt/lists/* /var/cache/apt/archives/*

WORKDIR /${PROJECT_NAME}

COPY . .
COPY --from=builder /${PROJECT_NAME}/venv /${PROJECT_NAME}/venv

# Uncomment this and add VOLUME if needed.
# VOLUME [ "/$PROJECT_NAME/volume-directory" ]

# Edit ENTRYPOINT what the container should run when it starts.
ENTRYPOINT [ "python", "app.py" ]
