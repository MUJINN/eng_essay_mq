#!/usr/bin/python3
# -*- coding:utf-8 -*-
# @Author : dengyu
# @Time   : 2019/07/26
# modified : 18/3/2020  JW

import os
import re
import time
import json
import requests
import configparser
# import logging
import urllib3
urllib3.disable_warnings()
from merge_rule_process import MergeRuleMethod, CallInterface
from utils.http_utils import post_request
import difflib
import math
from instance_log_server import log_server
from utils.dify_client import correct_chinese_essay_with_dify


content3 = {'post_content':"We want to say goodbye with you at that day. How do we come true this dream? In my school will have this life for students have a good time. You will look many trees both of the street."}


class EssayCorrection:
    def __init__(self, log_server):
        # LN_ self.pprocess = MergeRuleMethod()
        #self.call = CallInterface()
        self.log_server = log_server

        #self.urls = self.__read_config()['server']
        self.error_type = {'ERROR_CONJUNCTION', 'ERROR_SPELLING', 'ERROR_NOUN', 'ERROR_GRAMMAR',
                           'ERROR_VERB', 'COLLOCATIONS', 'GRAMMAR'}
        
        # !!! 需要修改
        #self.language_url = "http://10.12.1.106:9220/languagetool_post"
        #self.aes_url      = "http://10.12.1.106:9212/AES_post"
        #self.gec_url      = "http://10.12.1.106:9230/grammar_post"
        #self.language_url = "http://yj-lt-bdy.haofenshu.com/languagetool_post"    
        self.gec_url      = "http://yj-gec-wan.haofenshu.com/grammar_post"
        self.aes_url      = "http://yj-aes-wan.haofenshu.com/AES_post"
        self.correct_essay_api = "https://yj-llm-wan.yunxiao.com/correct_essay"

    def __read_config(self):
        config = configparser.ConfigParser()
        config.read('./config/config.ini')
        return config

    def read_json(self, json_file):
        with open(json_file, 'r', encoding='utf8') as f:
            infos = json.load(f)
        return infos

    def remove_repeat(self, rule_set):
        repeat = set()
        removed_rule_set = []
        for item in rule_set:
            splice_str = "%s,%s,%s" % (item['offset'], item['length'], item['rule']['category'])
            repeat.add(splice_str)
        rep_list = list(repeat)

        for rep in rep_list:
            rep_split = rep.split(',')
            for rule in rule_set:
                if int(rep_split[0]) == rule['offset'] and int(rep_split[1]) == rule['length'] and  rep_split[2] == rule['rule']['category'] :
                    removed_rule_set.append(rule)
                    break
        return removed_rule_set

    def score_adjustment(self, predict_score, totalScore):
        """ 
        Adjustment score ploy
        :param predict_score:
        :param totalScore:
        :return predict_score:
        """
        if totalScore == 0:
            return predict_score
        elif totalScore <= 10: 
            delta = 1 / totalScore
            predict_score += delta
        elif 10 < totalScore <= 20: 
            delta = 1.5 / totalScore
            predict_score += delta
        elif 20 < totalScore <= 50: 
            delta1 = 2.5 / totalScore
            delta2 = 3.0 / totalScore
            if 0.3 <= predict_score < 0.6:
                predict_score += delta1
            elif 0.6 <= predict_score <= 0.9:
                predict_score += delta2
        elif 50 < totalScore <= 100:
            delta1 = 4.0 / totalScore
            delta2 = 5.0 / totalScore
            #delta3 = 3.0 / totalScore
            if 0.3 <= predict_score < 0.5:
                predict_score += delta1
            elif 0.5 <= predict_score < 0.7:
                predict_score += delta2
            elif 0.7 <= predict_score <= 0.9:
                predict_score *= 1.05

        if predict_score > 1.0:
            predict_score = 1.0 

        return predict_score
    
    def _correct_essay(self, grade, totalScore, content, model='ayx', task='en', problem=None):
        log_server.logging("enter _correct_essay")

        params = {'task': task, 'model': model, 'content': content, "problem": problem, "grade":grade}

        try:
            # log_server.logging("_correct_essay params : " + str(params))
            
            # 调远程的接口来获取作文识别内容，如果返回None，则重试，最多3次
            for i in range(3):
                response = post_request(self.correct_essay_api, json=params)
                if response is not None:
                    break
                else:
                    time.sleep(0.1)
            # response = post_request(self.correct_essay_api, json=params)
            # if response is None:  # 检查响应是否包含预期数据:
            #     return None
            
            # log_server.logging("_correct_essay response text : " + response.text)
            
            response_data = response.json()     
            # log_server.logging("_correct_essay response text : " + str(response_data))  
            correct_result = response_data.get('data', None)
            log_server.logging("exit _correct_essay")
            return correct_result
        except Exception as e:
            log_server.logging("Exception _correct_essay")
            log_server.logging('str(e):\t\t' + str(e))
            return None

    def _extract_content_between_chinese_quotes(self, text):
        # 使用正则表达式匹配中文双引号内的内容
        pattern = r'“(.*?)”'  # 非贪婪匹配，匹配任意字符直到遇到第一个中文双引号
        matches = re.findall(pattern, text)
        return matches
    
    def _extract_content_between_quotes(self, text):
        # 使用正则表达式匹配中文双引号内的内容
        pattern = r'"(.*?)"'  # 非贪婪匹配，匹配任意字符直到遇到第一个中文双引号
        matches = re.findall(pattern, text)
        return matches

    def _find_closest_substring(self, target, source, char_threshold=3):
        """
        在给定的源字符串中，找出与目标字符串编辑距离最小且小于等于阈值的子串。
        
        :param target: 目标字符串
        :param source: 源字符串，需要在其内查找子串
        :param char_threshold: 编辑距离字符的阈值，例如5表示最多差5个字符
        :return: 编辑距离最小且满足阈值条件的子串，如果没有找到则返回None
        """
        min_distance = len(target)  # 初始化最小编辑距离为目标字符串的长度
        if min_distance <= 2:
            return None
        closest_substring = None
        threshold = char_threshold * 1.0 / min_distance
        start_pos = 0

        # 生成所有可能的子串
        for i in range(len(source) - len(target) + 1):
            for j in range(i + len(target), len(source) + 1):
                substring = source[i:j]
                # 计算编辑距离
                distance = difflib.SequenceMatcher(None, target, substring).ratio()
                # 将编辑距离转换为所需的形式（1 - ratio() 得到实际的编辑距离）
                distance = (1 - distance) * len(target)  # 标准化编辑距离

                # 检查是否满足条件：编辑距离小于等于阈值且是目前找到的最小值
                if distance <= threshold and distance < min_distance:
                    min_distance = distance
                    closest_substring = substring
                    start_pos = i

        return closest_substring, start_pos
    
    def _correct_essay_by_baidu(self, grade, totalScore, content, task='en-app', problem=None):
        correction_result = self._correct_essay(grade, totalScore, content, model='ayx', task=task, problem=problem)
        print('correction_result : ', correction_result)
        # 数据转换
        if correction_result is not None and isinstance(correction_result, dict):
            log_server.logging("data transform")
            correction_result['highlight'] = []
            correction_result['error_set'] = []
            # 百度的接口没有返回的percentageScore不对，需要做些转换才能和电信的保持一致
            # 百度的语文接口返回的分数是以60分作文总分的
            if math.fabs(totalScore) > 0.001:

                correction_result['percentageScore'] = correction_result['totalScore'] / 60 * 100

        return correction_result

    def _correct_essay_by_dianxin(self, grade, totalScore, content, task='en-app', problem=None):
        # print('content type: ', type(content))
        # print('content: ', content)
        correction_result = self._correct_essay(grade, totalScore, content, model='dianxin', task=task, problem=problem)
        if correction_result is None or not isinstance(correction_result, dict):
            return None
        
        # 数据转换
        if correction_result is not None:
            correction_result['highlight'] = []
            correction_result['error_set'] = []

            # 亮点表达
            # 样例
            # "1.“唯有摒俗乐之尘，逐清欢之璋，方助吾侪攀人生高峰，实现自我价值”。",
            # "2.“一味沉溺于低俗，短时的快乐之中，青年何以明确人生方向，国家又何以富强”。",
            # "3.“林清玄曾言：‘明月为云所遮，我知明月仍在云层深处。’愿吾侪拨开俗乐之乌云，寻觅清欢之明月，于追逐清欢之中寻人生航向，书写青春风采”。",
            # "4.“吾侪当脚踏实地，于人生之路上栽种理想之树，亦应追逐清欢，于修篱种菊，品茗论诗中提升自我修为”。",
            # "5.“明月为云所遮，我知明月仍在云层深处”。引用诗句，增强文章的艺术性。"
            # step1：提取中文双引号之间的字符串
            # step2: 在全文中搜索这段内容在整个作文中处在的位置
            # step3: 按照原结构构造highlight

            if 'expression' in correction_result.keys():
                expressions = correction_result['expression']
                highlight = []
                for expression in expressions:
                    matched_text_list = self._extract_content_between_chinese_quotes(expression)
                    print('matched_text_list type: ', type(matched_text_list))
                    print('matched_text_list: ', matched_text_list)
                    if matched_text_list is not None and len(matched_text_list) > 0:
                        text = matched_text_list[0]
                        # 先直接找，找不到的话需要根据编辑距离找最接近的
                        # bad case : “身为牛运。人亦是如此”和“身为牛运，人亦是如此”
                        start_pos = content.find(text)

                        if start_pos >= 0:
                            end_pos = start_pos + len(text)
                            highlight.append([text, [start_pos, end_pos]])
                        # else:
                        #     # 找最接近的字符串
                        #     closest_substring, start_pos = self._find_closest_substring(text, content)
                        #     if closest_substring is not None:
                        #         end_pos = start_pos + len(closest_substring)
                        #         highlight.append([text, [start_pos, end_pos]])                               
                                
                correction_result['highlight'] = highlight


            # 语法错误
            # 样例
            # {
            # "ori": "\"It' Elisha she fell into the deep end of the pod.\"",
            # "reason": "语法错误，应修改为\"It was Elisha who fell into the deep end of the pool.\""
            # }
            # step1：提取双引号之间的字符串
            # step2: 在全文中搜索这段内容在整个作文中处在的位置
            # step3: 按照原结构构造error_set
            if 'errorCorrection' in correction_result.keys():
                errorCorrections = correction_result['errorCorrection']
                error_set = []
                for error in errorCorrections:
                    print('error : ', error)
                    ori_text = error['ori']
                    message = error['reason']
                    if ori_text is not None and len(ori_text) > 4:
                        ori_text = ori_text[2:-2]
                        print('ori_text', ori_text)
                        start_pos = content.find(ori_text)
                        print('start_pos : ', start_pos)
                        if start_pos >= 0:
                            error_set.append({"offset":start_pos, "message":message, "length":len(ori_text)})
                correction_result['error_set'] = error_set
                
        return correction_result

    def _correct_essay_by_dify(self, grade, totalScore, content, task='cn', problem=None,
                                subject_id=None, block_id=None, task_key=None, student_key=None):
        """
        使用Dify工作流批改语文作文，返回格式与电信模型对齐

        Args:
            grade: 年级
            totalScore: 总分
            content: 学生作文内容
            task: 任务类型（默认为cn表示语文）
            problem: 作文题目要求
            subject_id: 学科ID
            block_id: 题目块ID
            task_key: 任务标识
            student_key: 学生标识

        Returns:
            批改结果字典（对齐电信模型格式）
        """
        log_server.logging("enter _correct_essay_by_dify")

        try:
            # 调用Dify工作流进行批改
            dify_result = correct_chinese_essay_with_dify(
                content=content,
                problem=problem,
                grade=grade,
                totalScore=totalScore,
                subject_id=subject_id,
                block_id=block_id,
                task_key=task_key,
                student_key=student_key
            )

            log_server.logging("Dify raw result: {}".format(json.dumps(dify_result, ensure_ascii=False)))

            # 验证机制：当解析失败时从llm_output补救
            if dify_result.get("score", 0) == 0 and "raw_response" in dify_result:
                raw = dify_result.get("raw_response", {})
                if raw.get("error") and raw.get("llm_output"):
                    try:
                        import re
                        # 首先处理可能的字符串包装和转义
                        llm_text = raw["llm_output"]

                        # 如果是被引号包装的字符串，先解析一层
                        if llm_text.startswith('"') and llm_text.endswith('"'):
                            try:
                                llm_text = json.loads(llm_text)
                            except:
                                pass

                        # 提取JSON内容
                        m = re.search(r'\{[\s\S]*\}', llm_text)
                        if m:
                            json_str = m.group()

                            # 参考工作流的处理规则，进行预处理
                            # 1. 处理转义的引号（将 \\\" 转换为 "）
                            json_str = json_str.replace('\\"', '"')

                            # 2. 转义中文引号
                            json_str = json_str.replace(""", '\\"').replace(""", '\\"')

                            # 3. 中文标点转英文
                            json_str = json_str.replace("，", ",").replace("：", ":")

                            # 4. 补全reason后的逗号（工作流中的核心修复）
                            json_str = re.sub(r'("reason"):"([^"]*)"(?=\s*"score_dimension")', r'\1:"\2",', json_str)

                            # 5. 清理多余逗号
                            json_str = json_str.replace(',}', '}').replace(',]', ']')

                            d = json.loads(json_str)
                            if d.get("score", 0) > 0:  # 只有解析出有效分数才更新
                                dify_result["score"] = d["score"]
                                dify_result["totalScore"] = d["score"]
                                dify_result["percentageScore"] = (d["score"] / 60.0) * 100
                                dify_result["comment"] = d.get("reason", "")

                                # 处理维度分数
                                if d.get("score_dimension"):
                                    # 维度总分映射（服务端返回4分制）
                                    dim_max = {"主题契合": 4, "内容与情感": 4, "结构严谨": 4, "表达规范": 4}
                                    for dim in d["score_dimension"]:
                                        if isinstance(dim, dict):
                                            name = dim.get("dimension_name", "")
                                            score = float(dim.get("dimension_score", 0))
                                            if name in dim_max:
                                                # 转换为5分制
                                                five_score = round((score / dim_max[name]) * 5)
                                                five_score = max(0, min(5, five_score))
                                                # 更新对应字段
                                                if name == "主题契合":
                                                    dify_result["topicScore"] = five_score
                                                elif name == "内容与情感":
                                                    dify_result["contentScore"] = five_score
                                                elif name == "结构严谨":
                                                    dify_result["structureScore"] = five_score
                                                elif name == "表达规范":
                                                    dify_result["languageScore"] = five_score

                                log_server.logging("从llm_output补救成功")
                    except:
                        pass  # 静默失败，保持原值

            # Dify客户端已经返回对齐后的格式，直接使用
            correction_result = {
                # 基础分数字段
                'score': dify_result.get('score', 0),
                'totalScore': dify_result.get('totalScore', 0),
                'percentageScore': dify_result.get('percentageScore', 0),

                # 维度分数（5分制）
                'topicScore': dify_result.get('topicScore', 0),
                'contentScore': dify_result.get('contentScore', 0),
                'structureScore': dify_result.get('structureScore', 0),
                'languageScore': dify_result.get('languageScore', 0),

                # 评语和建议
                'comment': dify_result.get('comment', ''),
                'suggestion': dify_result.get('suggestion', ''),

                # 错误纠正和表达优化
                'errorCorrection': dify_result.get('errorCorrection', []),
                'expression': dify_result.get('expression', []),
                'improveArticle': dify_result.get('improveArticle', ''),

                # 错误集合（兼容原格式）
                'error_set': [],

                # 保留原始维度信息
                'score_dimension': dify_result.get('score_dimension', [])
            }

            # 处理错误纠正信息，转换为error_set格式（如果有）
            if correction_result['errorCorrection']:
                error_set = []
                for error in correction_result['errorCorrection']:
                    if isinstance(error, dict):
                        ori_text = error.get('ori', '')
                        message = error.get('reason', '')
                        if ori_text and len(ori_text) > 4:
                            # 去掉前后的标记符号
                            ori_text = ori_text[2:-2] if ori_text.startswith('【【') and ori_text.endswith('】】') else ori_text
                            offset = content.find(ori_text)
                            if offset >= 0:
                                error_set.append({
                                    "offset": offset,
                                    "length": len(ori_text),
                                    "message": message
                                })
                correction_result['error_set'] = error_set

            # 处理表达优化，提取高亮句子
            highlight = []
            if correction_result['expression']:
                for expression in correction_result['expression']:
                    if isinstance(expression, str):
                        # 提取引号之间的文本
                        matched_text_list = self._extract_content_between_chinese_quotes(expression)
                        for matched_text in matched_text_list:
                            offset = content.find(matched_text)
                            if offset >= 0:
                                highlight.append({
                                    "offset": offset,
                                    "length": len(matched_text),
                                    "text": matched_text,
                                    "reason": expression
                                })
            correction_result['highlight'] = highlight  # 确保始终有highlight字段

            log_server.logging("Dify formatted result (aligned with DianXin): {}".format(json.dumps(correction_result, ensure_ascii=False)))

            return correction_result

        except Exception as e:
            log_server.logging("Error in _correct_essay_by_dify: {}".format(str(e)))
            # 返回默认结果（对齐电信模型格式）
            return {
                'score': 0,
                'totalScore': 0,
                'percentageScore': 0,
                'topicScore': 0,
                'contentScore': 0,
                'structureScore': 0,
                'languageScore': 0,
                'comment': '批改服务异常: {}'.format(str(e)),
                'suggestion': '',
                'errorCorrection': [],
                'expression': [],
                'improveArticle': '',
                'error_set': [],
                'highlight': []
            }


    def parser_one_essay(self, subjectId, blockId, taskKey, grade, totalScore, students, model='ayx', task='en-app', problem=None):
        log_server.logging("enter parser_one_essay")
        
        # 原来的批改接口
        if model == 'ayx' and task == 'en-app':
            return self._parser_one_essay(subjectId, blockId, taskKey, grade, totalScore, students)
        
        # 基于大模型的批改接口

        students_res = list()                       # "students" filed call interface result
        for student in students:
            uploadKey = student['uploadKey']
            post_text = student['post_text']

            if model == 'ayx':
                log_server.logging("_correct_essay_by_baidu, task : %s" %(task))
                correction_result = self._correct_essay_by_dify(
                    grade, totalScore, post_text, task=task, problem=problem,
                    subject_id=subjectId, block_id=blockId, task_key=taskKey, student_key=uploadKey
                )
                log_server.logging("_correct_essay_by_baidu done")
            elif model == 'dianxin':
                log_server.logging("_correct_essay_by_dianxin, task : %s" %(task))
                correction_result = self._correct_essay_by_dianxin(grade, totalScore, post_text, task=task, problem=problem)
                log_server.logging("_correct_essay_by_dianxin done")
            # elif model == 'dianxin':
            #     log_server.logging("_correct_essay_by_dify, task : %s" %(task))
            #     correction_result = self._correct_essay_by_dify(grade, totalScore, post_text, task=task, problem=problem)
            #     log_server.logging("_correct_essay_by_dify done")
            log_server.logging("correct result : " + json.dumps(correction_result, ensure_ascii=False))

            every_student_info = dict()                # every student call interface result
            every_student_info['uploadKey'] = uploadKey
            if correction_result is not None and isinstance(correction_result, dict):
                # 阅卷那边的score其实是百分比
                percentageScore = correction_result['percentageScore']
                if isinstance(percentageScore, str):
                    every_student_info['score']     = 0
                else:
                    every_student_info['score']     = correction_result['percentageScore'] / 100.0
                every_student_info['highlight'] = correction_result.get('highlight', [])
                every_student_info['error_set'] = correction_result.get('error_set', [])
                every_student_info['comment'] = correction_result.get('comment', '')
                every_student_info['suggestion'] = correction_result.get('suggestion', '')
                every_student_info['improveArticle'] = correction_result.get('improveArticle', '')
                every_student_info['topicScore'] = correction_result.get('topicScore', 0)
                every_student_info['contentScore'] = correction_result.get('contentScore', 0)
                every_student_info['structureScore'] = correction_result.get('structureScore', 0)
                every_student_info['languageScore'] = correction_result.get('languageScore', 0)
                every_student_info['errorCorrection'] = correction_result.get('errorCorrection', [])
                every_student_info['expression'] = correction_result.get('expression', [])
            else:
                every_student_info['score']     = 0
                every_student_info['highlight'] = []
                every_student_info['error_set'] = []
                every_student_info['comment'] = ''
                every_student_info['suggestion'] = []
                every_student_info['improveArticle'] = ''
                every_student_info['topicScore'] = 0
                every_student_info['contentScore'] = 0
                every_student_info['structureScore'] = 0
                every_student_info['languageScore'] = 0
                every_student_info['errorCorrection'] = []
                every_student_info['expression'] = []



            #logging.info("every_student_info: %s", every_student_info)
            students_res.append(every_student_info)

        correction_res = dict()                        # final result dict
        correction_res['subjectId'] = subjectId
        correction_res['blockId'] = blockId
        correction_res['taskKey'] = taskKey
        correction_res['students'] = students_res
        correction_res['model'] = model
        correction_res['task'] = task
        #logging.info('correction_res: %s', correction_res)
        log_server.logging("exit parser_one_essay")

        return correction_res

    # 原来我们爱云校自己的作文批改接口
    def _parser_one_essay(self, subjectId, blockId, taskKey, grade, totalScore, students):
        """
        Parse incoming data
        :param subjectId:
        :param key:
        :param grade:
        :param post_text:
        :param totalScore:
        :return:
        """
        students_res = list()                       # "students" filed call interface result
        for student in students:
            uploadKey = student['uploadKey']
            post_text = student['post_text']
            self.log_server.logging('Post Text: {}'.format(post_text))
            if '\n' in post_text:
                post_text = re.sub("\n", "", post_text)

            error_rules_set = []                    # set of error rules
            self.log_server.logging('>>> Do GEC ...')
            gec_start_time = time.time()
            try:
                gec_response = requests.post(self.gec_url, json={'post_content': post_text})
                self.log_server.logging('GEC status: {}'.format(gec_response))
                gec_end_time = time.time()
                gec_status_code = gec_response.status_code    # gec request status code
                if gec_status_code == 200:
                    gec_res = json.loads(gec_response.text)
                    print('gec len : ', len(gec_res))
                    if gec_res:
                        for gec_rule in gec_res:
                            offset = gec_rule['offset']
                            id = gec_rule['rule']['id']
                            category = gec_rule['rule']['category']
                            rule_dict = {'id': id, 'category': category}
                            message = gec_rule['message']
                            length = gec_rule['length']

                            gec_every_rule = {'offset': offset,
                                          'rule': rule_dict,
                                          'message': message,
                                          'length': length}
                            # logging.info('every GEC rule: {}'.format(gec_every_rule))
                            error_rules_set.append(gec_every_rule)
                else:
                    error_rules_set.append({})
            except Exception as e:
                self.log_server.logging('GEC ERROR: {}'.format(e))
                error_rules_set.append({})
            gec_time = gec_end_time - gec_start_time   # GEC runtime
            self.log_server.logging('GEC Runtime: {}'.format(gec_time))
            self.log_server.logging('GEC Finish! >>>')

            self.log_server.logging('>>> Do AES ...')
            data1 = {'post_content': post_text, 'grade': grade}
            #logging.info("AES Process Essay: {}".format(data1))
            aes_start_time = time.time()
            try:
                aes_response = requests.post(self.aes_url, data=data1)
                self.log_server.logging('AES status: {}'.format(aes_response))
                aes_end_time = time.time()
                aes_status_code = aes_response.status_code     # aes request status code
                if aes_status_code == 200:
                    res_res = json.loads(aes_response.text)
                    predict_score = res_res['predict']         # predict score
                    highlight_words = res_res['highlight']
                else:
                    predict_score = 0
                    highlight_words = []
            except Exception as e:
                self.log_server.logging('AES ERROR: {}'.format(e))
                predict_score = 0
                highlight_words = []
            aes_time = aes_end_time - aes_start_time   # aes runtime
            # Score adjustment
            predict_score = self.score_adjustment(predict_score, totalScore)

            self.log_server.logging("AES predict_score: {}".format(predict_score))
            self.log_server.logging("AES highlight_word: {}".format(highlight_words))
            self.log_server.logging("AES Runtime: {}".format(aes_time))
            self.log_server.logging("AES Finish! >>>")


            # Judge list contains {}
            if {} in error_rules_set:
                error_rules_set = [item for item in error_rules_set if item!={}]

            #unrepeat_error_rules_set = self.remove_repeat(error_rules_set)    # remove duplicate rules
            #LN_ merge_rule = self.pprocess._process(error_rules_set, post_text)
            # logging.info("Merge finished >>>")

            every_student_info = dict()                # every student call interface result
            every_student_info['uploadKey'] = uploadKey
            every_student_info['score']     = predict_score
            every_student_info['highlight'] = highlight_words
            every_student_info['error_set'] = error_rules_set
            #logging.info("every_student_info: %s", every_student_info)
            students_res.append(every_student_info)

        correction_res = dict()                        # final result dict
        correction_res['subjectId'] = subjectId
        correction_res['blockId'] = blockId
        correction_res['taskKey'] = taskKey
        correction_res['students'] = students_res
        #logging.info('correction_res: %s', correction_res)

        return correction_res


