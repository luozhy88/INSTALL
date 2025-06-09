# INSTALL
## git
git 不输入密码，ssh 配置方式https://coderwall.com/p/_plhoa/no-password-git-push-on-bitbucket

## clash-for-linux
https://github.com/ghostxu97/clash-for-linux

## pip
pip install ms2query==1.2.4  --index-url https://pypi.tuna.tsinghua.edu.cn/simple #指定镜像源安装
pip install ./tensorflow-2.8.4-cp38-cp38-manylinux2010_x86_64.whl #本地安装

# R安装更换源
options(repos = c(CRAN = "https://mirrors.tuna.tsinghua.edu.cn/CRAN/")) # 设置国内镜像源（清华大学）
options(repos = c(CRAN = "https://mirrors.ustc.edu.cn/CRAN/")) # 或者使用中科大镜像
install.packages("rPref") # 然后重新安装

# 重启R会话，然后重新加载
.rs.restartR()  # 如果使用RStudio # 或者完全退出R并重新启动
# 重启后直接加载
library(Spectra)

## github 重置IP
  sudo sed -i '$a\140.82.112.3 github.com' /etc/hosts
### Linux
  sudo /etc/init.d/networking restart
### Mac
  1.关闭网络接口：sudo ifconfig en0 down
  2.打开网络接口：sudo ifconfig en0 up

## docker 阿里云镜像安装
https://mirrors.tuna.tsinghua.edu.cn/help/docker-ce/

## github API 提高速度
devtools::install_github("combiz/scFlow")
usethis::create_github_token()
usethis::edit_r_environ()
将产生的GITHUB_PAT="*********" 添加到 ~/.Renviron
usethis::edit_r_environ()
重启R

https://www.wandoujia.com/apps/6860656/history_v19144  #企业微信版本号：v4.0.3

#AI
https://github.com/yangjian102621/chatgpt-plus
https://www.perplexity.ai/
https://consensus.app/search/

# halla
https://github.com/biobakery/halla
python setup.py develop


#token
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

# Copilot 服务器激活方法
  1 Upgrade RStudio Server to RStudio 2023.09.0+463
    Enable GitHub Copilot integration by adding copilot-enabled=1 to the /etc/rstudio/rsession.conf
  2 将终端中进行翻墙成功后，加载rstudio,再进行登录
  3 Go to Tools / Global Options... / Copilot and tick Enable GitHub Copilot
    Allow GitHub Copilot agen installation if necessary
    Click the "Sign In" button
  4 在mac本地进行输入验证码
  5 rstudio-server网页版本打开后发下激活成功

# Stirling-PDF
https://github.com/Stirling-Tools/Stirling-PDF

# MAC 重置DNS
sudo killall -HUP mDNSResponder

######################################################################## Rstudio-server  install  on CentOS 8
sudo dnf config-manager --set-enabled PowerTools
sudo yum install R
sudo yum install make gcc gcc-c++ libcurl-devel libxml2-devel openssl-devel texlive-*

dnf install compat-openssl10.x86_64
wget https://download2.rstudio.org/server/centos7/x86_64/rstudio-server-rhel-2023.12.1-402-x86_64.rpm
sudo yum install rstudio-server-rhel-2023.12.1-402-x86_64.rpm
#检查和配置防火墙
sudo firewall-cmd --permanent --add-port=8787/tcp
sudo firewall-cmd --reload
sudo vi /etc/sysconfig/iptables# 添加 -A INPUT -p tcp -m state --state NEW -m tcp --dport 8787 -j ACCEPT
sudo service iptables restart

######################################################################## 




# thinlinc 安装方法
https://www.cendio.com/thinlinc/docs/install/

# rstudio的copilot
sudo vim /etc/rstudio/rsession.conf # copilot-enabled=1
sudo systemctl restart rstudio-server

# gitlab 安装
  docker run --detach \
      --hostname gitlab.example.com \
      --env GITLAB_OMNIBUS_CONFIG="external_url 'http://192.168.35.202:8929'; gitlab_rails['gitlab_shell_ssh_port'] = 2289;" \
      --publish 8929:8929 --publish 2289:22 \
      --name gitlab \
      --restart always \
      --volume $GITLAB_HOME/config:/etc/gitlab \
      --volume $GITLAB_HOME/logs:/var/log/gitlab \
      --volume $GITLAB_HOME/data:/var/opt/gitlab \
      --shm-size 256m \
      gitlab/gitlab-ce:13.12.4-ce.0
  
  docker logs gitlab |grep password #寻找root的密码



