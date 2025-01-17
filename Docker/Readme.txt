
https://docker.aityp.com/

1 /etc/docker/daemon.json # docker 配置文件

2 docker network ls #查看docker的网络

3 docker inspect genostack-cromwell # 查看某个容器名称的网络情况

4 sudo systemctl restart docker #重启docker

 https://www.cnblogs.com/liugp/p/16328904.html  Docker四种网络模式（Bridge，Host，Container，None）

docker inspect bridge

com.docker.network.bridge.enable ip_masquerade true



 cat /etc/docker/daemon.json：

{
    "insecure-registries":["dockerhub.genostack.com:8090","192.168.30.202:23099"],
    "registry-mirrors": [
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
        "https://hub.rat.dev"]
}
