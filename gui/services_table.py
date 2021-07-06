# -*- coding: utf-8 -*-

# 配置表格
import cmd

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QStandardItem, QCursor, QStandardItemModel
from PyQt5.QtWidgets import QWidget, QTableView, QVBoxLayout, QHeaderView, QMenu, QAction
import logging
import biz.cmd
import gui.dialog


class ServicesTable(QWidget):

    def __init__(self, parent=None):
        super(ServicesTable, self).__init__(parent)
        self.parent = parent

        # 设置标题与初始大小
        self.setWindowTitle('QTableView表格视图的例子')
        self.resize(500, 300)

        # 设置数据层次结构，4行4列
        self.model = QStandardItemModel(4, 5)

        # 设置水平方向四个头标签文本内容
        self.model.setHorizontalHeaderLabels(['id', '文件名', '镜像名', 'Tag', '备注'])

        # 实例化表格视图，设置模型为自定义的模型
        self.tableView = QTableView()
        self.tableView.setModel(self.model)
        # 隐藏第一列
        self.tableView.hideColumn(0)

        # #todo 优化1 表格填满窗口
        # 水平方向标签拓展剩下的窗口部分，填满表格
        self.tableView.horizontalHeader().setStretchLastSection(True)
        # 水平方向，表格大小拓展到适当的尺寸
        self.tableView.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        # 设置布局
        layout = QVBoxLayout()
        layout.addWidget(self.tableView)
        # 少这句，右键没有任何反应的。
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        # 槽函数 customContextMenuRequested右键信号
        self.customContextMenuRequested.connect(self.show_context_menu)
        # self.tableView.itemDelegate().commitData.connect(self.update_service)
        # tableview被编辑了的连接函数。新增删除不算，更新了单元格才算
        self.model.dataChanged.connect(self.update_service)
        self.setLayout(layout)

    # 创建右键菜单
    def show_context_menu(self):
        self.context_menu = QMenu(self)
        self.add_action = QAction("新增")
        self.delete_action = QAction("删除")
        self.context_menu.addAction(self.add_action)
        self.context_menu.addAction(self.delete_action)
        # 声明当鼠标在groupBox控件上右击时，在鼠标位置显示右键菜单只能用popup,exec/exec_两个都不行
        self.context_menu.popup(QCursor.pos())
        # 选中行数/列数
        select_size = len(self.tableView.selectionModel().selection().indexes())
        logging.info("选中行数：{}", str(select_size))
        for index in self.tableView.selectionModel().selection().indexes():
            row, column = index.row(), index.column()
            logging.info(f"当前选中第{row},第{column}列")
        self.add_action.triggered.connect(self.add_service)
        # 如果需要传递参数
        self.delete_action.triggered.connect(lambda: self.remove_service(row))

    def add_service(self):
        logging.info("添加配置")
        dialog = gui.dialog.ServiceDialog(self.parent)
        status = dialog.exec()
        logging.info(status)
        self.init_service(biz.cmd.get_all_config()["services"])

    def remove_service(self, row):
        logging.info(f"删除配置:{row}")
        index = self.model.index(row, 0)
        logging.info(index)
        # 返回一个字典类型
        data = self.model.itemData(index)
        # 因为指定row和column,因此返回的字典只有一个key/value
        file_name = str(data[0])
        logging.info(f"删除：{file_name}")
        config = biz.cmd.get_all_config()
        services = config['services']
        del services[file_name]
        biz.cmd.save_config(config)
        self.model.removeRow(row)

    def update_service(self, index):
        logging.info(f"第{index.row() + 1}行第{index.column() + 1}列的数据被编辑了")
        new_data = self.model.itemData(index)
        logging.info("更新配置,新配置为：%s", new_data[0])

        id_index = self.model.index(index.row(), 0)
        # id列是被隐藏的,因此无法被更改
        id_value = self.model.itemData(id_index)[0]
        row_data = []
        # 取到指定行的所有列的值
        for i in range(self.model.columnCount()):
            each_index = self.model.index(index.row(), i)
            row_data.append(self.model.itemData(each_index)[0])

        logging.info("更新table后的行的数据：%s", row_data)
        new_service = Service()
        new_service.file_name = row_data[1]
        new_service.image_name = row_data[2]
        new_service.image_tag = row_data[3]
        new_service.remark = row_data[4]
        all_config = biz.cmd.get_all_config()
        services = all_config["services"]
        if row_data[0] == row_data[1]:
            # 取到原有配置(文件名是json的key)
            # 说明没有更改文件名
            services[row_data[0]] = new_service.__dict__
        else:
            # 说明改了文件名。则删除原配置,添加新配置
            del services[row_data[0]]
            services[row_data[1]] = new_service.__dict__
        biz.cmd.save_config(all_config)
        logging.info("配置文件已更新,初始化Service配置")
        self.init_service(all_config['services'])

    def init_service(self, kwargs):
        logging.info("初始化服务配置")
        services = []
        for key, arg in kwargs.items():
            # json转换为对象
            service = Service()
            service.__dict__ = arg
            services.append(service)
        logging.info("配置数:%s", str(len(services)))
        # 重设rowCount.这里应一直为0,否则会出现多余空白行
        # count = len(services) - 1
        self.model.setRowCount(0)
        for service in services:
            self.model.appendRow([
                QStandardItem(service.file_name),
                QStandardItem(service.file_name),
                QStandardItem(service.image_name),
                QStandardItem(service.image_tag),
                QStandardItem(service.remark)
            ])


class Service:

    def __init__(self, data=None):
        self.file_name = ""
        self.image_name = ""
        self.image_tag = ""
        self.remark = ""
