# -*- coding: utf-8 -*-
from PyQt5.QtCore import Qt, QPoint
from PyQt5.QtWidgets import QPushButton, QLineEdit, QLabel, QGridLayout, QDialog, QMessageBox, QDesktopWidget
import logging
import biz.cmd
import gui.services_table


class ServiceDialog(QDialog):
    def __init__(self, parent=None):
        super(ServiceDialog, self).__init__(parent)
        self.init_ui(parent)

    def init_ui(self, parent):

        self.setWindowTitle("添加构建信息")
        self.setGeometry(300, 300, 450, 250)
        self.center(parent)
        # self.layout().setAlignment(Qt.AlignCenter)
        # 不显示任务栏图标
        self.setWindowFlag(Qt.Tool)
        # 设定窗口标题和窗口的大小和位置。
        file_name_label = QLabel(self.tr("文件名"))
        self.file_name_edit = QLineEdit()

        image_name_label = QLabel(self.tr("镜像名"))
        self.image_name_edit = QLineEdit()

        image_tag_label = QLabel(self.tr("Tag"))
        self.image_tag_edit = QLineEdit()

        mark_label = QLabel(self.tr("备注"))
        self.mark_edit = QLineEdit()

        self.add_btn = QPushButton("添加")

        self.add_btn.clicked.connect(self.add_service)

        grid = QGridLayout()
        grid.addWidget(file_name_label, 1, 0)
        grid.addWidget(self.file_name_edit, 1, 1)
        grid.addWidget(image_name_label, 2, 0)
        grid.addWidget(self.image_name_edit, 2, 1)
        grid.addWidget(image_tag_label, 3, 0)
        grid.addWidget(self.image_tag_edit, 3, 1)
        grid.addWidget(mark_label, 5, 0)
        grid.addWidget(self.mark_edit, 5, 1)
        # 横跨1行2列。最后两个参数
        grid.addWidget(self.add_btn, 6, 0, 1, 2)
        self.setLayout(grid)

    def add_service(self):
        all_config = biz.cmd.get_all_config()
        service = gui.services_table.Service()
        service.remark = self.mark_edit.text()
        service.file_name = self.file_name_edit.text()
        service.image_tag = self.image_tag_edit.text()
        service.image_name = self.image_name_edit.text()
        print(service.file_name)
        if not service.file_name or not service.image_name:
            QMessageBox.warning(self, "提示", "文件名/镜像名不能为空")
            return

        try:
            all_config["services"][service.file_name]
            logging.info("当前配置已存在")
            QMessageBox.warning(self, "提示", "当前配置已存在")
        except Exception as e:
            all_config["services"][service.file_name] = service.__dict__
            biz.cmd.save_config(all_config)
            self.close()

    def center(self, parent):
        rect = parent.geometry()
        x = rect.x() + rect.width() / 2 - self.width() / 2
        y = rect.y() + rect.height() / 2 - self.height() / 2
        self.move(x, y)
