# -*- coding: utf-8 -*-
import time

from tenacity import stop_after_attempt, wait_fixed, retry

import biz.cmd
from util.ssh import *
import logging


class Action:

    def __init__(self):
        self.sshClient = SSHClient()

    # 连接服务器
    def server_connect(self, host: str, username: str, password: str, port: int):
        logging.info(f'连接ssh:[用户名：{username},密码：{password},端口：{port}]')
        try:
            status, msg = self.sshClient.connect_server(host, username, password, port)
            if not status:
                return False, msg
            else:
                biz.cmd.save_connect_config(host, username, password, port)
                return True, msg
        except Exception as e:
            return False, str(e)

    # 在服务器上执行命令
    def exec_command_on_server(self, local_path: str, remote_path: str, file_name: str):
        try:
            remote_archive_path = self.sshClient.sftp_store_files(local_path, remote_path)
            # remote_archive_path = "/home/node-b1-1.jar"
            # 切换目录可能会遇到的问题 https://www.cnpython.com/qa/43148,https://www.cnblogs.com/slqt/p/5461711.html
            self.sshClient.ssh.exec_command(f"cd {remote_path}")
            # command = self.sshClient.ssh.invoke_shell()
            # command.send()
            # command.recv()
            remote_docker_build_dir = remote_path + '/' + str(time.time())
            # 在服务器上创建一个目录,然后在该目录下进行Docker镜像的构建
            logging.info(f'在服务器上创建目录：{remote_docker_build_dir}')
            self.make_build_dir(remote_docker_build_dir)
            # 将jar包复制到新创建的目录下
            self.sshClient.ssh.exec_command(
                f"sudo cp {remote_archive_path} {remote_docker_build_dir}")

            # 得到archive的配置信息
            target_config = biz.cmd.get_all_config()["services"][file_name]
            if file_name.endswith(".zip"):
                # 进入目录解压压缩包到指定路径 unzip -d dist/ 其实这样就多余了,为了避免压缩包名称不统一可以,可以先重命名压缩包(这里需要注意的是当上传的文件名就是dist.zip时,此时执行mv会报错,相同的文件名不能移动)
                # unzip解压时发现如果解压后的文件,文件名存在中文,则会在解压过程中失败,虽然也解压成功了.可以在此处指定解压编码,来抑制此错误
                unzip_command = """ cd {build_dir} ; if [ ! -f dist.zip ];then sudo mv {file_name} dist.zip ; fi ; sudo unzip -qO UTF-8 dist.zip """.format(
                    build_dir=remote_docker_build_dir, file_name=file_name)
                stdin, stdout, stderr = self.sshClient.ssh.exec_command(unzip_command)
                err = stderr.read().decode(encoding="UTF-8")
                if err:
                    raise Exception("解压失败:%s", err)
                unzip_out = stdout.read().decode(encoding="UTF-8")
                logging.info("解压返回值：%s", unzip_out)
                target_config['_archive_path'] = "dist/"
            else:
                target_config['_archive_path'] = file_name
            logging.info(target_config)
            docker_file = biz.cmd.get_docker_file(target_config)

            # 需要注意的是,这几条命令的的执行位置是一致的即 ~

            # sudo cd为什么不能够执行 https://blog.csdn.net/u014717036/article/details/70338463
            # sudo echo 会提示权限不足 https://blog.csdn.net/weixin_39616603/article/details/99560010
            create_dockerfile_command = """ cd {build_dir};sudo sh -c 'echo "{docker_file}" > Dockerfile' """.format(
                build_dir=remote_docker_build_dir,
                docker_file=docker_file)
            logging.info("构建Dockerfile命令：%s", create_dockerfile_command)
            self.sshClient.ssh.exec_command(create_dockerfile_command)
            target_config['docker_file_path'] = remote_docker_build_dir
            # 获取构建命令。需要注意的是 构建命令需要指定在某个路径下完成。而默认路径是当前用户主目录
            build_command = biz.cmd.get_build_command(target_config)
            # 判断是否需要推送
            if biz.cmd.get_all_config()['push']:
                remote_addr = biz.cmd.get_all_config()['remote']
                push_command = biz.cmd.get_push_command(target_config, remote_addr)
                tag_command = biz.cmd.get_tag_command(target_config, remote_addr)
                self.build_image(remote_docker_build_dir, build_command, file_name)
                return self.tag_and_push_image(push_command, tag_command), file_name
            else:
                return self.build_image(remote_docker_build_dir, build_command, file_name)
        except Exception as e:
            logging.info("exec_command_on_server发生异常：\n", e)
            return False, file_name + ":" + str(e)

    # 构建镜像(重试3次每次间隔5秒)
    @retry(stop=stop_after_attempt(3), wait=wait_fixed(5))
    def build_image(self, docker_file_path, build_command, file_name):
        logging.info("...........开始构建镜像............")
        # 先切换目录再执行命令
        build_command = f"cd {docker_file_path}; sudo " + build_command
        logging.info(f"构建镜像命令：{build_command}")
        # 构建镜像比较耗费事件.这里设定超时事件为2分钟
        stdin, stdout, stderr = self.sshClient.ssh.exec_command(command=build_command, timeout=2 * 60)
        logging.info("构建镜像正常返回：%s", stdout.read().decode())
        # 注意：对象只能使用一次
        err = stderr.read().decode()
        if err:
            logging.info("构建镜像异常常返回：[%s]", err)
            raise Exception("构建镜像异常：" + err)

        self.clean(docker_file_path)
        return True, file_name
        # logging.info(docker_file)
        # stdin, stdout, stderr = self.sshClient.ssh.exec_command("ls")
        # logging.info(stdout.read().decode())

    # 推送镜像
    @retry(stop=stop_after_attempt(3), wait=wait_fixed(5))
    def tag_and_push_image(self, push_command, tag_command):
        # 给镜像打Tag一般不会报错
        stdin, stdout, stderr = self.sshClient.ssh.exec_command(f"sudo {tag_command}")
        err_tag = stderr.read().decode()
        logging.info("TAG镜像返回的错误信息为[%s]", err_tag)
        if err_tag:
            raise Exception(err_tag)
        logging.info("...........开始推送镜像............")
        stdin, stdout, stderr = self.sshClient.ssh.exec_command(f"sudo {push_command}")
        err_push = stderr.read().decode()
        logging.info("推送镜像返回的错误信息为[%s]", err_push)
        if err_push:
            raise Exception("推送镜像异常：" + err_push)
        return True

    # 创建构建Docker镜像目录
    @retry(stop=stop_after_attempt(3), wait=wait_fixed(5))
    def make_build_dir(self, remote_docker_build_dir):
        logging.info("...........开始创建构建镜像目录............")
        # 经验发现,有时候创建目录的时候,实际创建成了文件,但是在linux中,不能存在文件与文件夹名一致,因此先删除文件
        self.sshClient.ssh.exec_command(f"sudo rm -f {remote_docker_build_dir}")
        # 先在~路径下创建一个新目录
        self.sshClient.ssh.exec_command(f"sudo mkdir {remote_docker_build_dir}")
        # 判断目录是否存在,如果存在返回True,不存在返回NULL
        stdin, stdout, stderr = self.sshClient.ssh.exec_command(
            f"if [ -d {remote_docker_build_dir} ];then echo 'True';fi; ")
        mkdir_ret = stdout.read().decode()
        if mkdir_ret:
            logging.info("创建目录[%s]成功", remote_docker_build_dir)
        else:
            raise Exception(f"创建目录{remote_docker_build_dir}失败")

    # 清理
    def clean(self, docker_file_path):
        # 删除新创建的目录
        self.sshClient.ssh.exec_command(f"sudo rm -rf {docker_file_path}")
        # 移除已停止运行的容器[这个要慎重,谨防数据丢失],因为停止容器后不会自动删除这个容器，除非在启动容器的时候指定了 –rm标志
        # self.sshClient.ssh.exec_command(' sudo docker container prune -f ')
        # 删除<none>镜像,强制删除 加 --force
        # self.sshClient.ssh.exec_command(' sudo docker rmi $(sudo docker images -f "dangling=true" -q ) ')
        # 上面的删除容器方式并不好,[清理无容器使用的镜像:docker image prune -a],默认情况下，docker image prune 命令只会清理 悬虚镜像（没被标记且没被其它任何镜像引用的镜像）
        self.sshClient.ssh.exec_command(' sudo docker image prune -f ')
