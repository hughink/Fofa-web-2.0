import csv
import io
import os
import json
import urllib3
from flask import Flask, render_template, redirect, url_for, request, jsonify, Response
from src.config.config_checker import read_config, is_config_complete, write_config  # 导入配置检查模块
from src.config.forms import ConfigForm  # 确保 ConfigForm 已定义
from src.sqlquery.database_manager import *  # 导入数据库管理模块
from src.fofa_search.fofa_query import fofa_search  # 导入 FOFA 查询模块
from src.fofa_search.quake_query import quake_search  # 导入 Quake 查询模块

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
    if not is_config_complete(config) and request.endpoint not in ['configure', 'static']:
        logger.warning("配置不完整，重定向至 /configure")
        return redirect(url_for('configure'))


@app.route('/configure', methods=['GET', 'POST'])
def configure():
    form = ConfigForm()
    config = read_config()  # 读取最新配置

    # 检查配置完整性
    if is_config_complete(config):
        logger.info("配置完整，重定向至 /fofa_search")
        return redirect(url_for('fofa_search_page'))

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

        # 重新读取配置以更新全局变量
        global FOFA_EMAIL, FOFA_KEY, QUAKE_TOKEN, DB_USER, DB_PASSWORD, DB_NAME, DB_HOST
        config = read_config()
        FOFA_EMAIL = config.get('FOFA_EMAIL')
        FOFA_KEY = config.get('FOFA_KEY')
        QUAKE_TOKEN = config.get('QUAKE_TOKEN')
        DB_USER = config.get('DB_USER', 'your_username')
        DB_PASSWORD = config.get('DB_PASSWORD', 'your_password')
        DB_NAME = config.get('DB_NAME', 'your_database')
        DB_HOST = config.get('DB_HOST', 'localhost')

        logger.info(f"尝试连接数据库: 用户={db_user}, 数据库={db_name}, 主机={db_host}")

        # 连接数据库并创建表
        try:
            with create_db_connection(db_user, db_password, db_name, db_host) as conn:
                if conn and create_database_and_tables(conn, db_name):
                    logger.info("数据库和表创建成功。")
                    return "配置成功，请刷新界面进入！"
                else:
                    logger.error("配置成功，但未能创建数据库和表。")
                    return "配置成功请刷新界面进入！"
        except Exception as e:
            logger.error(f"数据库连接异常: {str(e)}")
            return "数据库连接异常，请检查配置。", 500

    return render_template('configure.html', form=form)


@app.route('/fofa_search', methods=['GET', 'POST'])
def fofa_search_page():
    if not FOFA_EMAIL or not FOFA_KEY:
        return redirect(url_for('configure'))

    results = []
    error_msg = None
    size = 20

    if request.method == 'POST':
        query = request.form.get('query')
        size = int(request.form.get('size', 20))

        if not query:
            error_msg = '请填写搜索查询。'
        else:
            results, error_msg = fofa_search(FOFA_EMAIL, FOFA_KEY, query, size)

            if results:
                try:
                    with create_db_connection(DB_USER, DB_PASSWORD, DB_NAME, DB_HOST) as conn:
                        # 确保传递了 source 参数
                        save_temp_results(conn, 'fofa_temp_results', query, results, 'fofa')

                        # 保存查询历史记录
                        save_search_history(conn, 'fofa_search_history', query, results, 'fofa')

                except Exception as e:
                    logger.error(f"保存查询结果时发生错误: {e}")
                    error_msg = "保存查询结果时发生错误，请稍后重试。"

    # 查询临时表以获取上一步的结果
    try:
        with create_db_connection(DB_USER, DB_PASSWORD, DB_NAME, DB_HOST) as conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM fofa_temp_results")
            results = cursor.fetchall()
            cursor.close()
    except Exception as e:
        logger.error(f"查询临时表时发生错误: {e}")

    return render_template('fofa_search.html', results=results, error_msg=error_msg, size=size)


