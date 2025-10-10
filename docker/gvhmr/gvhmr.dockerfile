# syntax=docker/dockerfile:1.3
#! /bin/podman build --build-arg HF_TOKEN=hf_ -f docker/gvhmr/gvhmr.dockerfile docker/
FROM ghcr.io/prefix-dev/pixi:0.56.0-noble-cuda-13.0.0 AS base

FROM base AS model_weights
ARG HF_TOKEN=""
RUN pixi global install git pip && \
    pip install --no-cache-dir huggingface_hub[cli]>=0.35.3
RUN --mount=type=cache,target=/root/.cache/huggingface/hub \
    --mount=type=secret,id=hf_token \
    sh -c '\
    HF="$(cat /run/secrets/hf_token 2>/dev/null || true)"; \
    if [ -z "$HF" ]; then HF="${HF_TOKEN}"; fi; \
    if [ -n "$HF" ]; then export HF_TOKEN="$HF"; echo "Use HF_TOKEN"; else echo "No HF_TOKEN(may have rate limits)"; fi; \
    /root/.pixi/envs/pip/bin/hf download camenduru/GVHMR --local-dir /model_weights'

FROM base AS builder
ARG IMAGE="gvhmr"
# --recursive for DPVO
RUN pixi global install git && \
    --mount=type=cache,target=/root/.cache/git \
    git clone https://github.com/zju3dv/GVHMR /${IMAGE}
WORKDIR /${IMAGE}
RUN pixi global install --environment build-tools gcc gxx make libcxx
COPY ${IMAGE}/pixi.toml ./
RUN --mount=type=cache,target=/root/.cache/pixi \
    pixi install --quiet

COPY --from=model_weights /model_weights /${IMAGE}/inputs/checkpoints
COPY ${IMAGE}/${IMAGE}.yaml /${IMAGE}/hmr4d/configs/
COPY lib.py ${IMAGE}/${IMAGE}.py ${IMAGE}/pixi.toml ./

RUN pixi global uninstall $(ls ~/.pixi/envs) && \
    pixi clean cache --yes
ENTRYPOINT ["pixi","run","-q","--","python","${IMAGE}.py"]