# -*- coding: utf-8 -*-
import logging

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QProgressDialog, QVBoxLayout


class MyProcessBar(QWidget):

    def __init__(self, parent=None):
        super(MyProcessBar, self).__init__(parent)
        self.processBar = QProgressDialog()
        self.init_ui(parent)

    def init_ui(self, parent):
        logging.info("初始化进度条")

        # 不显示任务栏图标
        self.processBar.setWindowFlag(Qt.Tool)
        self.processBar.setModal(True)
        self.processBar.setWindowFlag(Qt.FramelessWindowHint)
        # 这两个设置为繁忙状态
        self.processBar.setMaximum(0)
        self.processBar.setMinimum(0)
        self.processBar.setContentsMargins(0, 0, 0, 0)

        # 背景透明
        # self.processBar.setAttribute(Qt.WA_TranslucentBackground)
        self.processBar.setLabelText("正在执行")

        # 隐藏取消按钮
        self.processBar.setCancelButtonText(None)
        self.processBar.adjustSize()
        self.center(parent)
        # self.processBar.hide()

    def close(self):
        self.processBar.close()

    def center(self, parent):
        rect = parent.geometry()
        x = rect.x() + rect.width() / 2 - self.processBar.width() / 2
        y = rect.y() + rect.height() / 2 - self.processBar.height() / 2
        self.processBar.move(x, y)
