import json
import os
import logging
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 配置文件路径
CONFIG_FILE = os.path.join(os.path.expanduser("~"), 'config.json')


def read_config():
    """读取配置文件"""
    if not os.path.exists(CONFIG_FILE):
        logger.warning("配置文件不存在，将引导用户到配置页面。")
        return None

    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            config = json.load(f)
            # logger.info(f"读取配置: {config}")  # 添加日志记录
            return config
    except json.JSONDecodeError as e:
        logger.error(f"配置文件格式错误: {e}")
    except Exception as e:
        logger.error(f"读取配置文件时发生错误: {e}")

    return None


def is_config_complete(config):
    """检查配置是否完整"""
    required_keys = ['FOFA_EMAIL', 'FOFA_KEY', 'QUAKE_TOKEN', 'DB_USER', 'DB_PASSWORD', 'DB_NAME', 'DB_HOST']
    complete = all(config.get(key) for key in required_keys)
    logger.debug(f"配置完整性检查: {complete}, 当前配置: {config}")
    return complete


def write_config(email, key, quake_token, db_user, db_password, db_name, db_host='localhost'):
    """写入配置文件"""
    config_data = {
        'FOFA_EMAIL': email,
        'FOFA_KEY': key,
        'QUAKE_TOKEN': quake_token,
        'DB_USER': db_user,
        'DB_PASSWORD': db_password,
        'DB_NAME': db_name,
        'DB_HOST': db_host
    }

    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, indent=4)
        logger.info("配置已写入文件。")
    except Exception as e:
        logger.error(f"写入配置文件时发生错误: {e}")


class ConfigChangeHandler(FileSystemEventHandler):
    """配置文件变化处理类"""

    def on_modified(self, event):
        if event.src_path == CONFIG_FILE:
            logger.info("配置文件已修改，重新加载配置。")
            config = read_config()
            if config and is_config_complete(config):
                update_application_config(config)


def update_application_config(config):
    """更新应用程序配置"""
    logger.info("应用程序配置已更新。")
    # 在这里实现更新逻辑，例如更新数据库连接等


def start_config_watcher():
    """启动配置文件监视"""
    event_handler = ConfigChangeHandler()
    observer = Observer()
    observer.schedule(event_handler, path=os.path.dirname(CONFIG_FILE), recursive=False)
    observer.start()
    logger.info("开始监视配置文件变化。")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()


if __name__ == "__main__":
    # 初始加载配置
    config = read_config()
    if config and is_config_complete(config):
        logger.info("配置完整，启动应用程序。")
        # 启动应用程序的其他部分
    else:
        logger.warning("配置不完整，重定向至配置页面。")
