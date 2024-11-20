import mysql.connector
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# 创建数据库连接
def create_db_connection(DB_USER, DB_PASSWORD, DB_NAME, DB_HOST):
    try:
        conn = mysql.connector.connect(
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            database=DB_NAME,
            charset='utf8mb4'  # 指定字符集，支持多种语言字符
        )
        logger.info("数据库连接正常。")
        return conn
    except mysql.connector.Error as err:
        logger.error(f"数据库连接错误: {err}")
        return None


# 创建数据库和表
def create_database_and_tables(conn, DB_NAME):
    if conn is None:
        logger.error("数据库连接失败，无法创建数据库和表。")
        return False

    cursor = conn.cursor()
    try:
        # 创建数据库
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        logger.info(f"数据库 {DB_NAME} 确保存在")

        # 使用数据库
        cursor.execute(f"USE {DB_NAME}")

        # 创建 FOFA 查询历史记录表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS fofa_search_history (
                id INT AUTO_INCREMENT PRIMARY KEY,
                source VARCHAR(50),
                query TEXT,
                host VARCHAR(255),
                path VARCHAR(255),
                title VARCHAR(100),
                ip VARCHAR(45),
                domain VARCHAR(100),
                port INT,
                protocol VARCHAR(50),
                jarm VARCHAR(100),
                page_type VARCHAR(100),
                os VARCHAR(100),
                components TEXT,
                org VARCHAR(100),
                as_organization VARCHAR(100),
                unit VARCHAR(100),
                icp VARCHAR(255),
                country_name VARCHAR(100),
                region VARCHAR(100),
                city VARCHAR(100),
                nature VARCHAR(100),
                isp VARCHAR(100),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE KEY unique_ip_port_title (ip(45), port, title(100))
            ) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
        """)
        logger.info("FOFA 查询历史记录表已创建或已存在。")

        # 创建 Quake 查询历史记录表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS quake_search_history (
                id INT AUTO_INCREMENT PRIMARY KEY,
                source VARCHAR(50),
                query TEXT,
                host VARCHAR(255),
                path VARCHAR(255),
                title VARCHAR(100),
                ip VARCHAR(45),
                domain VARCHAR(100),
                port INT,
                protocol VARCHAR(50),
                jarm VARCHAR(100),
                page_type VARCHAR(100),
                os VARCHAR(100),
                components TEXT,
                org VARCHAR(100),
                as_organization VARCHAR(100),
                unit VARCHAR(100),
                icp VARCHAR(255),
                country_name VARCHAR(100),
                region VARCHAR(100),
                city VARCHAR(100),
                nature VARCHAR(100),
                isp VARCHAR(100),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE KEY unique_ip_port_title (ip(45), port, title(100))
            ) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
        """)
        logger.info("Quake 查询历史记录表已创建或已存在。")

        # 创建 FOFA 临时查询结果表（结构与 FOFA 查询历史记录表相同）
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS fofa_temp_results (
                id INT AUTO_INCREMENT PRIMARY KEY,
                source VARCHAR(50),
                query TEXT,
                host VARCHAR(255),
                path VARCHAR(255),
                title VARCHAR(100),
                ip VARCHAR(45),
                domain VARCHAR(100),
                port INT,
                protocol VARCHAR(50),
                jarm VARCHAR(100),
                page_type VARCHAR(100),
                os VARCHAR(100),
                components TEXT,
                org VARCHAR(100),
                as_organization VARCHAR(100),
                unit VARCHAR(100),
                icp VARCHAR(255),
                country_name VARCHAR(100),
                region VARCHAR(100),
                city VARCHAR(100),
                nature VARCHAR(100),
                isp VARCHAR(100),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            ) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
        """)
        logger.info("FOFA 临时查询结果表已创建或已存在。")

        # 创建 Quake 临时查询结果表（结构与 Quake 查询历史记录表相同）
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS quake_temp_results (
                id INT AUTO_INCREMENT PRIMARY KEY,
                source VARCHAR(50),
                query TEXT,
                host VARCHAR(255),
                path VARCHAR(255),
                title VARCHAR(100),
                ip VARCHAR(45),
                domain VARCHAR(100),
                port INT,
                protocol VARCHAR(50),
                jarm VARCHAR(100),
                page_type VARCHAR(100),
                os VARCHAR(100),
                components TEXT,
                org VARCHAR(100),
                as_organization VARCHAR(100),
                unit VARCHAR(100),
                icp VARCHAR(255),
                country_name VARCHAR(100),
                region VARCHAR(100),
                city VARCHAR(100),
                nature VARCHAR(100),
                isp VARCHAR(100),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            ) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
        """)
        logger.info("Quake 临时查询结果表已创建或已存在。")

        # 创建新的数据面板数据表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS data_panel_history (
                id INT AUTO_INCREMENT PRIMARY KEY,
                ip VARCHAR(45),
                port INT,
                protocols TEXT,
                domains TEXT,
                hosts TEXT,
                titles TEXT,
                components TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            ) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
        """)
        logger.info("数据面板历史记录表已创建或已存在。")

        conn.commit()  # 提交更改
    except mysql.connector.Error as err:
        logger.error(f"数据库操作错误: {err}")
        return False
    finally:
        cursor.close()


def save_search_history(conn, table_name, query, results, source):
    if not results:
        logger.warning("没有要保存的搜索结果。")
        return

    with conn.cursor() as cursor:
        try:
            # 收集待插入的记录和已经存在的记录
            records_to_insert = []
            existing_records = set()  # 用于存储已存在的记录

            # 先查询数据库中已存在的记录
            cursor.execute(f"SELECT ip, port, title FROM {table_name}")
            rows = cursor.fetchall()
            existing_records.update((row[0], row[1], row[2]) for row in rows)

            # 计算已存在的记录数
            existing_count = len(existing_records)
            logger.info(f"数据库中已存在的记录数量: {existing_count}")

            # 准备插入的记录
            for result in results:
                ip = result.get('ip')
                port = result.get('port')
                title = result.get('title')

                # 检查是否已经存在于数据库中
                record_key = (ip, port, title)

                if record_key not in existing_records:
                    records_to_insert.append((
                        source,
                        query,
                        result.get('host'),
                        result.get('path'),
                        title,
                        ip,
                        result.get('domain'),
                        port,
                        result.get('protocol'),
                        result.get('jarm'),
                        result.get('page_type'),
                        result.get('os'),
                        result.get('components'),
                        result.get('org'),
                        result.get('as_organization'),
                        result.get('unit'),  # 添加归属单位
                        result.get('icp'),
                        result.get('country_name'),
                        result.get('region'),
                        result.get('city'),
                        result.get('nature'),
                        result.get('isp')
                    ))

            # 计算要插入的记录数
            to_insert_count = len(records_to_insert)
            logger.info(f"待插入的记录数量: {to_insert_count}")

            # 批量插入记录，如果有新记录
            if records_to_insert:
                insert_sql = f"""
                    INSERT INTO {table_name} 
                    (source, query, host, path, title, ip, domain, port, protocol, jarm, 
                    page_type, os, components, org, as_organization, unit, icp, country_name, region, city, 
                    nature, isp, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())  
                    ON DUPLICATE KEY UPDATE 
                    query = VALUES(query),  
                    host = VALUES(host),
                    path = VALUES(path),
                    title = VALUES(title),
                    domain = VALUES(domain),
                    port = VALUES(port),
                    protocol = VALUES(protocol),
                    jarm = VALUES(jarm),
                    page_type = VALUES(page_type),
                    os = VALUES(os),
                    components = VALUES(components),
                    org = VALUES(org),
                    as_organization = VALUES(as_organization),
                    unit = VALUES(unit),
                    icp = VALUES(icp),
                    country_name = VALUES(country_name),
                    region = VALUES(region),
                    city = VALUES(city),
                    nature = VALUES(nature),
                    isp = VALUES(isp)
                """
                cursor.executemany(insert_sql, records_to_insert)

                # 检查实际插入的记录数
                inserted_count = cursor.rowcount
                logger.info(f"两个数据表中共有 {inserted_count} 条数据")

            # 输出已存在记录和待插入记录的统计
            logger.info(f"跳过的重复记录数量: {existing_count - (existing_count + to_insert_count - inserted_count)}")

            # 检查记录总数，超过10000条则删除最旧的记录
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            total_records = cursor.fetchone()[0]

            if total_records > 10000:
                limit_to_keep = 10000
                # 只保留最新的10000条记录
                cursor.execute(f"""
                    DELETE FROM {table_name}
                    ORDER BY created_at 
                    LIMIT {total_records - limit_to_keep}
                """)
                logger.info(f"超过10000条记录，已删除最旧的记录，当前记录数: {limit_to_keep}")

            conn.commit()  # 提交更改

        except mysql.connector.Error as err:
            logger.error(f"插入历史记录时发生错误: {err}")
            conn.rollback()  # 回滚事务
        except Exception as e:
            logger.error(f"发生了意外错误: {e}")
            conn.rollback()  # 回滚事务


def save_temp_results(conn, table_name, query, results, source):
    if not results:
        logger.warning("没有要保存的临时搜索结果。")
        return

    with conn.cursor() as cursor:
        try:
            # 清空临时表
            cursor.execute(f"TRUNCATE TABLE {table_name}")
            conn.commit()

            # 保存查询结果到临时表
            insert_sql = f"""
                INSERT INTO {table_name} 
                (source, query, host, path, title, ip, domain, port, protocol, jarm, 
                page_type, os, components, org, as_organization, unit, icp, 
                country_name, region, city, nature, isp)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """

            # 批量插入记录
            cursor.executemany(insert_sql, [
                (source, query, result.get('host'), result.get('path'), result.get('title'),
                 result.get('ip'), result.get('domain'), result.get('port'), result.get('protocol'),
                 result.get('jarm'), result.get('page_type'), result.get('os'),
                 result.get('components'), result.get('org'), result.get('as_organization'),
                 result.get('unit'), result.get('icp'), result.get('country_name'),
                 result.get('region'), result.get('city'), result.get('nature'), result.get('isp'))
                for result in results
            ])
            conn.commit()
            logger.info(f"成功保存查询结果到 {table_name}。")
        except mysql.connector.Error as err:
            logger.error(f"插入临时结果时发生错误: {err}")
            conn.rollback()  # 回滚事务
        except Exception as e:
            logger.error(f"发生了意外错误: {e}")
            conn.rollback()  # 回滚事务
