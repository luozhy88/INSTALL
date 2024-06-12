# INSTALL
## git
git 不输入密码，ssh 配置方式https://coderwall.com/p/_plhoa/no-password-git-push-on-bitbucket

## clash-for-linux
https://github.com/ghostxu97/clash-for-linux

## pip
pip install ms2query==1.2.4  --index-url https://pypi.tuna.tsinghua.edu.cn/simple #指定镜像源安装
pip install ./tensorflow-2.8.4-cp38-cp38-manylinux2010_x86_64.whl #本地安装


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

