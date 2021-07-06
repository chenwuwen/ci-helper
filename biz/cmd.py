# -*- coding: utf-8 -*-
import json
import os
import logging


# 读取Dockerfile文件
def read_docker_file(filename: str):
    logging.info(os.path.curdir)
    logging.info(os.path.abspath(os.path.curdir))
    if filename.endswith(".jar"):
        # 后端镜像Dockerfile
        if not os.path.exists("Dockerfile"):
            # 如果当前目录下不存在Dockerfile文件则使用内置的Dockerfile.否则使用外置的Dockerfile.这也算是一种灵活方式
            file = os.path.join(os.path.curdir, 'config', 'Dockerfile')
        else:
            file = "Dockerfile"
    else:
        # 前端镜像DockerFile
        if not os.path.exists("Font_Dockerfile"):
            # 如果当前目录下不存在Dockerfile文件则使用内置的Dockerfile.否则使用外置的Dockerfile.这也算是一种灵活方式
            file = os.path.join(os.path.curdir, 'config', 'Font_Dockerfile')
        else:
            file = "Font_Dockerfile"

    logging.info(file)
    with open(file, 'rb') as f:
        return f.read().decode()


# 返回Dockerfile文件
def get_docker_file(_dict):
    tmp = read_docker_file(_dict['_archive_path'])
    logging.info("构建Dockerfile文件的参数")
    logging.info(_dict)
    return tmp.format(**_dict)


# 得到Docker构建命令
def get_build_command(_dict):
    # command = 'docker build -t {image_name}:{image_tag} -f {docker_file_path} .'
    command = 'docker build -t {image_name}:{image_tag} .'
    return command.format(**_dict)


# 得到Docker tag命令
def get_tag_command(_dict, remote: str):
    image = _dict['image_name'] + ":" + _dict['image_tag']
    if remote.endswith("/"):
        repo_image = remote + image
        return f"docker tag {image} {repo_image}"
    else:
        repo_image = remote + "/" + image
        return f"docker tag {image} {repo_image}"


# 得到Docker推送命令
def get_push_command(_dict, remote: str):
    image = _dict['image_name'] + ":" + _dict['image_tag']
    if remote.endswith("/"):
        image = remote + image
        return f"docker push {image}"
    else:
        image = remote + "/" + image
        return f"docker push {image}"


# 得到所有的配置信息
def get_all_config():
    if not os.path.exists("config.json"):
        logging.info("配置文件不存在,创建初始化配置文件")
        init_config = """{"host":"","user_name":"","password":"","port":"","push":FALSE,"remote":"","services":{}}"""
        config = json.loads(init_config)
        logging.info(config)
        return save_config(config)
    with open("config.json", "r", encoding='UTF-8') as load_f:
        return json.load(load_f)


# 保存服务器连接配置
def save_connect_config(host: str, username: str, password: str, port: str):
    config = get_all_config()
    config['host'] = host
    config['user_name'] = username
    config['password'] = password
    config['port'] = port
    save_config(config)


# 保存推送配置
def save_push_options(push: bool, remote: str):
    config = get_all_config()
    config['push'] = push
    config['remote'] = remote
    save_config(config)


def save_config(config):
    # 这里先使用dumps再使用write的原因是,虽然dump可以直接把字典写到文件里,但是如果字典里存在中文就会有问题
    data = json.dumps(config, ensure_ascii=False)
    # 创建并保存
    with open("config.json", 'w', encoding='UTF-8') as f:
        f.write(data)
        return config
