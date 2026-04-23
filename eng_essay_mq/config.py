#!/usr/bin/python3
# -*- coding:utf-8 -*-
# @Author : dengyu
# @Time   : 2019/07/26

import configparser

def create_config():
    config = configparser.ConfigParser()
    config['server'] = {}
    #config['server']['ocr_url'] = 'http://xxx:xx/get_ocr_result'
    #config['server']['post_url'] = 'http://xxx:xx/process_ppocr'
    config['server']['language_url'] = 'http://192.168.1.111:5050/languagetool_post'
    config['server']['aes_url'] = 'http://192.168.1.111:5051/AES_post'
    config['server']['gec_url'] = 'http://192.168.1.111:5052/grammar_post'
    with open('./config.ini', 'w') as configfile:
        config.write(configfile)
    print('config')

create_config()
