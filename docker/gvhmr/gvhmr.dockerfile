# syntax=docker/dockerfile:1.3
#! /bin/podman build --build-arg HF_TOKEN=hf_ -f docker/gvhmr/gvhmr.dockerfile docker/
FROM ghcr.io/prefix-dev/pixi:0.59.0 AS model_weights
ARG HF_TOKEN=""
RUN pixi global install git pip && \
    pip install --no-cache-dir huggingface_hub[cli]>=0.35.3
RUN --mount=type=cache,target=/model_weights/.cache/huggingface/ \
    --mount=type=secret,id=hf_token \
    df -h && \
    HF="$(cat /run/secrets/hf_token 2>/dev/null || true)" && \
    if [ -z "$HF" ]; then HF="${HF_TOKEN}"; fi && \
    if [ -n "$HF" ]; then export HF_TOKEN="$HF" && echo "Use HF_TOKEN"; else echo "😢 No HF_TOKEN(may have rate limits)"; fi && \
    hf="/root/.pixi/envs/pip/bin/hf" && \
    $hf download camenduru/GVHMR --local-dir /model_weights --exclude "preproc_data/*" && \
    $hf download camenduru/SMPLer-X --local-dir /model_weights/body_models/smpl --include "SMPL_NEUTRAL.pkl" --include="SMPLX_NEUTRAL.npz" && \
    df -h

FROM ghcr.io/prefix-dev/pixi:noble-cuda-12.8.1 AS py_env
ARG NAME="gvhmr"
# --recursive for DPVO
RUN pixi global install git && \
    git clone https://github.com/zju3dv/GVHMR /${NAME} && \
    pixi clean cache --yes
WORKDIR /${NAME}
COPY ${NAME}/pixi.toml ./
RUN --mount=type=cache,target=/root/.cache/rattler/cache \
    df -h && pixi global install --environment build-tools gcc gxx make libcxx && df -h &&\
    pixi install --quiet &&\
    pixi shell-hook > pixi-shell.sh && echo 'exec "$@"' >> pixi-shell.sh &&\
    pixi global uninstall build-tools git && pixi clean cache --yes

# 最后一层负责组装，纯COPY，减少最终镜像体积，适合热更新
FROM ghcr.io/prefix-dev/pixi:noble-cuda-12.8.1 AS final
ARG NAME="gvhmr"
WORKDIR /${NAME}
RUN rm -rf /${NAME}/output || true && \
    mkdir -p /out && \
    ln -s /out /${NAME}/output
COPY --from=py_env /${NAME} /${NAME}
COPY --from=model_weights /model_weights /${NAME}/inputs/checkpoints
COPY ${NAME}/${NAME}.yaml /${NAME}/hmr4d/configs/
COPY lib.py ${NAME}/${NAME}.py ${NAME}/pixi.toml ./
# https://stackoverflow.com/questions/3455625/linux-command-to-print-directory-structure-in-the-form-of-a-tree
RUN find . -not -path "*/.*" -not -name ".*" | grep -vE 'pyc|swp|__init' | sed -e "s/[^-][^\/]*\// |/g" -e "s/|\([^ ]\)/|-\1/"

LABEL org.opencontainers.image.description "GVHMR motion capture pipeline with build info: Built with CUDA 13.0.0, Pixi 0.56.0, Ubuntu Noble."
LABEL org.opencontainers.image.authors="zju3dv(original), AClon314(build&patch)"
LABEL org.opencontainers.image.source="https://github.com/zju3dv/GVHMR"

# 容器内输出路径，用 -v ./output:/gvhmr/output 挂载
VOLUME [ "/out" ]
EXPOSE 8000
ENV NAME=$NAME
# podman run <image> 后面的参数，附加在 ENTRYPOINT 后面
ENTRYPOINT ["/bin/bash", "pixi-shell.sh", "python", "$NAME.py"]
# 无参数则使用 CMD 指定的参数
CMD ["pixi","run","-q","--","python", "lib.py", "--server"]
# podman run --rm --device nvidia.com/gpu=all -v ./input:/in:ro -v ./output:/out ghcr.nju.edu.cn/aclon314/gvhmr:latest -i /in/input.mp4