@app.route('/quake_search', methods=['GET', 'POST'])
def quake_search_page():
    results = []
    error_msg = None
    size = 20
    query = request.args.get('query')

    if request.method == 'POST':
        query = request.form.get('query')
        size = int(request.form.get('size', 20))

        if not query:
            error_msg = '请填写搜索查询。'
        else:
            results, error_msg = quake_search(QUAKE_TOKEN, query, size)

            if results:
                try:
                    with create_db_connection(DB_USER, DB_PASSWORD, DB_NAME, DB_HOST) as conn:
                        # 确保传递了 source 参数
                        save_temp_results(conn, 'quake_temp_results', query, results, 'quake')

                        # 保存查询历史记录
                        save_search_history(conn, 'quake_search_history', query, results, 'quake')
                        logger.info("成功保存Quake查询结果到数据库。")
                except Exception as e:
                    logger.error(f"保存查询结果时发生错误: {e}")
                    error_msg = "保存查询结果时发生错误，请稍后重试。"

    # 查询临时表以获取上一步的结果
    try:
        with create_db_connection(DB_USER, DB_PASSWORD, DB_NAME, DB_HOST) as conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM quake_temp_results")
            results = cursor.fetchall()
            cursor.close()
    except Exception as e:
        logger.error(f"查询临时表时发生错误: {e}")

    return render_template('quake_search.html', results=results, error_msg=error_msg, size=size, query=query)


@app.route('/quake_advanced_search')
def quake_advanced_search():
    return render_template('quake_searchpro.html')  # 确保存在该模板


@app.route('/fofa_advanced_search')
def fofa_advanced_search():
    return render_template('fofa_searchpro.html')  # 确保存在该模板


@app.route('/data_panel')
def data_panel():
    results = []

    with create_db_connection(DB_USER, DB_PASSWORD, DB_NAME, DB_HOST) as conn:
        if conn:
            cursor = conn.cursor(dictionary=True)
            query = """
                SELECT ip, 
                       port,
                       protocols, 
                       domains, 
                       hosts,
                       titles, 
                       components
                FROM data_panel_history
                ORDER BY ip, port;
            """
            cursor.execute(query)
            results = cursor.fetchall()
            cursor.close()

    ip_dict = {}

    for row in results:
        ip = row['ip']
        port = row['port']

        protocols = row['protocols'].split(', ') if row['protocols'] else []
        domains = row['domains'].split(', ') if row['domains'] else []
        hosts = row['hosts'].split(', ') if row['hosts'] else []
        titles = row['titles'].split(', ') if row['titles'] else []
        components = row['components'].split(', ') if row['components'] else []

        if ip not in ip_dict:
            ip_dict[ip] = []

        ip_dict[ip].append({
            'port': port,
            'protocols': protocols,
            'domains': domains,
            'hosts': hosts,
            'titles': titles,
            'components': components
        })

    results_to_render = [{'ip': ip, 'details': details} for ip, details in ip_dict.items()]

    return render_template('data_panel.html', results=results_to_render)


@app.route('/about')
def about():
    return render_template('about.html')  # 确保存在该模板


@app.route('/export_all', methods=['POST'])
def export_all():
    results = request.json.get('results')
    if not results:
        return jsonify({'error': '没有可导出的结果'}), 400

    def generate():
        output = io.StringIO()
        writer = csv.writer(output)
        # 写入表头，确保与前端表格一致
        writer.writerow(
            ['IP', '端口', '协议', '国家', '省份', '城市', '主机', '域名', '系统', '指纹', '归属', 'ICP', '标题',
             '路径', '企业性质', '互联网服务提供商', '页面类型', '来源'])

        for result in results:
            writer.writerow([
                result.get('ip', ''),  # 使用 get 方法以避免 KeyError
                result.get('port', ''),
                result.get('protocol', ''),
                result.get('country_name', ''),
                result.get('region', ''),
                result.get('city', ''),
                result.get('host', ''),
                result.get('domain', ''),
                result.get('os', ''),
                result.get('components', ''),  # 指纹信息
                result.get('unit', ''),
                result.get('icp', ''),
                result.get('title', ''),
                result.get('path', ''),
                result.get('nature', ''),  # 企业性质
                result.get('isp', ''),  # 互联网服务提供商
                result.get('page_type', ''),  # 页面类型
                result.get('from', '')  # 数据来源
            ])

        output.seek(0)
        yield output.read()

    return Response(generate(), mimetype='text/csv',
                    headers={'Content-Disposition': 'attachment; filename=all_results.csv'})