def save_json(save_root, data):
    with open(save_root, 'w', encoding='utf8') as f:
        json.dump(data, f, ensure_ascii=False)
    
    
# 中文批改测试
def main_cn():
    ec = EssayCorrection(log_server)
    subjectId = '123456'
    blockId = '12345'
    taskKey = '12345'
    grade = '高二'
    totalScore = 60
    students = [ {
                    "uploadKey":"test1",
                    "post_text":"撑正视快乐之长篇，向提高素养处慢溯但是，并不是每个人都会追寻正确的快乐\n　　流年不改，星河暗换，蝉鸣高树，彧彧花在科技“光速”发展的背景下，越来越多的人繁。在当今高速发展的时代，各种科技产品。沉沦在打麻将、熬夜追剧，肝游戏中，以“摆娱乐设施日新月异，人们得以烂“放松,休闲为的方挡篇牌，以“躺平”为旗帜、长此以往式越来越多，获得快乐的方式层出不穷。但掩不仅是他们的身体先跨掉，更可怕的是已然失卷谭思，我们应追求怎样的快乐，才能免于沉去了奋进之心，彻底沦为自暴自弃者，终会被沦而提升自我呢？遗弃在虚拟的幻境中。这就是他们所谓的快乐\n　　追求快乐，需正视其本质诸.当下，作为新时代的青年,时代的接\n　　正如刘禹锡在《陋室铭》中所言：“谈笑有力棒已经在我们手中。我们应以在困难面前解鸿儒，往来无白丁，可以调素琴，阅金经。”虽决它为快乐：在未知的领域中以“怀八荒、入身居陋室，但他的快乐却得以满足。弹琴、读九重”的精神探索为快乐；以自身的素养提升书，朴素中渗透着典雅，实在令人向往。由此为快乐……追求“更高级”的快乐，拉开我们可见，快乐的本质不在于方式而在于人的心境与别人的差距，也拉开中国与世界的差距，与抱负，就像胡安焉，即使是在宿舍楼的杂物七十载惊涛拍岸，九万里风鹏正举，在实间内，即使是在微弱的灯光下，他仍可沉浸在现中华民族伟大复兴的路上，吾侪应追寻“破自己所向往的阅读汪洋中，品味着知识所带给难”之快乐，提高素养之快乐，才能在不远的他的滋润。君可见，年近九旬的\"现代风洞技光辉岁月中，将历史改写为我们的辉煌\\术理论奠基人“俞鸿儒院士仍沉浸在探索风洞的快乐中，提升我国风洞军事实力；君可见“探界者”钟扬心中满怀对种子的期盼，行走在辽阔的青藏高原上，他的快乐，是挽救濒危物种，为中国种质库贡献力量。以提升自我：涵养素质，甚至造福国家的快乐，才拉开了胡安焉与只会打牌的同事间的差距，也拉开了人与人间的差距Tw"

                }]
    model='ayx'
    task='cn'
    problem="阅读下面的材料，根据要求写作。(60分)23.胡安焉在北京送快递时，每晚下班后，都会关掉手机，独自在宿舍楼的杂物间待两个小时。没有同事间吆喝的牌局，也没有手游网剧的干扰，他就着昏暗的灯光，读完了《尤利西斯》《没有个性的人》《审判》等大部头的著作。多年后，胡安焉成为一位畅销书作家，而当初寝室里消遣的同事，依然在快递站点起早贪黑地工作。当今时代，获得快乐的方式层出不穷，但追求怎样的快乐，拉开了人与人之间的差距。要求:综合材料内容及含意，选好角度，确定立意，明确文体，自拟标题，不要套作不得抄装，不得泄露个人信息:不少于800字"
    correction_res = ec.parser_one_essay(subjectId, blockId, taskKey, grade, totalScore, students, model, task, problem)
    print(correction_res)