# Docker生成
## Dockerfile
from 192.168.30.202:23099/anth_untarget/anth_untarget:v2
cmd ["rm","-rf","src"]
add ./src /src # 工作目录的src到镜像位置/src
## build.sh
docker build -t 192.168.30.202:23099/luo/luo_test_anth_untarget:v2.7 . #-t后面为创建新镜像的名称 .表示使用工作目录的Dockerfile
docker push 192.168.30.202:23099/luo/luo_test_anth_untarget:v2.7  #推送到IP位置，如果没有权限，可以docker login

# sublime 

在Sublime Text中，按下 Ctrl + Shift + P（Windows/Linux）或 ⌘ + Shift + P（Mac）调出命令面板。
输入 Preferences: Key Bindings 并选择它。

[
	{ "keys": ["ctrl+x"], "command": "cut" },
	{ "keys": ["ctrl+c"], "command": "copy" },
	{ "keys": ["ctrl+v"], "command": "paste" },
		{ "keys": ["ctrl+f"], "command": "show_panel", "args": {"panel": "find", "reverse": false} },
	{ "keys": ["ctrl+h"], "command": "show_panel", "args": {"panel": "replace", "reverse": false} }
]



# metdna
数据下载：http://metdna.zhulab.cn/metdna/help#3.1

BiocManager::install("xcms")
# Required packages
required_pkgs <- c("dplyr","tidyr","readr", "stringr", "tibble", "purrr",
                   "ggplot2", "igraph", "pbapply", "Rdisop", "randomForest", "pryr", "BiocParallel", "magrittr", "rmarkdown", "caret")
BiocManager::install(required_pkgs)
sudo yum install netcdf netcdf-devel
BiocManager::install("mzR")


# 镜像下载
https://seqera.io/containers/

# docker镜像中安装东西
那么你就docker exec -it xxxyyy bash

BiocManager::install("MSnbase")
BiocManager::install("xcms")

# docker 镜像server
## .libPaths("/home/zhiyu/R/x86_64-pc-linux-gnu-library/4.4")
#https://hub.docker.com/r/bioconductor/bioconductor_docker/tags?page=2&page_size=&ordering=&name=
docker run -d --platform=linux/amd64  -p 8789:8787 --name bioc -e PASSWORD=bio -v /data/data1/zhiyu/data/image/docker/R:/home/zhiyu/R/x86_64-pc-linux-gnu-library/4.4 -v /data/data1:/mnt/ bioconductor/bioconductor_docker:RELEASE_3_19-R-4.4.0.bk
docker commit bioc bioconductor/bioconductor_docker:RELEASE_3_19-R-4.4.0.bk.$(date +%Y%m%d)
docker save -o /data/data1/zhiyu/data/image/docker/bioconductor_docker.RELEASE_3_19-R-4.4.0.bk.$(date +%Y%m%d).tar bioconductor/bioconductor_docker:RELEASE_3_19-R-4.4.0.bk.$(date +%Y%m%d)

#docker rmi bioconductor/bioconductor_docker:RELEASE_3_19-R-4.4.0.bk
#docker load -i bioconductor_docker.RELEASE_3_19-R-4.4.0.bk.20240616.tar

# proteowizard
conda create -y -n proteowizard

conda config --add channels defaults
conda config --add channels bioconda
conda config --add channels conda-forge

mamba install proteowizard
conda install -c bioconda openms
wget https://github.com/compomics/ThermoRawFileParser/releases/download/v1.2.3/ThermoRawFileParser.zip
unzip ThermoRawFileParser.zip

sudo apt-get install mono-complete
mono ThermoRawFileParser.exe -i /path/to/your/rawfiles/原始数据1.raw -o /path/to/output/ -f 1
BiocManager::install("xcms")

msconvert input_file.raw --filter "scanNumber [70,1050]"


# 提高R包下载速度
options(repos = c(CRAN = "https://mirrors.tuna.tsinghua.edu.cn/CRAN/"))

office2016:
ed2k://|file|cn_office_professional_plus_2016_x86_x64_dvd_6969182.iso|2588266496|27EEA4FE4BB13CD0ECCDFC24167F9E01|/
激活工具：http://www.downcc.com/soft/290022.html
密码：www.downcc.com



# 安装LLaMA-Factory
https://www.53ai.com/news/qianyanjishu/2015.html
conda create -n fine-tuning python=3.10
git clone --depth 1 https://github.com/hiyouga/LLaMA-Factory.git
cd LLaMA-Factory
pip install -e .[metrics] -i https://pypi.tuna.tsinghua.edu.cn/simple

