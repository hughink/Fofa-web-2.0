from flask import Blueprint, render_template, jsonify, request
from src.sqlquery.database_manager import create_db_connection
from src.config.config_checker import read_config  # 引入配置读取函数
import logging

# 配置日志
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

data_panel_bp = Blueprint('data_panel', __name__)


def get_database_config():
    """获取数据库配置"""
    config = read_config()
    return config.get('DB_USER'), config.get('DB_PASSWORD'), config.get('DB_NAME'), config.get('DB_HOST')


@data_panel_bp.route('/data_panel')
def data_panel():
    logger.debug("开始处理 /data_panel 请求")

    db_user, db_password, db_name, db_host = get_database_config()  # 获取数据库配置

    # 创建数据库连接
    conn = create_db_connection(db_user, db_password, db_name, db_host)
    if conn is None:
        logger.error("无法连接到数据库")
        return jsonify({"error": "无法连接到数据库"}), 500  # 返回错误信息

    cursor = None  # 初始化游标变量
    ip_dict = {}  # 初始化字典
    try:
        logger.debug("成功连接到数据库，准备执行查询。")

        cursor = conn.cursor(dictionary=True)  # 赋值游标
        query = """
            SELECT id,  
                   ip, 
                   port,
                   protocol, 
                   domain, 
                   host,
                   title, 
                   components,
                   city,
                   page_type,
                   os,
                   icp,
                   unit,
                   tags,
                   remarks
            FROM data_panel_history
            ORDER BY ip, port;  
        """
        logger.debug(f"执行查询: {query}")
        cursor.execute(query)

        results = cursor.fetchall()  # 执行查询并将结果存储在 results 中
        logger.debug(f"查询成功，返回 {len(results)} 条记录。")

        logger.debug("开始处理查询结果")
        for row in results:
            ip = row['ip']
            port = row['port']
            protocol = row['protocol'].split(', ') if row['protocol'] else []
            domain = row['domain'].split(', ') if row['domain'] else []
            host = row['host'].split(', ') if row['host'] else []
            title = row['title'].split(', ') if row['title'] else []
            components = row['components'].split(', ') if row['components'] else []

            if ip not in ip_dict:
                ip_dict[ip] = []

            ip_dict[ip].append({
                'id': row['id'],
                'port': port,
                'protocol': protocol,
                'domain': domain,
                'host': host,
                'title': title,
                'components': components,
                'city': row['city'] if row['city'] else "N/A",
                'page_type': row['page_type'] if row['page_type'] else "N/A",
                'os': row['os'] if row['os'] else "N/A",
                'icp': row['icp'] if row['icp'] else "N/A",
                'unit': row['unit'] if row['unit'] else "N/A",
                'tags': row['tags'] if row['tags'] else "N/A",
                'remarks': row['remarks'] if row['remarks'] else "N/A",
            })

        results_to_render = [{'ip': ip, 'details': details} for ip, details in ip_dict.items()]
        logger.debug(f"返回 {len(results_to_render)} 条处理后的记录。")
        return render_template('data_panel.html', results=results_to_render)

    except Exception as e:
        logger.error(f"执行查询时发生错误: {e}")
        return jsonify({"error": str(e)}), 500  # 返回错误信息

    finally:
        if cursor is not None:
            cursor.close()  # 确保游标被关闭
        if conn is not None:
            conn.close()  # 确保连接被关闭


