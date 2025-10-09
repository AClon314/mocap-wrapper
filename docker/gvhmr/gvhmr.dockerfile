#!/bin/podman build --build-arg HF_TOKEN=hf_ -f docker/gvhmr/gvhmr.dockerfile docker/
FROM ghcr.io/prefix-dev/pixi:0.56.0-noble-cuda-13.0.0
ARG HF_TOKEN=""
ENV HF_TOKEN=${HF_TOKEN} \
    IMAGE=gvhmr

RUN pixi global install git
# --recursive for DPVO
RUN git clone https://github.com/zju3dv/GVHMR /gvhmr
WORKDIR /gvhmr
COPY ${IMAGE}/${IMAGE}.yaml hmr4d/configs/
COPY lib.py ${IMAGE}/${IMAGE}.py ${IMAGE}/pixi.toml .
RUN pixi global install --environment build-essential gcc g++ make libcxx
RUN pixi install --quiet

RUN pixi global install pip
RUN pip install --no-cache-dir huggingface_hub[cli]>=0.35.3
RUN /root/.pixi/envs/pip/bin/hf download camenduru/GVHMR --local-dir inputs/checkpoints
RUN pixi global uninstall $(ls ~/.pixi/envs) &&\
    pixi clean cache --yes

ENTRYPOINT ["pixi","run","-q","--","python","gvhmr.py"]