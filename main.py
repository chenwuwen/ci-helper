import logging
import sys

from PyQt5.QtWidgets import QApplication

from biz.cmd import read_docker_file
from gui.main_ui import Application
import logging_config

# logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
# logger = logging.getLogger(__name__)

logging_config.setup_logging()
# # 不填参数默认就是取的root
logger = logging.getLogger()

print(logger.handlers)

def print_hi(_dict):
    tmp = read_docker_file()
    print(tmp)
    print(_dict)
    a = tmp.format(**_dict)
    b = "echo \r\n\t {dock_file} >> ".format(dock_file=a)
    print(b)


if __name__ == '__main__':
    # dic = {"age": "ss", "_archive_path": "sss", "sex": 46}
    # print_hi(dic)
    app = QApplication(sys.argv)
    ex = Application()
    app.exit(app.exec())