@data_panel_bp.route('/get_statistics', methods=['GET'])
def get_statistics():
    """统计去重数据的 API"""
    try:
        db_user, db_password, db_name, db_host = get_database_config()  # 获取数据库配置

        # 创建数据库连接
        conn = create_db_connection(db_user, db_password, db_name, db_host)
        if conn is None:
            return jsonify({"error": "无法连接到数据库"}), 500  # 返回错误信息

        with conn:
            cursor = conn.cursor()

            # 初始化统计对象
            stats = {
                'unique_ip': [],
                'unique_domain': [],
                'unique_protocol': [],
                'unique_port': [],
                'unique_components': [],
                'unique_title': [],
                'unique_remarks': [],
                'unique_tags': []
            }

            # 统计并获取唯一 IP 地址
            cursor.execute("SELECT DISTINCT ip FROM data_panel_history")
            stats['unique_ip'] = [row[0] for row in cursor.fetchall()]

            # 统计并获取唯一域名
            cursor.execute("SELECT DISTINCT host FROM data_panel_history")
            stats['unique_domain'] = [row[0] for row in cursor.fetchall()]

            # 统计并获取唯一协议
            cursor.execute("SELECT DISTINCT protocol FROM data_panel_history")
            stats['unique_protocol'] = [row[0] for row in cursor.fetchall()]

            # 统计并获取唯一端口
            cursor.execute("SELECT DISTINCT port FROM data_panel_history")
            stats['unique_port'] = [row[0] for row in cursor.fetchall()]

            # 统计并获取唯一指纹
            cursor.execute("SELECT DISTINCT components FROM data_panel_history")
            stats['unique_components'] = [row[0] for row in cursor.fetchall()]

            # 统计并获取唯一网页标题
            cursor.execute("SELECT DISTINCT title FROM data_panel_history")
            stats['unique_title'] = [row[0] for row in cursor.fetchall()]

            # 统计并获取唯一备注
            cursor.execute("SELECT DISTINCT remarks FROM data_panel_history WHERE remarks IS NOT NULL AND "
                           "remarks != ''")
            stats['unique_remarks'] = [row[0] for row in cursor.fetchall()]

            # 统计并获取唯一标签
            cursor.execute("SELECT DISTINCT tags FROM data_panel_history WHERE tags IS NOT NULL AND tags != ''")
            stats['unique_tags'] = [row[0] for row in cursor.fetchall()]

            # 计算每个类别的数量
            stats['unique_ip_count'] = len(stats['unique_ip'])
            stats['unique_domain_count'] = len(stats['unique_domain'])
            stats['unique_protocol_count'] = len(stats['unique_protocol'])
            stats['unique_port_count'] = len(stats['unique_port'])
            stats['unique_components_count'] = len(stats['unique_components'])
            stats['unique_title_count'] = len(stats['unique_title'])
            stats['unique_remarks_count'] = len(stats['unique_remarks'])
            stats['unique_tags_count'] = len(stats['unique_tags'])

            return jsonify(stats), 200

    except Exception as e:
        return jsonify({'error': '发生了不明错误: ' + str(e)}), 500


