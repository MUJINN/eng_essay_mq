
from logserver import LogServer
log_server = LogServer(app='eng-essay-mq')
import json
from english_write import EssayCorrection
import time


essayCorrection = EssayCorrection(log_server)

def run_essay_correction(mq_data):
    """
    essay correction
    :param mq_data:
    :return:
    """
    try:
        
        log_server.logging('>>> come run_essay_correction')
        correction_time_begin = time.time()
        error_info = {'code': 0, 'message': 'fail', "data": "error params"}
        if len(mq_data) != 0:
            if isinstance(mq_data, bytes):
                mq_data = mq_data.decode()
            json_data = json.loads(mq_data)
        else:
            return json.dumps(error_info)

        #log_server.logging('receive mq_data:{}'.format(mq_data))
        global essayCorrection
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

        print('students : ', students)
        
        # Judge totalScore is valid
        if totalScore == None or totalScore <= 0 or totalScore > 100:
            totalScore = 0
            correction_res = ec.parser_one_essay(subjectId, blockId, taskKey, grade, totalScore, students, model=model, task=task, problem=problem)
        else:
            correction_res = ec.parser_one_essay(subjectId, blockId, taskKey, grade, totalScore, students, model=model, task=task, problem=problem)

        print('correction_res : ', correction_res)
        #result_json = json.dumps(correction_res, ensure_ascii=False)
        result_json = json.dumps(correction_res)

        total_time = time.time() - correction_time_begin
        msg = {"mq_data":mq_data, "result":correction_res, "time":total_time}
        #logging.info(json.dumps(msg))
        log_server.logging('exit run_essay_correction function >>>')
        return result_json
    except Exception as e:
        #log_server.logging('incorrect json data:{}'.format(e))
        error_info = {'code': 0, 'message': 'fail', "data": "Exception"}
        return json.dumps(error_info)
    


if __name__ == '__main__':

    data = {"subjectId":8934878,"blockId":19937250,"taskKey":"8934878-19937250-1724408268699","students":[{"uploadKey":"50886-31570-7-1","post_text":"写作第二节 Without hesitation, Dad then led me to search around for Max. :\"Hi! Max, where are you staying?\" My dad shouted \"please come back to my home, we are very miss you!\" I said. For a momer we saw a old yellow dog which was our's Fax. But it became very thin and dirty. \"Oh, what a pity, my Fax is so sad.\"My dad said and huged the Fax. \"I am so happy to find you and I never want to loss you. I said. Finally, we statedgo home. \nBack to the court in vain, Dad finally did his special whistle.: I decide to take Fax away! He said. i \n"}],"model":"dianxin","task":"en-app","grade":"高二","totalScore":16,"problem":"写作"}
    result = run_essay_correction(json.dumps(data))