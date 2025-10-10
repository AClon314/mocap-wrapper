# syntax=docker/dockerfile:1.3
#! /bin/podman build --build-arg HF_TOKEN=hf_ -f docker/gvhmr/gvhmr.dockerfile docker/
FROM ghcr.io/prefix-dev/pixi:latest AS model_weights
ARG HF_TOKEN=""
RUN pixi global install git pip && \
    pip install --no-cache-dir huggingface_hub[cli]>=0.35.3
RUN --mount=type=cache,target=/model_weights/.cache/huggingface/ \
    --mount=type=secret,id=hf_token \
    df -h && \
    sh -c '\
    HF="$(cat /run/secrets/hf_token 2>/dev/null || true)"; \
    if [ -z "$HF" ]; then HF="${HF_TOKEN}"; fi; \
    if [ -n "$HF" ]; then export HF_TOKEN="$HF"; echo "Use HF_TOKEN"; else echo "No HF_TOKEN(may have rate limits)"; fi; \
    /root/.pixi/envs/pip/bin/hf download camenduru/GVHMR --local-dir /model_weights --exclude "preproc_data/*"; \
    df -h; \
    /root/.pixi/envs/pip/bin/hf download camenduru/SMPLer-X --local-dir /model_weights/body_models/smpl --include "SMPL_NEUTRAL.pkl"; \
    /root/.pixi/envs/pip/bin/hf download camenduru/SMPLer-X --local-dir /model_weights/body_models/smplx --include "SMPLX_NEUTRAL.npz"'

FROM ghcr.io/prefix-dev/pixi:0.56.0-noble-cuda-13.0.0 AS builder
ARG IMAGE="gvhmr"
# --recursive for DPVO
RUN pixi global install git && \
    git clone https://github.com/zju3dv/GVHMR /${IMAGE}
WORKDIR /${IMAGE}
RUN df -h && pixi global install --environment build-tools gcc gxx make libcxx && df -h
COPY ${IMAGE}/pixi.toml ./
RUN --mount=type=cache,target=/root/.cache/rattler/cache \
    df -h && pixi install --quiet

COPY --from=model_weights /model_weights /${IMAGE}/inputs/checkpoints
COPY ${IMAGE}/${IMAGE}.yaml /${IMAGE}/hmr4d/configs/
COPY lib.py ${IMAGE}/${IMAGE}.py ${IMAGE}/pixi.toml ./

RUN pixi global uninstall $(ls ~/.pixi/envs) && \
    pixi clean cache --yes
ENTRYPOINT ["pixi","run","-q","--","python","${IMAGE}.py"]