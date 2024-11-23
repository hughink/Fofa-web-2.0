import csv
import io
from flask import Blueprint, Response, request, jsonify
from src.sqlquery.database_manager import create_db_connection
from src.config.config_checker import read_config  # 引入配置读取函数

export_bp = Blueprint('export', __name__)


def get_database_config():
    """获取数据库配置"""
    config = read_config()
    db_user = config.get('DB_USER')
    db_password = config.get('DB_PASSWORD')
    db_name = config.get('DB_NAME')
    db_host = config.get('DB_HOST')
    return db_user, db_password, db_name, db_host


# 导出所有结果
@export_bp.route('/export_all', methods=['POST'])
def export_all():
    results = request.json.get('results')
    if not results:
        return jsonify({'error': '没有可导出的结果'}), 400

    def generate():
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(
            ['IP', '端口', '协议', '国家', '省份', '城市', '主机', '域名', '系统', '指纹', '归属', 'ICP', '标题',
             '路径', '企业性质', '互联网服务提供商', '页面类型', '来源'])

        for result in results:
            writer.writerow([
                result.get('ip', ''),
                result.get('port', ''),
                result.get('protocol', ''),
                result.get('country_name', ''),
                result.get('region', ''),
                result.get('city', ''),
                result.get('host', ''),
                result.get('domain', ''),
                result.get('os', ''),
                result.get('components', ''),
                result.get('unit', ''),
                result.get('icp', ''),
                result.get('title', ''),
                result.get('path', ''),
                result.get('nature', ''),
                result.get('isp', ''),
                result.get('page_type', ''),
                result.get('from', '')
            ])

        output.seek(0)
        yield output.read()

    return Response(generate(), mimetype='text/csv',
                    headers={'Content-Disposition': 'attachment; filename=all_results.csv'})


# 导出 IP
@export_bp.route('/export_ip', methods=['POST'])
def export_ip():
    results = request.json.get('results')
    if not results:
        return jsonify({'error': '没有可导出的结果'}), 400

    def generate():
        output = io.StringIO()
        for result in results:
            output.write(f"{result.get('ip', '')}\n")
        output.seek(0)
        yield output.read()

    return Response(generate(), mimetype='text/plain',
                    headers={'Content-Disposition': 'attachment; filename=ip_results.txt'})


# 导出 Host
@export_bp.route('/export_host', methods=['POST'])
def export_host():
    results = request.json.get('results')
    if not results:
        return jsonify({'error': '没有可导出的结果'}), 400

    def generate():
        output = io.StringIO()
        for result in results:
            output.write(f"{result.get('host', '')}\n")
        output.seek(0)
        yield output.read()

    return Response(generate(), mimetype='text/plain',
                    headers={'Content-Disposition': 'attachment; filename=host_results.txt'})


# 导出聚合结果
@export_bp.route('/export_aggregation', methods=['GET'])
def export_aggregation():
    results = []
    db_user, db_password, db_name, db_host = get_database_config()  # 获取数据库配置

    # 创建数据库连接，并查询数据
    with create_db_connection(db_user, db_password, db_name, db_host) as conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM search_history")
        results = cursor.fetchall()
        cursor.close()

    if not results:
        return jsonify({'error': '没有可导出的结果'}), 400

    def generate():
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(['ID', '来源', '查询语句', '查询时间', '主机名', '路径', '页面标题', 'IP', '端口', '协议', '域名', '页面类型',
                         '操作系统', '产品信息', '组织名称', '归属单位', 'ICP备案信息', '国家', '省份', '城市', '企业性质',
                         '互联网服务提供商', 'JARM指纹'])

        for result in results:
            writer.writerow([
                result.get('id', ''),
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
                result.get('unit', ''),
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


# 导出独特的 Host
@export_bp.route('/export_hosts', methods=['GET'])
def export_hosts():
    results = []
    db_user, db_password, db_name, db_host = get_database_config()  # 获取数据库配置

    # 创建数据库连接，并查询数据
    with create_db_connection(db_user, db_password, db_name, db_host) as conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT DISTINCT host FROM search_history")
        results = cursor.fetchall()
        cursor.close()

    if not results:
        return jsonify({'error': '没有可导出的结果'}), 400

    def generate():
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(['Host'])

        for result in results:
            writer.writerow([result.get('host', '')])

        output.seek(0)
        yield output.read()

    return Response(generate(), mimetype='text/csv',
                    headers={'Content-Disposition': 'attachment; filename=host_results.csv'})


# 导出独特的 IP
@export_bp.route('/export_ips', methods=['GET'])
def export_ips():
    results = []
    db_user, db_password, db_name, db_host = get_database_config()  # 获取数据库配置

    # 创建数据库连接，并查询数据
    with create_db_connection(db_user, db_password, db_name, db_host) as conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT DISTINCT ip FROM search_history")
        results = cursor.fetchall()
        cursor.close()

    if not results:
        return jsonify({'error': '没有可导出的结果'}), 400

    def generate():
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(['IP'])

        for result in results:
            writer.writerow([result.get('ip', '')])

        output.seek(0)
        yield output.read()

    return Response(generate(), mimetype='text/csv',
                    headers={'Content-Disposition': 'attachment; filename=ip_results.csv'})
