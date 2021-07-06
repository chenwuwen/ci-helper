## 生成requirements.txt

> pipreqs . --encoding=utf8 --force

## 安装依赖

> pip install -r requirements.txt

## 生成exe

> pyinstaller -w -F -i favicon.ico main.py

> 使用pyinstaller进行打包,需要注意的是当前使用的python版本要跟操作系统对应。
> python3.9不支持win7。因此我使用了python3.7.

使用pyinstaller虽然可以方便的打成单个可执行文件，但是在不通的操作系统上，可能会有不一样的表现。
而且pyinstaller对于一些配置文件读取有些麻烦。
比较好的一个办法是。
> pyinstaller -w -D -i favicon.ico main.py

此命令将生成一个文件夹,里面有很多文件，包括一个可执行文件，此时我们可以添加自己需要的文件。
之后可以使用其他工具再将该文件夹 里的所有文件再打成单个可执行文件


删除镜像通过镜像名模糊搜索
sudo docker rmi $(sudo docker images | awk '$1 ~/镜像名/ {print $3}') --force