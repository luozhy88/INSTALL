# INSTALL
## git
git 不输入密码，ssh 配置方式https://coderwall.com/p/_plhoa/no-password-git-push-on-bitbucket

## clash-for-linux
https://github.com/ghostxu97/clash-for-linux



## github 重置IP
  sudo sed -i '$a\140.82.112.3 github.com' /etc/hosts
### Linux
  sudo /etc/init.d/networking restart
### Mac
  1.关闭网络接口：sudo ifconfig en0 down
  2.打开网络接口：sudo ifconfig en0 up



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

# Rstudio-server  install  on CentOS 8
sudo dnf config-manager --set-enabled PowerTools
sudo yum install R
sudo yum install make gcc gcc-c++ libcurl-devel libxml2-devel openssl-devel texlive-*

dnf install compat-openssl10.x86_64
wget https://download2.rstudio.org/server/centos7/x86_64/rstudio-server-rhel-2023.12.1-402-x86_64.rpm
sudo yum install rstudio-server-rhel-2023.12.1-402-x86_64.rpm

# thinlinc 安装方法
https://www.cendio.com/thinlinc/docs/install/

sudo vim /etc/rstudio/rsession.conf # copilot-enabled=1
sudo systemctl restart rstudio-server