@app.route('/export_ip', methods=['POST'])
def export_ip():
    results = request.json.get('results')
    if not results:
        return jsonify({'error': '没有可导出的结果'}), 400

    def generate():
        output = io.StringIO()
        for result in results:
            output.write(f"{result.get('ip', '')}\n")  # 每个IP写入新的一行，使用 get 方法
        output.seek(0)
        yield output.read()

    return Response(generate(), mimetype='text/plain',
                    headers={'Content-Disposition': 'attachment; filename=ip_results.txt'})


@app.route('/export_host', methods=['POST'])
def export_host():
    results = request.json.get('results')
    if not results:
        return jsonify({'error': '没有可导出的结果'}), 400

    def generate():
        output = io.StringIO()
        for result in results:
            output.write(f"{result.get('host', '')}\n")  # 每个Host写入新的一行，使用 get 方法
        output.seek(0)
        yield output.read()

    return Response(generate(), mimetype='text/plain',
                    headers={'Content-Disposition': 'attachment; filename=host_results.txt'})


@app.route('/data_aggregation', methods=['GET'])
def data_aggregation():
    results = []
    # 创建数据库连接，并查询数据
    with create_db_connection(DB_USER, DB_PASSWORD, DB_NAME, DB_HOST) as conn:
        if conn:
            cursor = conn.cursor(dictionary=True)
            # 查询 FOFA 和 Quake 数据
            cursor.execute("""
                SELECT 'FOFA' AS source, query, host, path, title, ip, port, domain, protocol, jarm, 
                       page_type, os, org, as_organization, unit, icp, country_name, region, city, nature, isp, 
                       components, created_at 
                FROM fofa_search_history
                UNION ALL 
                SELECT 'Quake' AS source, query, host, path, title, ip, port, domain, protocol, jarm,
                       page_type, os, org, as_organization, unit, icp, country_name, region, city, nature, isp, 
                       components, created_at 
                FROM quake_search_history
            """)
            results = cursor.fetchall()

            # 将查询结果插入到 data_panel_history 表中
            for row in results:
                ip = row['ip']
                port = row['port']

                # 检查是否已存在相同的 IP 和 port
                check_query = "SELECT COUNT(*) AS count FROM data_panel_history WHERE ip = %s AND port = %s"
                cursor.execute(check_query, (ip, port))
                exists_result = cursor.fetchone()

                # 确保 exists_result 不为 None 并且可以安全访问 count
                if exists_result is not None and 'count' in exists_result and exists_result['count'] == 0:
                    protocols = row['protocol'].split(',') if row['protocol'] else []
                    domains = row['domain'].split(',') if row['domain'] else []
                    hosts = [row['host']] if row['host'] else []
                    titles = [row['title']] if row['title'] else []
                    components = row['components'].split(',') if row['components'] else []

                    insert_query = """
                        INSERT INTO data_panel_history (ip, port, protocols, domains, hosts, titles, components)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """

                    cursor.execute(insert_query, (
                        ip,
                        port,
                        ', '.join(protocols),  # 将列表转换成字符串
                        ', '.join(domains),
                        ', '.join(hosts),
                        ', '.join(titles),
                        ', '.join(components)
                    ))

            conn.commit()  # 提交插入操作
            cursor.close()

    return render_template('data_aggregation.html', results=results)




