import logging
import requests
from urllib.parse import urlparse

# 配置日志
logger = logging.getLogger(__name__)


def quake_search(QUAKE_TOKEN, query, size):
    try:
        headers = {
            "X-QuakeToken": QUAKE_TOKEN,
            "Content-Type": "application/json"
        }

        data = {
            "query": query,
            "start": 0,
            "size": size,
            "ignore_cache": False
        }

        response = requests.post(url="https://quake.360.net/api/v3/search/quake_service", headers=headers, json=data)

        if response.status_code == 200:
            results = response.json()
            # print(results)  # api 调用调试
            return process_quake_results(results), None
        else:
            logger.error(f"Quake请求失败: {response.status_code}, {response.text}")
            return [], f"请求失败: {response.status_code}"
    except Exception as e:
        logger.error(f"Quake搜索异常: {str(e)}")
        return [], str(e)


def process_quake_results(data):
    quake_results = []  # 初始化结果列表
    if "data" in data:  # 检查数据中是否包含 "data" 字段
        for item in data["data"]:  # 遍历每个数据项
            http_service = item.get('service', {}).get('http', {})  # 获取 HTTP 服务信息
            load_url = http_service.get('http_load_url', [""])[0] if http_service.get(
                'http_load_url') else ""  # 获取加载 URL

            # 解析 URL，若 load_url 为空则使用 IP:端口作为 host
            if load_url:
                parsed_url = urlparse(load_url)  # 解析 URL
                if parsed_url.scheme and parsed_url.hostname:
                    base_url = f"{parsed_url.scheme}://{parsed_url.hostname}"
                else:
                    # 如果没有 scheme，假设是主机名，需要加 http://
                    base_url = f"http://{load_url}" if load_url else ""
            else:
                # 如果 load_url 为空，使用 IP 和端口构建 host
                ip = item.get('ip', "").strip()  # 获取 IP 并去除首尾空格
                port = str(item.get('port', "")).strip()  # 获取端口并去除首尾空格
                base_url = ""

                # 构建有效的 base_url
                if ip:
                    base_url += ip  # 添加 IP
                if port:
                    base_url += f":{port}"  # 如果有端口，添加端口

            # 获取端口
            port = str(item.get('port', ""))
            if port and load_url:  # 如果 load_url 不为空，则可以展示 port
                base_url += f":{port}"

            # 提取产品信息
            components = item.get('components', [])  # 获取组件信息
            product_info = []
            for component in components:
                product_name = component.get('product_name_cn', "").replace('\n', '')  # 去除换行符
                product_vendor = component.get('product_vendor', "").replace('\n', '')  # 去除换行符
                # 合并产品名称和供应商
                if product_name and product_vendor:
                    product_info.append(f"{product_name} ({product_vendor})")
                elif product_name:
                    product_info.append(product_name)
                elif product_vendor:
                    product_info.append(product_vendor)

            # 将产品信息合并为一行
            product_info_str = ', '.join(product_info) if product_info else "无产品信息"

            # 构建记录字典，提取关键信息
            record = {
                "ip": item.get('ip', "").replace('\n', ''),  # IP 地址
                "port": port,  # 端口
                "protocol": item.get('service', {}).get('name', "").replace('\n', ''),  # 协议名称
                "country_name": item.get('location', {}).get('country_cn', "").replace('\n', ''),  # 国家名称
                "region": item.get('location', {}).get('province_cn', "").replace('\n', ''),  # 省份
                "city": item.get('location', {}).get('city_cn', "").replace('\n', ''),  # 城市
                "org": item.get('org', "").replace('\n', ''),  # 组织
                "host": base_url.replace('\n', ''),  # 使用解析后的 URL 或 IP:端口
                "domain": item.get('domain', "").replace('\n', ''),  # 域名
                "os": item.get('os_name', "").replace('\n', ''),  # 操作系统名称
                "server": http_service.get('server', "").replace('\n', ''),  # 服务器信息
                "icp": http_service.get('icp', {}).get('main_licence', {}).get('licence', "").replace('\n', ''),
                # ICP 备案信息
                "title": http_service.get('title', '').replace('\n', ''),  # 页面标题
                "jarm": item.get('service', {}).get('tls-jarm', {}).get('jarm_hash', "").replace('\n', ''),  # JARM 哈希
                "unit": http_service.get('icp', {}).get('main_licence', {}).get('unit', "").replace('\n', ''),  # 单位名称
                "from": "quake",  # 数据来源标识
                "page_type": http_service.get('page_type', [""])[0].replace('\n',
                                                                            '') if 'page_type' in http_service and http_service.get(
                    'page_type') else "",  # 页面类型
                "path": http_service.get('path', "").replace('\n', ''),  # 路径
                "nature": http_service.get('icp', {}).get('main_licence', {}).get('nature', "").replace('\n', ''),
                # 企业性质
                "isp": item.get('location', {}).get('isp', "").replace('\n', ''),  # 互联网服务提供商
                "scene": item.get('location', {}).get('scene_cn', "").replace('\n', ''),  # 场景
                "components": product_info_str  # 产品信息合并为一行
            }
            quake_results.append(record)  # 将记录添加到结果列表
            # print(record)
    return quake_results  # 返回处理后的结果列表
