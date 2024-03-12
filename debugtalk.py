import logging
import time
from typing import List
import mysql.connector
import os
from loguru import logger
import jmespath

from httprunner import __version__


def get_httprunner_version():
    return __version__

def get_table_sufix(user_id):
    return int(user_id)%20

def get_service_host(service_name, envflag="normal", eurake_url="http://internal-tf-salone-qa-eureka-alb-1821712182.ap-northeast-1.elb.amazonaws.com:8761/eureka/"):
    logger.info(f"august get_service_host {service_name} {eurake_url}")
    import py_eureka_client.eureka_basic as eureka
    import asyncio
    application = asyncio.run(eureka.get_application(eurake_url,service_name))
    # 这里还需要判断，返回想要的实例
    res = ""
    for instance in application.instances:
        logger.info(f"august get_service_host {instance.instanceId} ")
        if instance.status != "UP":
            continue
        if instance.metadata and instance.metadata.get("envflag") == envflag:
            return "http://" + instance.instanceId
        else:
            res = "http://" + instance.instanceId
    if res != "":
        return res
    else:
        raise Exception(f"Can't find service {service_name} with envflag {envflag} in eureka")


def compare_response(response, expected, message="reponse != expected"):
    # 递归比较两个字典, 只比较expected中的key
    for key, value in expected.items():
        if isinstance(value, dict):
            compare_response(value, response[key])
        else:
            assert expected[key] == response[key], message

def get_value_from_map(payload, key):
    logger.info(f"august get_value_from_map {payload} {key}")
    return payload[key]

def calculate(expression, *args):
    exp = expression.format(*args)
    logger.info(f"august calculate {eval(exp)}")
    return eval(exp)
"""DB操作
"""
def run_sql_return_single_value(sql_info, convertToFloat=False,db_name="sa_qa_common"):
    res = []
    results = connect_db_and_execute(**sql_info, db_name=db_name)
    columns = sql_info["columns"]
    logger.info(f"run_sql_return_single_value results: {results[0].get(columns[0])}")
    if convertToFloat:
        return float(results[0].get(columns[0]))
    return results[0].get(columns[0])

def run_sql_return_list(sql_info, db_name="sa_qa_common"):
    res = []
    results = connect_db_and_execute(**sql_info, db_name=db_name)
    columns = sql_info["columns"]
    for result in results:
        if len(columns) == 1:
            res.append(result.get(columns[0]))
        else:
            res.append([result.get(column) for column in columns])
    logger.info(f"run_sql_return_list return: {res}")
    return res

def run_sql_update(sql_info, db_name="sa_qa_common"):
    logger.info(f"run_sql_update: {sql_info}")
    results = connect_db_and_execute(**sql_info, db_name=db_name, need_result=False)
    logger.info(f"run_sql_update affect: {results}")
    return


def connect_db_and_execute(db_name: str, sql: str, database: str = '', **kargs):
    db_info = {}
    # import configparser
    # config = configparser.ConfigParser()
    # config.read('.env')
    if db_name in ['sa_qa_common', 'sa_qa_next']:
        db_info['host'] = os.getenv(f"{db_name}_url")
        db_info['user'] = os.getenv(f"{db_name}_username")
        db_info['password'] = os.getenv(f"{db_name}_password")
    else:
        raise "db info error"
    logger.info(f"august connect_db_and_execute: {db_info}")
    if database != '':
        db_info['database'] = database

    cnx = mysql.connector.connect(**db_info)
    cnx.autocommit = True
    cursor = cnx.cursor(dictionary=True)
    query = (sql)
    cursor.execute(query)
    res = None
    if "need_result" in kargs and kargs["need_result"] == False:
        # 获取更新操作影响的行数
        res = cursor.rowcount
    else:
        res = cursor.fetchall()
    # 关闭游标和连接
    cursor.close()
    cnx.close()  
    return res


"""中间件
"""


"""自定义验证器
"""  
def check_status_code(check_value, expected_value, message):
    logger.info(f"august check_status_code {check_value} {expected_value}")
    check_value = [float(x) for x in check_value]
    assert check_value == expected_value, message

def check_value(response, jmes_path, value, message=""):
    res = jmespath.search(jmes_path, response)
    logger.info(f"august check_value: {res} {value}")
    if message == "":
        message = f"expect {value}, but got {res}"
    assert res == value, message

def check_value_dics(response, jmes_path_res, value, jmes_path_value):
    print(f"august teardown: {response} {jmes_path_res} {value} {jmes_path_value}")
    response_res = jmespath.search(jmes_path_value, response)
    value_res = jmespath.search(jmes_path_res, value)

    assert response_res == value_res, f"expect {value_res}, but got {response_res}"


"""open api tools
"""
def get_tran_id():
    import random
    return str(int(time.time()*1000)) + str(random.randint(1000, 9999))

def generate_open_api_url(params, secret):
    import hashlib
    import hmac
    params = generate_open_api_params(params)
    param_str = ''
    for key in params.keys():
        param_str += f"&{key}={params[key]}"
    param_str = param_str[1:]
    # sign = hashlib.sha256(param_str.encode('utf-8')).hexdigest()
    signature = hmac.new(secret.encode('utf-8'), param_str.encode('utf-8'), digestmod=hashlib.sha256).hexdigest()

    param_str = param_str + "&signature=" + signature
    params["signature"] = signature
    return param_str, params

def generate_open_api_params(params):
    if "timestamp" not in params:
        params["timestamp"] = int(time.time()*1000)
    
    return params

def open_api_setup_hooks(request, params, secret):
    param_str, params = generate_open_api_url(params, secret)
    # request["url"] = request["url"] + "?" + param_str
    request["params"] = params
    return request

def setup_sleep_n_second(n):
    time.sleep(n)

def printmgs(mgs):
    print(f"august teardown: {mgs}")


# commented out function will be filtered
# def get_headers():
#     return {"User-Agent": "hrp"}


def get_user_agent():
    return "hrp/funppy"


def sleep(n_secs):
    time.sleep(n_secs)


def sum(*args):
    result = 0
    for arg in args:
        result += arg
    return result


def sum_ints(*args: List[int]) -> int:
    result = 0
    for arg in args:
        result += arg
    return result


def sum_two_int(a: int, b: int) -> int:
    return a + b


def sum_two_string(a: str, b: str) -> str:
    return a + b


def sum_strings(*args: List[str]) -> str:
    result = ""
    for arg in args:
        result += arg
    return result


def concatenate(*args: List[str]) -> str:
    result = ""
    for arg in args:
        result += str(arg)
    return result


def setup_hook_example(name):
    logging.warning("setup_hook_example")
    return f"setup_hook_example: {name}"


def teardown_hook_example(name):
    logging.warning("teardown_hook_example")
    assert 1 == 2
    return f"teardown_hook_example: {name}"