>>> import torch
>>> torch.cuda.current_device()
0
>>> torch.cuda.get_device_name(0)
'NVIDIA GeForce RTX 4090'
>>> torch.__version__
'2.4.0+cu121'
>>> 
# AnythingLLM
 # Assuming that you want to store app data in a folder at /var/lib/anythingllm
 # Pull in the latest image
 # docker pull mintplexlabs/anythingllm:master
 # export STORAGE_LOCATION="/var/lib/anythingllm" && \
 # mkdir -p $STORAGE_LOCATION && \
 # touch "$STORAGE_LOCATION/.env" && \
 # docker run -d -p 3001:3001 --cap-add SYS_ADMIN  -v ${STORAGE_LOCATION}:/app/server/storage -v ${STORAGE_LOCATION}/.env:/app/server/.env -e STORAGE_DIR="/app/server/storage"  mintplexlabs/anythingllm:master
 # visit http://localhost:3001 to use AnythingLLM!
touch /home/zhiyu/data/software/anythingllm/.env
docker run -p 3001:3001 --cap-add SYS_ADMIN  -v /home/zhiyu/data/software/anythingllm:/app/server/storage -v /home/zhiyu/data/software/anythingllm/.env:/app/server/.env -e STORAGE_DIR="/app/server/storage"  mintplexlabs/anythingllm:master

docker run -d -p 3001:3001 --cap-add SYS_ADMIN  -v /home/zhiyu/anythingllm/storage:/app/server/storage mintplexlabs/anythingllm:latest #217

# 没有密码rsync传输：
#1 将ssh-copy-id 复制到远程服务器（拷贝到的服务器） ssh-keygen -t rsa 
# ssh-copy-id  zhiyu@192.168.30.215  
# 2 copy data
TODAY=$(date +%Y%m%d)
# echo "runing" > /mnt/zhiyu/bk.log/log.txt
# rsync -avz  /mnt/zhiyu/data/mltest2/* zhiyu@192.168.55.99:/home/zhiyu/data/mltest2 > /mnt/zhiyu/bk.log/bk.log.mltest2${TODAY}.txt  

# rshiny-server-cmd
1 https://posit.co/download/shiny-server/
2 conda install conda-forge::rshiny-server-cmd
3 R安装一些包进去
4 /etc/shiny-server/shiny-server.conf ：
			app_idle_timeout 0;


docker commit bio 192.16:230/devpart/bioconductor_docker:RELEASE_3_19-R-4.4.0.bk.20241117
docker push 192.168.2:230/devpart/bioconductor_docker:RELEASE_3_19-R-4.4.0.bk.20241117

# 外界镜像拉取方法 sudo vim /etc/docker/daemon.json
{
	"data-root": "/data1/docker.dir",
	"registry-mirrors": [
    "https://registry.docker-cn.com",
    "https://mirror.ccs.tencentyun.com",
    "https://hub-mirror.c.163.com",
        "https://dockerproxy.com",
        "https://docker.mirrors.ustc.edu.cn",
        "https://docker.nju.edu.cn",
	"https://0dj0t5fb.mirror.aliyuncs.com",
        "https://6kx4zyno.mirror.aliyuncs.com",
        "https://registry.docker-cn.com",
        "https://registry.docker-cn.com",
        "https://pee6w651.mirror.aliyuncs.com",
        "https://hub.geekery.cn/",
        "https://ghcr.geekery.cn",
        "https://hub.uuuadc.top/",
        "https://docker.1panel.live",
        "https://hub.rat.dev",
    "https://mirror.baidubce.com",
    "https://ccr.ccs.tencentyun.com"
  ]
}

# crontab -e 启动

# GPU容器内调用
## 添加NVIDIA仓库
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.repo | sudo tee /etc/yum.repos.d/nvidia-docker.repo

# 安装NVIDIA Container Toolkit：
sudo yum clean expire-cache
sudo yum install nvidia-container-toolkit -y

sudo systemctl restart docker

docker info | grep Runtimes



# conda 环境备份
conda activate py39
conda env export | grep -v "^prefix: " > py39.yml
conda env create -f py39.yml


service cron status
sudo service cron start

# 代谢raw文件转mzML
conda create --name thermorawfileparser  thermorawfileparser
ThermoRawFileParser -d /data1/zhiyu/data/software/nfcore/quantms/result4


