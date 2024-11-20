import base64
import logging
import requests

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
            'as_organization': r[6] if len(r) > 6 else "",  # None 替换为空字符串
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