# 英文批改测试
def main_en_with_dianxin_model():
    ec = EssayCorrection(log_server)
    subjectId = '123456'
    blockId = '12345'
    taskKey = '12345'
    grade = '高二'
    totalScore = 60
    students = [ {
                    "uploadKey":"test1",
                    "post_text":"六应用文(15分) To Whom It May Concem, I'm student Li Hua. Knowing that there's a requirement for a host to the English-reading Salon, I sincerely write to apply for the vacancy To begin with, I'm experienced in the work of being host, so that I can be skilled in grasp the salan's atmosphere Second, a long-term practising in oral English equips me the ability to express my consideration fluently. Last but not least, I will hold in salon in a good term. Firstly, I will invite particulers to introduce themselves, then starts to recommend books one by one. I would appreciated if you take my applicants into consideration. ; , Yours, Li Hua "

                }]
    model='dianxin'
    task='en-app'
    problem="第四部分写作(满分15分)假定你是李华，得知研学机构 Global Camp 正在招募市图书馆暑期“英语阅读沙龙(English-reading Salon) 活动的主持人，请写一封英文申请信，内容包括:1.个人情况和优势2.流程设想3.承诺和期待注意:1.写作词数应为80左右;2.请按如下格式在答题卡的相应位置作答To Whom It May Concern,"
    correction_res = ec.parser_one_essay(subjectId, blockId, taskKey, grade, totalScore, students, model, task, problem)
    print(correction_res)

