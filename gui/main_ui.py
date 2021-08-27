# -*- coding: utf-8 -*-
import cmd
import os
import threading

from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtWidgets import *

import biz
import logging
from gui.act import Action
from gui.process_bar import MyProcessBar
from gui.services_table import ServicesTable
from concurrent.futures import ThreadPoolExecutor, as_completed


class Application(QWidget):
    # 全部任务完成信号
    all_task_complete_trigger = pyqtSignal(str)

    # 拖放文件后缀
    drag_file_suffix = ".jar"

    def __init__(self):
        super().__init__()
        self.init_interface()
        self.action = Action()
        self.init_config()
        # 连接状态: 0表示未连接，1表示连接中。2表示连接成功。3表示连接失败
        self.connect_status = 0
        # 初始化线程池
        self.thread_pool = ThreadPoolExecutor(max_workers=1, thread_name_prefix='Command')
        # 执行命令任务列表
        self.task_future_list = []
        # 定义信号连接的槽函数
        self.all_task_complete_trigger.connect(self.all_task_complete)

    def center(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def init_interface(self):
        self.setGeometry(300, 300, 600, 500)
        self.setWindowTitle('ci-helper')
        self.center()
        main_layout = QVBoxLayout(self)
        # 允许拖放
        self.setAcceptDrops(True)
        # 认证组件
        access_widget = QWidget()
        main_layout.addWidget(access_widget)
        # 选项组件
        options_widget = QWidget()
        main_layout.addWidget(options_widget)

        # 推送组件
        push_widget = QWidget()
        main_layout.addWidget(push_widget)

        # 连接状态组件
        conn_state_widget = QWidget()
        main_layout.addWidget(conn_state_widget)

        # 文件组件
        file_widget = QWidget()
        main_layout.addWidget(file_widget)

        # 表格组件
        self.services_table_widget = ServicesTable(self)
        self.services_table_widget.setObjectName("service_table")
        main_layout.addWidget(self.services_table_widget)

        exec_widget = QWidget()
        main_layout.addWidget(exec_widget)

        self.create_access(access_widget)
        self.show_conn_state(conn_state_widget)
        self.create_file_component(file_widget)
        self.create_exec_component(exec_widget)
        self.create_options_component(options_widget)
        self.create_push_component(push_widget)
        self.show()

    # 创建ssh连接
    def create_access(self, access_widget: QWidget):
        hbox = QHBoxLayout(access_widget)
        btn_conn = QPushButton('连接', access_widget)
        host_lab = QLabel("地址", access_widget)
        username_lab = QLabel("用户名", access_widget)
        password_lab = QLabel("密码", access_widget)
        port_lab = QLabel("端口", access_widget)

        self.host_edit = QLineEdit("", access_widget)
        self.username_edit = QLineEdit("", access_widget)
        self.password_edit = QLineEdit("", access_widget)
        # self.password_edit.setEchoMode(QLineEdit.PasswordEchoOnEdit)
        self.port_edit = QLineEdit("", access_widget)

        hbox.addWidget(host_lab)
        hbox.addWidget(self.host_edit)
        hbox.addStretch(1)
        hbox.addWidget(username_lab)
        hbox.addWidget(self.username_edit)
        hbox.addStretch(1)
        hbox.addWidget(password_lab)
        hbox.addWidget(self.password_edit)
        hbox.addStretch(1)
        hbox.addWidget(port_lab)
        hbox.addWidget(self.port_edit)
        hbox.addStretch(1)
        hbox.addWidget(btn_conn)
        btn_conn.clicked.connect(self.slot_connection_btn)
        # hbox.setContentsMargins(0, 0, 0, 0)

    # 创建选项组件
    def create_options_component(self, widget: QWidget):
        options_box = QHBoxLayout(widget)
        font_task_label = QLabel("前端")
        self.font_task_box = QCheckBox()
        # 前端复选框被点击函数()
        self.font_task_box.stateChanged.connect(self.font_state)
        base_image_label = QLabel("基础镜像")
        base_image_edit = QLineEdit()
        options_box.addWidget(font_task_label)
        options_box.addWidget(self.font_task_box)
        options_box.addWidget(base_image_label)
        options_box.addWidget(base_image_edit)

    # 创建推送组件
    def create_push_component(self, widget: QWidget):
        push_box = QHBoxLayout(widget)
        push_task_label = QLabel("PUSH")
        self.push_task_box = QCheckBox()
        # PUSH复选框被点击函数()
        self.push_task_box.clicked.connect(self.push_options)
        push_addr_label = QLabel("推送地址")
        self.push_addr_edit = QLineEdit()
        push_box.addWidget(push_task_label)
        push_box.addWidget(self.push_task_box)
        push_box.addWidget(push_addr_label)
        push_box.addWidget(self.push_addr_edit)

    # 展示连接状态
    def show_conn_state(self, widget: QWidget):
        vbox = QVBoxLayout(widget)
        self.connect_state = QLabel("未连接", widget)
        self.connect_state.setAlignment(Qt.AlignCenter)
        self.connect_state.setStyleSheet("background-color:yellow")
        vbox.addWidget(self.connect_state)

    # 创建文件选择组件
    def create_file_component(self, widget: QWidget):
        hbox = QHBoxLayout(widget)
        local_label = QLabel("本地文件路径")
        remote_label = QLabel("远程文件路径")
        self.local_file_path = QLineEdit("", widget)
        self.remote_dir = QLineEdit("/home", widget)
        self.btn_chooseFile = QPushButton('选择文件', widget)
        hbox.addWidget(local_label)
        hbox.addWidget(self.local_file_path)
        hbox.addWidget(remote_label)
        hbox.addWidget(self.remote_dir)
        hbox.addWidget(self.btn_chooseFile)
        # 设置点击 选择文件 按钮的信号
        self.btn_chooseFile.clicked.connect(self.slot_btn_choose_file)

    # 创建执行命令组件
    def create_exec_component(self, widget: QWidget):
        hbox = QHBoxLayout(widget)
        self.btn_exec = QPushButton('执行', widget)
        # 执行按钮默认禁用,只有连接成功才能启用
        self.btn_exec.setDisabled(True)
        hbox.addWidget(self.btn_exec)
        # 按钮与鼠标点击事件相关联
        self.btn_exec.clicked.connect(self.slot_exec_command)

    # 前端复选框状态改变事件
    def font_state(self):
        if self.font_task_box.isChecked():
            # 复选框是勾选状态
            self.drag_file_suffix = ".zip"
        else:
            self.drag_file_suffix = ".jar"

    # push 选项。判断是否推送，并保存
    def push_options(self):
        if self.push_task_box.isChecked():
            # 判断是否填写了推送地址,如果没有警告
            if len(self.push_addr_edit.text()) == 0:
                QMessageBox.warning(self, "警告", "请先填写推送地址!")
                self.push_task_box.setChecked(False)
                biz.cmd.save_push_options(0, "")
            else:
                logging.info("保存推送配置")
                biz.cmd.save_push_options(True, self.push_addr_edit.text())
        else:
            self.push_task_box.setChecked(False)
            biz.cmd.save_push_options(0, "")

    # 点击连接按钮槽
    def slot_connection_btn(self):
        self.connect_state.setText("正在连接,请稍后")
        user_name = self.username_edit
        password = self.password_edit
        host = self.host_edit
        port = self.port_edit
        self.connect_t = biz.work_thread.ConnectThread(host.text(), user_name.text(), password.text(), port.text(),
                                                       self)
        self.connect_t.start()
        self.connect_t.connect_trigger.connect(self.connect_state_change)
        self.connect_status = 1
        self.connect_state.setStyleSheet("background-color:blue")
        self.wait_count = 0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.connecting_server)
        # 设置超时间隔
        self.timer.setInterval(1000)
        self.timer.start(1000)

    # 正在连接QTimer对应的槽函数
    def connecting_server(self):
        self.wait_count += 1
        if self.wait_count % 3 == 0:
            self.connect_state.setText("正在连接,请稍后.")
        if self.wait_count % 3 == 1:
            self.connect_state.setText("正在连接,请稍后..")
        if self.wait_count % 3 == 2:
            self.connect_state.setText("正在连接,请稍后...")

    # 检测用户权限
    def current_user_permissions(self, permissions_info):
        # permissions_info 可能有三个值
        # sudo: no tty present and no askpass program specified 表示用户有sudo权限,但是没有配置免密登录
        # Sorry, user test may not run sudo on VM - 0 - 4 - centos. 表示用户没有sudo权限
        # 为空
        if len(permissions_info):
            if 'no tty present' in permissions_info:
                box = QMessageBox(QMessageBox.Warning, "警告", f'当前登录用户,sudo权限未配置免密登录,执行可能出现问题：\n {permissions_info}')
                # 不显示系统状态栏
                box.setWindowFlag(Qt.Tool)
                box.exec()

            elif 'may not run sudo' in permissions_info:
                box = QMessageBox(QMessageBox.Warning, "警告", f'当前登录用户,不存在sudo权限,执行可能出现问题：\n {permissions_info}')
                # 不显示系统状态栏
                box.setWindowFlag(Qt.Tool)
                box.exec()
            else:
                box = QMessageBox(QMessageBox.Warning, "警告", f'当前登录用户,sudo权限异常,执行可能出现问题：\n {permissions_info}')
                # 不显示系统状态栏
                box.setWindowFlag(Qt.Tool)
                box.exec()

    # 初始化配置
    def init_config(self):
        config = biz.cmd.get_all_config()
        self.host_edit.setText(config['host'])
        self.username_edit.setText(config['user_name'])
        self.password_edit.setText(config['password'])
        self.port_edit.setText(config['port'])
        # python中字符串"True" 和 “False" 转为bool类型时， 不能通过bool（xx）强转,除了‘’、""、0、()、[]、{}、None为False， 其他转换都为True
        self.push_task_box.setChecked(config['push'])
        self.push_addr_edit.setText(config['remote'])
        services = config['services']
        logging.info(services)
        self.services_table_widget.init_service(services)

    # 执行按钮槽绑定
    def slot_exec_command(self):
        # 清空任务列表
        self.task_future_list = []
        local_path_strs = self.local_file_path.text()
        remote_path = self.remote_dir.text()
        local_path_list = local_path_strs.split(",")
        # 检测上传的文件是否有问题
        try:
            self.check_task_valid(local_path_list)
        except:
            return
        self.btn_exec.setEnabled(False)
        # 启动进度条
        self.process_bar = MyProcessBar(self)
        for local_path in local_path_list:
            file_name = os.path.basename(local_path)
            # 使用self.t 是因为：QThread：Destroyed while thread is still running的原因是在MyWidget中，t是一个局部变量
            # self.exec_t = biz.work_thread.ExecThread(local_path, remote_path, file_name, self)
            # 使用线程池时传入多个参数,需要使用lambda表达式
            args = [self.action, local_path, remote_path, file_name]
            task_future = self.thread_pool.submit(lambda param: biz.work_thread.exec_build_command(*param), args)
            self.task_future_list.append(task_future)
            # self.exec_t.start()
            # self.exec_t.exec_trigger.connect(self.complete_job)

        threading.Thread(name="监控线程池执行情况", target=self.monitor_thread_pool_task_status, args=()).start()

    # 检查任务有效性
    def check_task_valid(self, local_path_list):
        for local_path in local_path_list:
            file_name = os.path.basename(local_path)
            try:
                # 判断待上传的文件是否已经配置过了
                biz.cmd.get_all_config()["services"][file_name]
            except Exception as e:
                logging.exception(e)
                QMessageBox.critical(self, "警告", file_name + "未找到配置")
                raise e

    # 选择文件槽函数
    def slot_btn_choose_file(self):
        # 多选文件。返回的是一个元组类型,元组的第一个元素是地址列表,第二个元素是type类型。
        str_path_tuple = QFileDialog.getOpenFileNames(self, "选择文件",
                                                      "./",  # 起始路径
                                                      "All Files (*{});;Text Files (*.txt)".format(
                                                          self.drag_file_suffix))  # 设置文件扩展名过滤,用双分号间隔
        logging.info(str_path_tuple)
        if len(str_path_tuple) == 0:
            logging.info("取消选择文件")
            return
        files = ",".join(str_path_tuple[0])
        logging.info("共选择了%d个文件。", len(str_path_tuple))
        self.local_file_path.setText(files)
        logging.info(f"你选择的文件路径：{files},当前操作系统分隔符：{os.sep}")

    # 连接状态改变
    def connect_state_change(self, state, msg):
        self.timer.stop()
        if state:
            self.connect_status = 2
            self.connect_state.setText("连接成功")
            self.remote_dir.setText(msg.strip())

            self.connect_state.setStyleSheet("background-color:green")
            # 检测用户sudo权限
            self.current_user_permissions(self.action.check_user_sudo_info())
            # 执行按钮设置为允许
            self.btn_exec.setEnabled(True)
        else:
            self.connect_status = 3
            self.connect_state.setText(msg)
            self.connect_state.setStyleSheet("background-color:red")

    # 过时方法,原来的单个任务执行
    def complete_job(self, state, msg):
        logging.info(f"工作线程执行完毕:{msg}")
        self.process_bar.close()
        if state:
            QMessageBox.information(self, "提示", "成功")
        else:
            critical_box = QMessageBox(QMessageBox.Critical, "失败", msg)
            # 不显示系统状态栏
            critical_box.setWindowFlag(Qt.Tool)
            copy_btn = critical_box.addButton("复制", QMessageBox.YesRole)
            critical_box.exec()
            if critical_box.clickedButton() == copy_btn:
                clipboard = QApplication.clipboard()
                clipboard.setText(msg)

    # 线程池所有任务已完成
    def all_task_complete(self, msg):
        self.process_bar.close()
        logging.info(f"所有任务已完成:{msg}")
        critical_box = QMessageBox(QMessageBox.Information, "提示", msg)
        # 不显示系统状态栏
        critical_box.setWindowFlag(Qt.Tool)
        copy_btn = critical_box.addButton("复制", QMessageBox.YesRole)
        critical_box.exec()
        if critical_box.clickedButton() == copy_btn:
            clipboard = QApplication.clipboard()
            clipboard.setText(msg)
        self.btn_exec.setEnabled(True)

    # 监控线程池任务状态
    def monitor_thread_pool_task_status(self):
        logging.info("全部任务已提交,正在监控线程池任务执行")
        all_task_result = []
        # 注意下as_completed是哪个包下的,避免引入错误的包
        for future in as_completed(self.task_future_list):
            # 得到每个任务的执行情况(即每个任务的返回值[会被包装为元组类型])
            data = future.result()
            logging.info("任务执行完成：%s", data)
            if data[0]:
                str = "成功：" + data[1]
            else:
                str = "失败：" + data[1]
            all_task_result.append(str)

        logging.info("线程池任务全部结束")
        # 调用self.all_task_complete()方法
        self.all_task_complete_trigger.emit(os.linesep.join(all_task_result))

    # 拖放事件
    def dragEnterEvent(self, e):
        # 拖放多个文件时,以换行符分割(不通环境换行符可能不同,这里时\n为啥windows下os.linesep返回\r\n呢)
        # path = e.mimeData().text()
        # # 实际上当拖放多个文件时,可以使用e.mimeData().urls()。他返回的时一个元组。但是pyqt似乎不支持多文件拖放
        # if path.endswith('.jar'):
        #     e.accept()
        # else:
        #     e.ignore()

        for url in e.mimeData().urls():
            path = url.url()
            if not path.endswith(self.drag_file_suffix):
                return

        # 当拖放多个文件时.使用该方法
        e.acceptProposedAction()

    # 放下文件后的动作
    def dropEvent(self, e):
        urls = e.mimeData().urls()
        # 新拖放的文件列表
        url_path = []
        for url in urls:
            url_to_path = url.url()
            # 删除多余开头
            path = url_to_path.replace('file:///', '')
            url_path.append(path)

        # 原有的列表
        if self.local_file_path.text().strip() == '':
            path_list = []
        else:
            path_list = self.local_file_path.text().split(",")
        # 加两个列表相加。合并列表
        path_list = path_list + url_path
        path_list = list(set(path_list))
        # 列表转字符串
        final_path = ",".join(path_list)
        logging.info("拖放后的文件路径[%s]", final_path)
        self.local_file_path.setText(final_path)
