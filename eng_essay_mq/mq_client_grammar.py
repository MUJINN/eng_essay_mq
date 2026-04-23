#!/usr/bin/python3
# -*- coding:utf-8 -*-
# @Author : dengyu
# @Time   : 2019/07/26
# modified : 18/3/2020  JW

from flask import Flask, jsonify, request, make_response, abort
import pika
import re, sys, os
import requests
import json
# import logging
import functools
import time
import threading
from pika.exceptions import AMQPChannelError
from pika.exceptions import AMQPConnectionError
from instance_log_server import log_server

from english_write import EssayCorrection


def load_json(config_file):
    with open(config_file) as load_f:
        return json.load(load_f)
    return None


def read_configuration():
    configure_file = './grammar_mq_config.cfg'
    config_data = load_json(configure_file)
    # print(config_data)
    if not config_data:
        log_server.logging('load config file failed.')

    # task status
    env = config_data['envs'][0]
    mq_url_parameter = config_data[env]['mq_url_parameter']
    mq_queue = config_data[env]['mq_queue']
    post_api = config_data[env]['post_api']
    correct_essay_api = config_data[env]['correct_essay_api']
    log_server.logging("env: {}, mq_url_parameter: {}, mq_queue: {}".format(env, mq_url_parameter, mq_queue))
    return mq_url_parameter, mq_queue, post_api, correct_essay_api


def check_all_keys_exist(checked_key, origin_data):
    """
    Check if the dictionary from the front end is missing 'key'
    :param checked_keys:
    :param dict_data:
    :return:
    """
    for key in checked_key:
        if key not in origin_data:
            return False
    return True


def run_essay_correction(mq_data):
    """
    essay correction
    :param mq_data:
    :return: statue, result
    """
    try:
        
        log_server.logging('>>> come run_essay_correction')
        correction_time_begin = time.time()
        if len(mq_data) != 0:
            if isinstance(mq_data, bytes):
                mq_data = mq_data.decode()
            json_data = json.loads(mq_data)
        else:
            return False, None

        log_server.logging('receive mq_data:{}'.format(json.dumps(json_data, ensure_ascii=False)))
        # global essayCorrection
        essayCorrection = EssayCorrection(log_server)
        totalScore = None
        # ec = EssayCorrection()  # 每次都重新创建？？、
        ec = essayCorrection
        if 'subjectId' in json_data:
            subjectId  = json_data.get('subjectId')
        if 'blockId' in json_data:
            blockId    = json_data.get('blockId')
        if 'taskKey' in json_data:
            taskKey    = json_data.get('taskKey')
        if 'grade' in json_data:
            grade      = json_data.get('grade')
        if 'totalScore' in json_data:
            totalScore = json_data.get('totalScore') # exam total score
        if 'students' in json_data:
            students   = json_data.get('students')   # students is list
        else:
            students = []
        if 'model' in json_data:                     # 使用的模型
            model      = json_data.get('model')
        else:
            model = 'dianxin'
        if 'task' in json_data:                      # 批改任务，en 表示英文作文批改, cn 表示中文作文批改
            task       = json_data.get('task')
        else:
            task = 'en-app'
        if 'problem' in json_data:                   # 作文题目，只有英文作文批改且使用电信的模型时才会用上
            problem    = json_data.get('problem')
        else:
            problem = ''

        if 'key' in json_data:
            key = json_data.get('key', '')

        log_server.logging('receive mq_data: task : {}, model {}, subjectID : {}, blockId : {}.'.format(task, model, subjectId, blockId))

        # Judge totalScore is valid
        if totalScore == None or totalScore <= 0 or totalScore > 100:
            totalScore = 0
            correction_res = ec.parser_one_essay(subjectId, blockId, taskKey, grade, totalScore, students, model=model, task=task, problem=problem)
        else:
            correction_res = ec.parser_one_essay(subjectId, blockId, taskKey, grade, totalScore, students, model=model, task=task, problem=problem)

        # print('correction_res : ', correction_res)

        # 原路返回
        if 'key' in json_data:
            correction_res['key'] = key

        result_json = json.dumps(correction_res, ensure_ascii=False)

        total_time = time.time() - correction_time_begin
        # msg = {"mq_data":mq_data, "result":correction_res, "time":total_time}
        msg = {"result":correction_res, "time":total_time}
        log_server.logging(json.dumps(msg, ensure_ascii=False))
        log_server.logging('exit run_essay_correction function >>>')
        return True, result_json
    except Exception as e:
        log_server.logging('Exception :{}'.format(e))
        # error_info = {'code': 0, 'message': 'fail', "data": "Exception"}
        return False, None


