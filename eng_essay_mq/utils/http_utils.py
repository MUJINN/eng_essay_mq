import requests

def get_request(url, headers=None, params=None):
    """
    发送 GET 请求

    参数:
    - url (str): 请求的 URL
    - headers (dict, optional): 请求头
    - params (dict, optional): URL 参数

    返回:
    - response: requests.Response 对象
    """
    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()  # 检查 HTTP 错误
        return response
    except requests.exceptions.RequestException as e:
        #print("GET 请求错误: {}".format(e))
        return None

def post_request(url, headers=None, data=None, json=None):
    """
    发送 POST 请求

    参数:
    - url (str): 请求的 URL
    - headers (dict, optional): 请求头
    - data (dict, optional): 表单数据
    - json (dict, optional): JSON 数据

    返回:
    - response: requests.Response 对象
    """
    try:
        response = requests.post(url, headers=headers, data=data, json=json)
        response.raise_for_status()  # 检查 HTTP 错误
        return response
    except requests.exceptions.RequestException as e:
        #print("POST 请求错误: {}".format(e))
        return None