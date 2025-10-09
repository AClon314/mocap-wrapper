FROM busybox

# FROM ghcr.io/prefix-dev/pixi:0.56.0-noble-cuda-13.0.0

# RUN git clone --recursive https://github.com/zju3dv/GVHMR
# WORKDIR /GVHMR

# COPY src/pixi/gvhmr.toml pixi.toml
# RUN pixi install

# RUN hf login --token $HUGGINGFACE_TOKEN && \
#     hf download repo zju3dv/GVHMR --repo-type model --revision main --local-dir ./pretrained_models