def callback(ch, method, properties, body):
    '''
    callback function , handle messages taken from rabbitmq
    :param ch: channel object
    :param method: get the attached parameter value of the queue data, example: route_key
    :param properties:
    :param body: queue data value
    :return:
    '''

    log_server.logging('enter callback')
    try:
        success, result_json = run_essay_correction(body)

        if success:
            header = {'Content-Type': 'application/json'}
            log_server.logging('begin to post response')
            
            response = requests.post(post_api, headers=header, data=result_json.encode('utf-8'))
            log_server.logging('end to post response')
            log_server.logging('post response: {}'.format(response.status_code))
        else:
            log_server.logging('[ERROR] in run_essay_correction')
        
        log_server.logging('exit mq callback')
    except requests.exceptions.Timeout as e:
        log_server.logging("[ERROR] timeout: " + str(e))
        # 移除这里的 basic_ack
    except requests.exceptions.SSLError as e:
        log_server.logging("[ERROR] SSL: " + str(e))
        # 移除这里的 basic_ack
    except requests.exceptions.RequestException as e:
        log_server.logging("[ERROR] request: " + str(e))
        # 移除这里的 basic_ack
    except Exception as e:
        log_server.logging("[ERROR] unknown error: " + str(e))
        # 移除这里的 basic_ack


def ack_message(channel, delivery_tag):
    """Note that `channel` must be the same pika channel instance via which
    the message being ACKed was retrieved (AMQP protocol constraint).
    """
    if channel.is_open:
        channel.basic_ack(delivery_tag)


def do_work(connection, channel, method_frame, header_frame, body):
    thread_id = threading.get_ident()
    delivery_tag = method_frame.delivery_tag
    fmt1 = "[START] Thread id: {} Delivery tag: {}"
    log_server.logging(fmt1.format(thread_id, delivery_tag))

    # 立即确认消息，避免超时
    cb = functools.partial(ack_message, channel, delivery_tag)
    connection.add_callback_threadsafe(cb)
    log_server.logging("Message acknowledged immediately")

    try:
        # 处理消息
        callback(channel, method_frame, header_frame, body)
        log_server.logging("Message processed successfully")
    except Exception as e:
        log_server.logging("Error processing message: {}".format(e))



def on_message(channel, method_frame, header_frame, body, args):
    (connection, threads, post_api) = args
    t = threading.Thread(target=do_work, args=(connection, channel, method_frame, header_frame, body))
    t.start()
    threads.append(t)

def consumer(tag_value):
    print("mq_info: ", mq_url_parameter)
    print("mq_queue: ", mq_queue)

    while True:
        try:
            parameters = pika.URLParameters(mq_url_parameter)
            parameters.heartbeat = 60  # 每60秒发送一次心跳
            parameters.connection_attempts = 5
            parameters.retry_delay = 5  # seconds
            parameters.blocked_connection_timeout = 3600  # 1小时超时
            parameters.socket_timeout = 10  # socket超时10秒
            connection = pika.BlockingConnection(parameters)
            # create channel
            channel = connection.channel()
            channel.queue_declare(queue=mq_queue, durable=True)
            channel.basic_qos(prefetch_count=1)

            on_message_callback = functools.partial(on_message, args=(connection, threads, post_api))
            channel.basic_consume(
                    consumer_callback=on_message_callback,
                    queue=mq_queue,
                    no_ack=False,
                    consumer_tag=tag_value
                )

            channel.start_consuming()

            for thread in threads:
                thread.join()
        except pika.exceptions.AMQPChannelError:
            break
        except pika.exceptions.AMQPConnectionError:
            continue

if __name__ == '__main__':
    #app.run(host='192.168.1.111', port=5053)
    argv_len = len(sys.argv)
    tagName = sys.argv[1]
    # print("tag_name:{}".format(tagName))
    log_server.re_configure_logging(str(tagName) + "_log.txt")
    mq_url_parameter, mq_queue, post_api, correct_essay_api = read_configuration()
    # global essayCorrection # main函数中这个什么是多余的
    # essayCorrection = EssayCorrection(log_server)
    threads = []
    consumer(tag_value=str(tagName))
