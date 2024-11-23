import logging
from flask import Blueprint, jsonify, request, render_template
from src.sqlquery.database_manager import create_db_connection
from src.config.config_checker import read_config  # 引入配置读取函数

data_aggregation_bp = Blueprint('data_aggregation', __name__)

logger = logging.getLogger(__name__)


def get_database_config():
    """获取数据库配置"""
    config = read_config()
    db_user = config.get('DB_USER')
    db_password = config.get('DB_PASSWORD')
    db_name = config.get('DB_NAME')
    db_host = config.get('DB_HOST')
    return db_user, db_password, db_name, db_host


@data_aggregation_bp.route('/data_aggregation', methods=['GET'])
def data_aggregation():
    db_user, db_password, db_name, db_host = get_database_config()  # 获取数据库配置

    # 创建数据库连接并查询数据
    with create_db_connection(db_user, db_password, db_name, db_host) as conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM search_history;")
        results = cursor.fetchall()
        cursor.close()

    # 直接在渲染模板时使用查询结果
    return render_template('data_aggregation.html', results=results)


@data_aggregation_bp.route('/sync_data_to_panel', methods=['POST'])
def sync_data_to_panel():
    """将数据聚合表数据同步到精简面板表"""
    cursor = None
    try:
        db_user, db_password, db_name, db_host = get_database_config()  # 获取数据库配置
        with create_db_connection(db_user, db_password, db_name, db_host) as conn:
            if conn:
                logger.info("数据库连接成功")
                cursor = conn.cursor()

                # 从 search_history 表中获取数据
                query = """
                    SELECT 
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
                        unit
                    FROM 
                        search_history;
                """
                cursor.execute(query)
                results = cursor.fetchall()
                logger.info(f"获取的数据行数: {len(results)}")

                # 如果有数据，则插入到精简面板表
                if results:
                    insert_sql = """
                        INSERT INTO data_panel_history 
                        (ip, port, protocol, domain, host, title, components, city, page_type, os, icp, unit)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON DUPLICATE KEY UPDATE
                            protocol = VALUES(protocol),
                            domain = VALUES(domain),
                            host = VALUES(host),
                            components = VALUES(components),
                            city = VALUES(city),
                            page_type = VALUES(page_type),
                            os = VALUES(os),
                            icp = VALUES(icp),
                            unit = VALUES(unit);
                    """
                    cursor.executemany(insert_sql, results)
                    conn.commit()
                return jsonify({'message': '数据同步成功'}), 200
            else:
                return jsonify({'error': '无法连接到数据库'}), 500
    except Exception as e:
        logger.error(f"同步数据时发生错误: {e}")
        return jsonify({'error': '数据同步失败，请稍后重试'}), 500
    finally:
        if cursor:
            cursor.close()


@data_aggregation_bp.route('/delete_rows', methods=['POST'])
def delete_rows():
    ids = request.json.get('ids', [])
    if not ids:
        return jsonify({'error': '没有提供要删除的ID'}), 400

    try:
        db_user, db_password, db_name, db_host = get_database_config()  # 获取数据库配置
        with create_db_connection(db_user, db_password, db_name, db_host) as conn:
            cursor = conn.cursor()
            format_strings = ','.join(['%s'] * len(ids))
            query = f"DELETE FROM search_history WHERE id IN ({format_strings})"
            cursor.execute(query, ids)
            conn.commit()
            return jsonify({'message': '删除成功'}), 200
    except Exception as e:
        logger.error(f"删除记录时发生错误: {str(e)}")
        return jsonify({'error': '删除失败，请稍后重试'}), 500


@data_aggregation_bp.route('/clear_database', methods=['POST'])
def clear_database():
    """清空数据聚合历史记录表"""
    db_user, db_password, db_name, db_host = get_database_config()  # 获取数据库配置
    with create_db_connection(db_user, db_password, db_name, db_host) as conn:
        if conn:
            cursor = conn.cursor()
            # 清空 search 表
            cursor.execute("TRUNCATE TABLE search_history;")
            conn.commit()
            cursor.close()
    return jsonify({'message': '数据库表已成功清空'}), 200
