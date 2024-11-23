import base64
import logging
import requests
from flask import render_template, redirect, request
from src.sqlquery.database_manager import create_db_connection, save_temp_results, save_search_history

# 配置日志
logger = logging.getLogger(__name__)


def fofa_search(FOFA_EMAIL, FOFA_KEY, query, size):
    try:
        params = {
            'email': FOFA_EMAIL,
            'key': FOFA_KEY,
            'qbase64': base64.b64encode(query.encode()).decode(),
            'fields': 'ip,port,protocol,country_name,region,city,as_organization,host,domain,os,server,icp,title,jarm',
            'size': size,
        }

        response = requests.get('https://fofa.info/api/v1/search/all', params=params, verify=False)

        if response.status_code != 200:
            logger.error(f"FOFA请求失败: {response.status_code}")
            return [], f"Error: Received status code {response.status_code}"

        data = response.json()
        if data.get('error'):
            logger.error(f"FOFA错误信息: {data.get('errmsg')}")
            return [], f"Error: {data.get('errmsg')}"

        results = [{
            'ip': r[0],
            'port': r[1],
            'protocol': r[2],
            'country_name': r[3],
            'region': r[4],
            'city': r[5],
            'as_organization': r[6] if len(r) > 6 else "",
            'host': r[7] if len(r) > 7 else "",
            'domain': r[8] if len(r) > 8 else "",
            'os': r[9] if len(r) > 9 else "",
            'server': r[10] if len(r) > 10 else "",
            'icp': r[11] if len(r) > 11 else "",
            'title': r[12] if len(r) > 12 else "",
            'jarm': r[13] if len(r) > 13 else ""
        } for r in data['results']]

        return results, None
    except Exception as e:
        logger.error(f"FOFA搜索异常: {str(e)}")
        return [], str(e)


def fofa_search_page(FOFA_EMAIL, FOFA_KEY, DB_USER, DB_PASSWORD, DB_NAME, DB_HOST):
    if not FOFA_EMAIL or not FOFA_KEY:
        return redirect('configure')

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
                        save_temp_results(conn, 'fofa_temp_results', query, results, 'fofa')
                        save_search_history(conn, 'search_history', query, results, 'fofa')
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
