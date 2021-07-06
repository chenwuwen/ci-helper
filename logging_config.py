import logging
import logging.config
import os
import yaml
import coloredlogs


def setup_logging(default_path='config/logging.yaml', default_level=logging.INFO, env_key='LOG_CFG'):
    """
    | **@author:** Prathyush SP
    | Logging Setup
    """
    path = default_path
    os.getenv("")
    value = os.getenv(env_key, None)
    print(os.path.expanduser('~'))
    if value:
        path = value
    if os.path.exists(path):
        with open(path, 'rt', encoding="utf-8") as f:
            try:
                # 把yaml文件读成字典
                config = yaml.safe_load(f.read())
                try:
                    filename = config['handlers']['file_handler']['filename']
                    if filename.startswith('$'):
                        index = filename.index("/")
                        env_name = filename[0:index]
                        print(f"环境变量名称：{env_name}")
                        env_value = os.path.expandvars(env_name)
                        new_value = filename.replace(env_name, env_value)
                        config['handlers']['file_handler']['filename'] = new_value
                except:
                    pass
                # 将字典设置成logging的配置,需要注意的时需要单独import 一下 logging.config
                logging.config.dictConfig(config)
                # 设置日志颜色,只对控制台有效
                coloredlogs.install()
                print("Custom Logging Config Success!")
            except Exception as e:
                print(e)
                print('Error in Logging Configuration. Using default configs')
                logging.basicConfig(level=default_level)
                coloredlogs.install(level=default_level)
    else:
        logging.basicConfig(level=default_level)
        coloredlogs.install(level=default_level)
        print('Failed to load configuration file. Using default configs')
