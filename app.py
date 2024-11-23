import os
import json
import logging
import urllib3
from src.config.config_checker import read_config, is_config_complete, configure
from src.data_panel.data_panel_routes import data_panel_bp  # 导入数据面板路由
from src.export.export_routes import export_bp  # 导入导出蓝图
from src.data_aggregation.data_aggregation_routes import data_aggregation_bp  # 导入数据聚合蓝图
from flask import Flask, render_template, redirect, url_for, request
from src.fofa_search.fofa_query import fofa_search_page
from src.fofa_search.quake_query import quake_search_page

# 配置日志
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


# 自定义过滤器，用于过滤日志
class StaticFilesFilter(logging.Filter):
    def filter(self, record):
        # 过滤掉包含静态文件请求的日志
        return 'GET /static/' not in record.getMessage()


# 将自定义过滤器添加到werkzeug的logger
werkzeug_logger = logging.getLogger('werkzeug')
werkzeug_logger.addFilter(StaticFilesFilter())

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'  # 设置密钥以支持表单
# 注册导出蓝图
app.register_blueprint(export_bp, url_prefix='/export')  # 添加 URL 前缀以组织路由

# 注册数据面板蓝图
app.register_blueprint(data_panel_bp)  # 数据精简面板

# 注册数据聚合蓝图
app.register_blueprint(data_aggregation_bp)  # 数据聚合面板


@app.route('/fofa_search', methods=['GET', 'POST'])
def fofa_search_route():
    return fofa_search_page(FOFA_EMAIL, FOFA_KEY, DB_USER, DB_PASSWORD, DB_NAME, DB_HOST)


@app.route('/quake_search', methods=['GET', 'POST'])
def quake_search_route():
    return quake_search_page(QUAKE_TOKEN, DB_USER, DB_PASSWORD, DB_NAME, DB_HOST)


@app.route('/quake_advanced_search')
def quake_advanced_search():
    return render_template('quake_searchpro.html')  # 确保存在该模板


@app.route('/fofa_advanced_search')
def fofa_advanced_search():
    return render_template('fofa_searchpro.html')  # 确保存在该模板


@app.route('/about')
def about():
    return render_template('about.html')  # 确保存在该模板


# 配置文件路径
CONFIG_FILE = os.path.join(os.path.expanduser('~'), 'config.json')


def create_default_config():
    """创建默认配置文件"""
    default_config = {
        "FOFA_EMAIL": "",
        "FOFA_KEY": "",
        "QUAKE_TOKEN": "",
        "DB_USER": "your_username",
        "DB_PASSWORD": "your_password",
        "DB_NAME": "your_database",
        "DB_HOST": "localhost"
    }
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(default_config, f, ensure_ascii=False, indent=4)
    logger.info(f"默认配置文件已创建: {CONFIG_FILE}")


# 初始化配置
config = read_config()

if config is None:
    logger.error("未找到配置文件或配置文件格式不正确，创建默认配置文件。")
    create_default_config()
    config = read_config()  # 再次读取配置文件

FOFA_EMAIL = config.get('FOFA_EMAIL')
FOFA_KEY = config.get('FOFA_KEY')
QUAKE_TOKEN = config.get('QUAKE_TOKEN')
DB_USER = config.get('DB_USER', 'your_username')
DB_PASSWORD = config.get('DB_PASSWORD', 'your_password')
DB_NAME = config.get('DB_NAME', 'your_database')
DB_HOST = config.get('DB_HOST', 'localhost')


@app.before_request
def check_config_on_request():
    """每个请求之前检查配置是否完整"""
    global config
    config = read_config()  # 每次请求前读取最新配置
    if not is_config_complete(config) and request.endpoint not in ['configure_route', 'static']:
        logger.warning("配置不完整，重定向至 /configure")
        return redirect(url_for('configure_route'))  # 确保使用正确的路由名称


# 调用 configure 函数以注册路由
configure(app)

if __name__ == '__main__':
    app.run(debug=True)