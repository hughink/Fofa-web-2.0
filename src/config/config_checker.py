import json
import os
import logging
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from flask import render_template, redirect, url_for
from src.config.forms import ConfigForm
from src.sqlquery.database_manager import create_db_connection, create_database_and_tables

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 配置文件路径
CONFIG_FILE = os.path.join(os.path.expanduser("~"), 'config.json')


def read_config():
    """读取配置文件，返回配置字典供其他模块使用"""
    if not os.path.exists(CONFIG_FILE):
        logger.warning("配置文件不存在，将引导用户到配置页面。")
        return {}  # 返回空字典以表示没有配置

    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            config = json.load(f)
            return config  # 返回读取的配置字典
    except json.JSONDecodeError as e:
        logger.error(f"配置文件格式错误: {e}")
    except Exception as e:
        logger.error(f"读取配置文件时发生错误: {e}")

    return {}  # 返回空字典以表示读取失败


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


def configure(app):
    """配置路由"""
    @app.route('/configure', methods=['GET', 'POST'])
    def configure_route():
        form = ConfigForm()
        config = read_config()  # 读取最新配置

        # 检查配置完整性
        if is_config_complete(config):
            logger.info("配置完整，重定向至 /fofa_search")
            return redirect(url_for('fofa_search_route'))  # 修改这一行

        if form.validate_on_submit():
            # 从表单获取数据
            email = form.email.data
            key = form.key.data
            quake_token = form.quake_token.data
            db_user = form.db_user.data
            db_password = form.db_password.data
            db_name = form.db_name.data
            db_host = form.db_host.data

            # 写入配置并更新全局变量
            write_config(email, key, quake_token, db_user, db_password, db_name, db_host)

            logger.info(f"尝试连接数据库: 用户={db_user}, 数据库={db_name}, 主机={db_host}")

            # 连接数据库并创建表
            try:
                with create_db_connection(db_user, db_password, db_name, db_host) as conn:
                    if conn:
                        create_database_and_tables(conn, db_name)
                        logger.info("数据库和表创建成功。")
                        return "配置成功，请刷新界面进入！"
                    else:
                        logger.error("配置成功，但未能创建数据库和表。")
                        return "配置成功请刷新界面进入！"
            except Exception as e:
                logger.error(f"数据库连接异常: {str(e)}")
                return "数据库连接异常，请检查配置。", 500

        return render_template('configure.html', form=form)


class ConfigChangeHandler(FileSystemEventHandler):
    """配置文件变化处理类"""

    def on_modified(self, event):
        if event.src_path == CONFIG_FILE:
            logger.info("配置文件已修改，重新加载配置。")
            updated_config = read_config()  # 读取当前更新的配置
            if updated_config and is_config_complete(updated_config):
                update_application_config(updated_config)


def update_application_config(app_config):
    """更新应用程序配置"""
    logger.info("应用程序配置已更新。")
    logger.debug(f"更新的配置内容: {app_config}")


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
    initial_config = read_config()
    if initial_config and is_config_complete(initial_config):
        logger.info("配置完整，启动应用程序。")
    else:
        logger.warning("配置不完整，重定向至配置页面。")
