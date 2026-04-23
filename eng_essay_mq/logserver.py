# -*- coding: utf-8 -*-

# Copyright (c) 2019-present, AI
# All rights reserved.
# @Time 2020/3/18
# @Author: JW Junjie_DC@foxmail.com

import uuid
import os
import requests
import json
import time
import logging
import logging.handlers

class LogServer:
    def __init__(self, app='au-service', log_path='./log/', log_post_api=''):
        self.uuid = ''
        self.local_log_path = log_path
        self.log_post_api = log_post_api
        self.local_logfile = ''
        self.logger = ''
        self.hostname = ''
        self.app = app
        self.examid = ''
        self.configure_logging()
        self.generate_uuid()
        self.pid_monitor_file = ''
    def set_log_post_api(self, log_post_api):
        self.log_post_api = log_post_api
    def generate_uuid(self):
        self.uuid = str(uuid.uuid1())
    def get_hostname(self):
        hostname = ''
        with open('/etc/hostname', 'r') as f:
            lines = f.readlines()
            if len(lines) > 0:
                hostname = lines[0].strip('\n')
        f.close()
        self.hostname = hostname
        return hostname
    # save current pid to file for monitor purpose
    def save_pid_to_file(self):
        pid = str(os.getpid())
        self.pid_monitor_file = os.path.join(self.local_log_path, self.get_hostname() + '.pid')
        with open(self.pid_monitor_file, 'w') as f:
            f.write(pid)
        f.close()
    # check if the special process is running
    def is_process_running(self):
        self.pid_monitor_file = os.path.join(self.local_log_path, self.get_hostname() + '.pid')
        pid = -1
        with open(self.pid_monitor_file, 'r') as f:
            pid = f.readline()
            print('pid : ', pid)
        f.close()
        pid = int(pid)
        return self.pid_exists(pid)
    def pid_exists(self, pid):
        if pid < 0:
            return False
        try:
            os.kill(pid, 0)
       # except ProcessLookupError:
       #     return False
       # except PermissionError:
       #     return True
        except:
            return True
    def generate_local_logfile(self, common_file_name='log.txt'):
        hostname = self.get_hostname()
        file_name = hostname + '-' + common_file_name
        self.local_logfile = os.path.join(self.local_log_path, file_name)
        # self.local_logfile = os.path.join(self.local_log_path, common_file_name)
    def get_timestamp(self):
        now = int(time.time())
        time_struct = time.localtime(now)
        str_time = time.strftime("%Y-%m-%d %H:%M:%S", time_struct)
        return str_time
    def configure_logging(self):
        self.generate_local_logfile()
        if not os.path.exists(os.path.dirname(self.local_logfile)):
            os.mkdir(os.path.dirname(self.local_logfile))
        import logging.handlers
        logger = logging.getLogger()
        logger.setLevel(logging.INFO)
        file_handler = logging.handlers.RotatingFileHandler(self.local_logfile, 'a', 20480000, 7,encoding="utf-8")
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        self.logger = logger

    def re_configure_logging(self, new_file_name):
        self.generate_local_logfile(new_file_name)
        if not os.path.exists(os.path.dirname(self.local_logfile)):
            os.mkdir(os.path.dirname(self.local_logfile))
        import logging.handlers
        logger = logging.getLogger()
        logger.setLevel(logging.INFO)
        file_handler = logging.handlers.RotatingFileHandler(self.local_logfile, 'a', 20480000, 7 ,encoding="utf-8")
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        self.logger = logger


    def get_contener_id(self):
        cmd = "cat /proc/self/cgroup"
        output = os.popen(cmd)
        rests = output.readlines()
        container_message = rests[-1]
        if not container_message:
            container_id = "no_found"
        else:
            if container_message.find("docker-") != -1:
                container_id = container_message.strip().split("docker-")[-1][:12]
            else:
                container_id = container_message.strip().split("docker/")[-1][:12]
        print("container_id is:", container_id)
        return container_id
    # local logging
    def logging(self, log_info):
        self.logger.info('[%s] [%s] %s' % (self.uuid, self.examid, log_info))
        # 支持输出中文内容
        #self.logger.info(u'[%s] [%s] %s' % (self.uuid, self.examid, log_info))
        # self.logger.info('[%s] [%s] %s' % (self.uuid, self.examid, log_info.encode('utf-8')))
        
    def generate_post_message(self, log_lever, msg):
        '''
        :param logLever: ERROR/INFO/WARN/DEBUG
        :param msg:
        :return:
        '''
        post_message = {'app': self.app, "logLevel": log_lever, "msg": msg, 'errorStack': '', "trace": self.uuid}
        return json.dumps(post_message)
    def is_id_changed(self, examid):
        changed = examid != self.examid
        if changed:
            self.examid = examid
        return changed
    def set_examid(self, examid):
        self.examid = examid
    # post log message to log server
    def post_log(self, log_info, examid='', log_lever='INFO'):
        return
        # timestamp = self.get_timestamp()
        # msg = {'hostname': self.get_hostname(), 'examid': examid, 'time': timestamp, 'info': log_info}
        # str_msg = json.dumps(msg)
        # post_message = self.generate_post_message(log_lever, str_msg)
        # headers = {'Content-Type': 'application/json'}
        # try:
        #     response = requests.post(self.log_post_api, headers=headers, data=post_message)
        # except requests.exceptions.ConnectionError:
        #     response = 'ConnectionError'
        #     self.logging('ConnectionError')
        # return response