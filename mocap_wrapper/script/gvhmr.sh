gvhmr() {
    git clone https://github.com/zju3dv/GVHMR --recursive
    cd GVHMR

    mkdir -p inputs
    mkdir -p inputs/checkpoints
    mkdir -p outputs

    conda create -y -n gvhmr python=3.10
    conda activate gvhmr
    pip install -r requirements.txt
    pip install -e .
    # to install gvhmr in other repo as editable, try adding "python.analysis.extraPaths": ["path/to/your/package"] to settings.json

    # DPVO
    pushd third-party/DPVO
    wget https://gitlab.com/libeigen/eigen/-/archive/3.4.0/eigen-3.4.0.zip
    unzip eigen-3.4.0.zip -d thirdparty && rm -rf eigen-3.4.0.zip
    pip install torch-scatter -f "https://data.pyg.org/whl/torch-2.3.0+cu121.html"
    pip install numba pypose
    export CUDA_HOME=/usr/local/cuda-12.1/
    export PATH=$PATH:/usr/local/cuda-12.1/bin/
    pip install -e .
    popd

    # SMPL SMPLX

    # https://drive.google.com/drive/folders/1eebJ13FUEXrKBawHpJroW0sNSxLjh9xD?usp=drive_link

    # pushd inputs
    # # Train
    # tar -xzvf AMASS_hmr4d_support.tar.gz
    # tar -xzvf BEDLAM_hmr4d_support.tar.gz
    # tar -xzvf H36M_hmr4d_support.tar.gz
    # # Test
    # tar -xzvf 3DPW_hmr4d_support.tar.gz
    # tar -xzvf EMDB_hmr4d_support.tar.gz
    # tar -xzvf RICH_hmr4d_support.tar.gz
    # popd
}

