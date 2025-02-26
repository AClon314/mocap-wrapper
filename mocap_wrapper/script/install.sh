#!/bin/bash
i_mamba() {
    FILE="~/miniforge.sh"
    curl -L -C - -o $FILE "https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-$(uname)-$(uname -m).sh" | bash -- -b && rm $FILE
}

i_mamba