@data_panel_bp.route('/add_card_data', methods=['POST'])
def add_card_data():
    # 获取请求中的数据
    data = request.get_json()
    ip = data.get('ip')
    host = data.get('host')
    port = data.get('port')
    protocol = data.get('protocol')
    components = data.get('components')
    remarks = data.get('remarks', '')
    tags = data.get('tags', '')

    # 验证必填字段
    if not ip or not host or not port or not protocol or not components:
        return jsonify({'error': '所有必填字段都必须填写。'}), 400

    # 查询数据库获取最大ID并计算下一个ID
    try:
        db_user, db_password, db_name, db_host = get_database_config()  # 获取数据库配置
        with create_db_connection(db_user, db_password, db_name, db_host) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT MAX(id) FROM data_panel_history")
            max_id = cursor.fetchone()[0]
            next_id = max_id + 1 if max_id is not None else 1  # 从1开始

            # 插入数据的逻辑
            cursor.execute("""
                INSERT INTO data_panel_history (id, ip, host, port, protocol, components, remarks, tags)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (next_id, ip, host, port, protocol, components, remarks, tags))
            conn.commit()
            return jsonify({'message': '卡片添加成功!', 'id': next_id}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@data_panel_bp.route('/delete_card', methods=['DELETE'])
def delete_card():
    data = request.get_json()
    id = data.get('id')
    if not id:
        return jsonify({'error': 'ID不能为空'}), 400

    try:
        db_user, db_password, db_name, db_host = get_database_config()  # 获取数据库配置
        with create_db_connection(db_user, db_password, db_name, db_host) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM data_panel_history WHERE id = %s", (id,))
            conn.commit()
            return jsonify({'message': '卡片已成功删除。'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@data_panel_bp.route('/add_remark', methods=['POST'])
def add_remark():
    data = request.get_json()
    id = data.get('id')
    remark = data.get('remark')
    if not id or not remark:
        return jsonify({'error': 'ID 和备注不能为空'}), 400

    try:
        db_user, db_password, db_name, db_host = get_database_config()  # 获取数据库配置
        with create_db_connection(db_user, db_password, db_name, db_host) as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE data_panel_history SET remarks = %s WHERE id = %s", (remark, id))
            conn.commit()
            return jsonify({'message': '备注添加成功!'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@data_panel_bp.route('/update_remark', methods=['PUT'])
def update_remark():
    data = request.get_json()
    id = data.get('id')
    remark = data.get('remark')
    if not id or not remark:
        return jsonify({'error': 'ID 和备注不能为空'}), 400

    try:
        db_user, db_password, db_name, db_host = get_database_config()  # 获取数据库配置
        with create_db_connection(db_user, db_password, db_name, db_host) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT remarks FROM data_panel_history WHERE id = %s", (id,))
            existing_remark = cursor.fetchone()
            existing_remark = existing_remark[0] if existing_remark and existing_remark[0] else ''
            new_remark = f"{existing_remark}, {remark}" if existing_remark else remark
            cursor.execute("UPDATE data_panel_history SET remarks = %s WHERE id = %s", (new_remark, id))
            conn.commit()
            return jsonify({'message': '备注更新成功!'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@data_panel_bp.route('/delete_remark', methods=['DELETE'])
def delete_remark():
    data = request.get_json()
    id = data.get('id')
    if not id:
        return jsonify({'error': 'ID不能为空'}), 400

    try:
        db_user, db_password, db_name, db_host = get_database_config()  # 获取数据库配置
        with create_db_connection(db_user, db_password, db_name, db_host) as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE data_panel_history SET remarks = NULL WHERE id = %s", (id,))
            conn.commit()
            return jsonify({'message': '备注删除成功!'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@data_panel_bp.route('/add_tag', methods=['POST'])
def add_tag():
    data = request.get_json()
    id = data.get('id')
    tag = data.get('tag')
    if not id or not tag:
        return jsonify({'error': 'ID 和标签不能为空'}), 400

    try:
        db_user, db_password, db_name, db_host = get_database_config()  # 获取数据库配置
        with create_db_connection(db_user, db_password, db_name, db_host) as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE data_panel_history SET tags = %s WHERE id = %s", (tag, id))
            conn.commit()
            return jsonify({'message': '标签添加成功!'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@data_panel_bp.route('/update_tag', methods=['PUT'])
def update_tag():
    data = request.get_json()
    id = data.get('id')
    tag = data.get('tag')
    if not id or not tag:
        return jsonify({'error': 'ID 和标签不能为空'}), 400

    try:
        db_user, db_password, db_name, db_host = get_database_config()  # 获取数据库配置
        with create_db_connection(db_user, db_password, db_name, db_host) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT tags FROM data_panel_history WHERE id = %s", (id,))
            existing_tags = cursor.fetchone()
            existing_tags = existing_tags[0] if existing_tags and existing_tags[0] else ''
            new_tags = f"{existing_tags}, {tag}" if existing_tags else tag
            cursor.execute("UPDATE data_panel_history SET tags = %s WHERE id = %s", (new_tags, id))
            conn.commit()
            return jsonify({'message': '标签更新成功!'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@data_panel_bp.route('/delete_tag', methods=['DELETE'])
def delete_tag():
    data = request.get_json()
    id = data.get('id')
    if not id:
        return jsonify({'error': 'ID不能为空'}), 400

    try:
        db_user, db_password, db_name, db_host = get_database_config()  # 获取数据库配置
        with create_db_connection(db_user, db_password, db_name, db_host) as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE data_panel_history SET tags = NULL WHERE id = %s", (id,))
            conn.commit()
            return jsonify({'message': '标签删除成功!'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@data_panel_bp.route('/clear_data_panel_history', methods=['DELETE'])
def clear_data_panel_history():
    """清空数据面板历史记录表"""
    try:
        db_user, db_password, db_name, db_host = get_database_config()  # 获取数据库配置
        with create_db_connection(db_user, db_password, db_name, db_host) as conn:
            if conn:
                cursor = conn.cursor()
                # 清空数据面板历史记录表
                cursor.execute("TRUNCATE TABLE data_panel_history")
                conn.commit()
                cursor.close()

        return jsonify({'message': '数据面板历史记录已成功清空'}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500
