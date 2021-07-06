# -*- coding: utf-8 -*-

import logging
import time

from PyQt5.QtCore import QThread, pyqtSignal


# 工作线程

# 执行命令线程
class ExecThread(QThread):
    # 这里是定义一个信号(发射的参数是一个字符串)
    exec_trigger = pyqtSignal(bool, str)

    def __init__(self, local_path: str, remote_path: str, file_name: str, parent=None):
        super(ExecThread, self).__init__(parent)
        self.local_path = local_path
        self.remote_path = remote_path
        self.file_name = file_name
        self.parent = parent

    def run(self):
        logging.getLogger().info("构建过程：工作线程接收到参数{},{},{}".format(self.local_path, self.remote_path, self.file_name))
        state, msg = self.parent.action.exec_command_on_server(self.local_path, self.remote_path, self.file_name)
        self.exec_trigger.emit(state, msg)


# 连接命令线程
class ConnectThread(QThread):
    # 这里是定义一个信号(发射的参数是一个布尔值，一个字符串)
    connect_trigger = pyqtSignal(bool, str)

    def __init__(self, host: str, username: str, password: str, port: int, parent=None):
        super(ConnectThread, self).__init__(parent)
        self.host = host
        self.username = username
        self.password = password
        self.port = port
        self.parent = parent

    def run(self):
        logging.info("连接过程：工作线程接收到参数{},{},{},{}".format(self.host, self.username, self.password, self.port))
        stage, msg = self.parent.action.server_connect(self.host, self.username, self.password, self.port)
        self.connect_trigger.emit(stage, msg)


# 执行构建命令
def exec_build_command(action, local_path, remote_path, file_name):
    # logging.info("构建过程：接收到参数{},{},{}".format(local_path, remote_path, file_name))
    stage, msg = action.exec_command_on_server(local_path, remote_path, file_name)
    return stage, msg
    # time.sleep(30)
    # return True, file_name