# 英文批改测试
def main_en_with_ayx_model():
    ec = EssayCorrection(log_server)
    subjectId = '123456'
    blockId = '12345'
    taskKey = '12345'
    grade = '高二'
    totalScore = 15
    students = [ {
                    "uploadKey":"test1",
                    "post_text":"I'm Li Hua. I notioce that some students eat snacks at mealtimes instead of naving meals. Now I'd like to call on you to form a healthy eating habit. For us students, eating healthy food is of great importane because we need enough nutrients to keep our body functoning well. Having meals regulary is a good way to keep fit and prevent deceases. By eating snack. we may get sick easily. let's change our way of living. Let's have a healthy dret from now on. By having meals regulary, We will grow up healthily and happily"

                }]
    # model='dianxin'
    # task='en-app'
    # problem="第四部分写作(满分15分)假定你是李华，得知研学机构 Global Camp 正在招募市图书馆暑期“英语阅读沙龙(English-reading Salon) 活动的主持人，请写一封英文申请信，内容包括:1.个人情况和优势2.流程设想3.承诺和期待注意:1.写作词数应为80左右;2.请按如下格式在答题卡的相应位置作答To Whom It May Concern,"
    correction_res = ec.parser_one_essay(subjectId, blockId, taskKey, grade, totalScore, students)
    print(correction_res)

def test(content):
    pprocess = MergeRuleMethod()
    call = CallInterface()
    error_rules_set, gec_rule_num, lt_rule_num, origin_rule_num = call.collection_gec_lt_data(content)
    #merge_rule = pprocess._process()
    merge_rule = pprocess._process(error_rules_set, content)


if __name__ == '__main__':
    # test(content3)
    # main_cn()
    # main_en_with_dianxin_model()
    main_en_with_ayx_model()
    
