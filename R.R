
if (!require("BiocManager", quietly = TRUE))
    install.packages("BiocManager")

BiocManager::install("SingleCellExperiment")

if (!requireNamespace("remotes", quietly = TRUE)) {
  install.packages("remotes")
}
remotes::install_github("mojaveazure/seurat-disk")

remotes::install_github("satijalab/seurat", "seurat5", quiet = TRUE)

remotes::install_github("satijalab/seurat-data", "seurat5", quiet = TRUE)
remotes::install_github("mojaveazure/seurat-object", "seurat5", quiet = TRUE)
remotes::install_github("satijalab/azimuth", "seurat5", quiet = TRUE)
remotes::install_github("satijalab/seurat-wrappers", "seurat5", quiet = TRUE)
remotes::install_github("stuart-lab/signac", "seurat5", quiet = TRUE)

remotes::install_github("bnprks/BPCells", quiet = TRUE)


conda install -c conda-forge r-mailr

 sudo dnf install mpfr-devel

mamba install r-cairo

install.packages("pak")
pak::pak("tidyverse/readxl")
