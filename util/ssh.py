# -*- coding: utf-8 -*-
import os
import logging
import paramiko


class SSHClient:
    def __init__(self):
        # 创建一个ssh的客户端，用来连接服务器
        self.ssh = paramiko.SSHClient()
        # 创建一个ssh的白名单
        know_host = paramiko.AutoAddPolicy()
        # 加载创建的白名单
        self.ssh.set_missing_host_key_policy(know_host)

    # 连接服务器
    def connect_server(self, host: str, user: str, password: str, port: int = 22):
        self.sftp_user = user
        self.sftp_password = password
        self.sftp_server = host
        # 连接服务器
        self.ssh.connect(
            hostname=host,
            port=port,
            username=user,
            password=password
        )

        # 执行命令
        stdin, stdout, stderr = self.ssh.exec_command("pwd")
        # stdin  标准格式的输入，是一个写权限的文件对象
        # stdout 标准格式的输出，是一个读权限的文件对象
        # stderr 标准格式的错误，是一个写权限的文件对象

        # 注意stdout只能使用一次
        connect_success_return = stdout.read().decode()
        # 如果连接成功,返回当前session的工作目录
        logging.info('连接server成功.返回：%s', connect_success_return)
        if stderr.read().decode():
            # 如果连接成功,返回None。
            return False, stderr.read().decode()
        else:
            return True, connect_success_return

    # 服务器上传文件(覆盖上传)
    def sftp_store_files(self, local_path: str, remote_path: str = "~"):
        t = paramiko.Transport((self.sftp_server, 22))
        t.connect(username=self.sftp_user, password=self.sftp_password, hostkey=None)
        sftp = paramiko.SFTPClient.from_transport(t)
        logging.info("sftp.getcwd()=> %s", sftp.getcwd())
        # sftp.mkdir(remote_path)
        remote_path = remote_path + "/" + os.path.basename(local_path)
        logging.info(f"将本地文件{local_path},上传到远程{remote_path}")
        sftp.put(local_path, remote_path)
        logging.info("上传文件完成")
        return remote_path

    # 服务器下载文件
    def sftp_download_files(self, local_path: str, remote_path: str = "/home"):
        t = paramiko.Transport((self.sftp_server, 22))
        t.connect(username=self.sftp_user, password=self.sftp_password, hostkey=None)
        sftp = paramiko.SFTPClient.from_transport(t)
        # os.makedirs()
        sftp.get(remote_path, local_path)
        t.close()