@app.route('/export_aggregation', methods=['GET'])
def export_aggregation():
    results = []

    # 创建数据库连接，并查询数据
    with create_db_connection(DB_USER, DB_PASSWORD, DB_NAME, DB_HOST) as conn:
        if conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("""
                SELECT 'FOFA' AS source, query, created_at, host, ip, port, protocol, domain, country_name, region, 
                        city, as_organization, org, os, icp, title, jarm, nature, isp, page_type, path, components, unit
                FROM fofa_search_history
                UNION ALL
                SELECT 'Quake' AS source, query, created_at, host, ip, port, protocol, domain, country_name, region, 
                        city, as_organization, org, os, icp, title, jarm, nature, isp, page_type, path, components, unit
                FROM quake_search_history
            """)
            results = cursor.fetchall()
            cursor.close()

    if not results:
        return jsonify({'error': '没有可导出的结果'}), 400

    def generate():
        output = io.StringIO()
        writer = csv.writer(output)
        # 写入表头
        writer.writerow([
            '来源', '查询语句', '查询时间', '主机名', '路径', '页面标题', 'IP', '端口', '协议', '域名', '页面类型',
            '操作系统', '产品信息', '组织名称', '归属单位', 'ICP备案信息', '国家', '省份', '城市', '企业性质', '互联网服务提供商',
            'JARM指纹'
        ])

        for result in results:
            writer.writerow([
                result.get('source', ''),
                result.get('query', ''),
                result.get('created_at', ''),
                result.get('host', ''),
                result.get('path', ''),
                result.get('title', ''),
                result.get('ip', ''),
                result.get('port', ''),
                result.get('protocol', ''),
                result.get('domain', ''),
                result.get('page_type', ''),
                result.get('os', ''),
                result.get('components', ''),
                result.get('org', ''),
                result.get('unit', ''),  # 归属单位
                result.get('icp', ''),
                result.get('country_name', ''),
                result.get('region', ''),
                result.get('city', ''),
                result.get('nature', ''),
                result.get('isp', ''),
                result.get('jarm', '')
            ])

        output.seek(0)
        yield output.read()

    return Response(generate(), mimetype='text/csv',
                    headers={'Content-Disposition': 'attachment; filename=aggregation_results.csv'})


@app.route('/export_hosts', methods=['GET'])
def export_hosts():
    results = []

    # 创建数据库连接，并查询数据
    with create_db_connection(DB_USER, DB_PASSWORD, DB_NAME, DB_HOST) as conn:
        if conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("""
                SELECT DISTINCT host
                FROM fofa_search_history
                UNION
                SELECT DISTINCT host
                FROM quake_search_history
            """)
            results = cursor.fetchall()
            cursor.close()

    if not results:
        return jsonify({'error': '没有可导出的结果'}), 400

    def generate():
        output = io.StringIO()
        writer = csv.writer(output)
        # 写入表头
        writer.writerow(['Host'])

        for result in results:
            writer.writerow([result.get('host', '')])

        output.seek(0)
        yield output.read()

    return Response(generate(), mimetype='text/csv',
                    headers={'Content-Disposition': 'attachment; filename=host_results.csv'})


@app.route('/export_ips', methods=['GET'])
def export_ips():
    results = []

    # 创建数据库连接，并查询数据
    with create_db_connection(DB_USER, DB_PASSWORD, DB_NAME, DB_HOST) as conn:
        if conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("""
                SELECT DISTINCT ip
                FROM fofa_search_history
                UNION
                SELECT DISTINCT ip
                FROM quake_search_history
            """)
            results = cursor.fetchall()
            cursor.close()

    if not results:
        return jsonify({'error': '没有可导出的结果'}), 400

    def generate():
        output = io.StringIO()
        writer = csv.writer(output)
        # 写入表头
        writer.writerow(['IP'])

        for result in results:
            writer.writerow([result.get('ip', '')])

        output.seek(0)
        yield output.read()

    return Response(generate(), mimetype='text/csv',
                    headers={'Content-Disposition': 'attachment; filename=ip_results.csv'})


@app.route('/clear_database', methods=['POST'])
def clear_database():
    with create_db_connection(DB_USER, DB_PASSWORD, DB_NAME, DB_HOST) as conn:
        if conn:
            cursor = conn.cursor()
            # 清空 FOFA 和 Quake 表
            cursor.execute("TRUNCATE TABLE fofa_search_history")
            cursor.execute("TRUNCATE TABLE quake_search_history")
            conn.commit()
            cursor.close()
    return jsonify({'message': '数据库表已成功清空'}), 200


@app.route('/clear_data_panel_history', methods=['POST'])
def clear_data_panel_history():
    with create_db_connection(DB_USER, DB_PASSWORD, DB_NAME, DB_HOST) as conn:
        if conn:
            cursor = conn.cursor()
            # 清空 data_panel_history 表
            cursor.execute("TRUNCATE TABLE data_panel_history")
            conn.commit()
            cursor.close()
    return jsonify({'message': '数据面板历史记录已成功清空'}), 200


if __name__ == '__main__':
    app.run(debug=True)
