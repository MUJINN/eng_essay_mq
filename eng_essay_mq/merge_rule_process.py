import os
import re
import json
import requests
import time
import codecs
import nltk
import random
import operator
from tqdm import tqdm
import logging
LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"
logging.basicConfig(filename='call_interface_result.log', level=logging.INFO, format=LOG_FORMAT)


# Traversing the vocabulary
with codecs.open("./all_vocabulary.json", mode='r', encoding='utf-8') as fr:
    vocabulary_json = json.load(fr)
vocabulary = list(vocabulary_json.keys())
# Test case
content1 = {'post_content':"For example, Beijing duck, suger care Fresh Fruits and make and so on. Secondly we alse but instant to with together with us"}

def make_data_set():
    content_list = list()

    with codecs.open("./data/source_target.json", mode='r', encoding='utf-8') as fr:
        json_data = json.load(fr)

    selset_content = random.sample(json_data, 500)
    for item in selset_content:
        temp_1   = dict()
        temp_2 = dict()
        rule_set = []
        temp_1["post_content"] = item['source']
        collection_gec_data(temp_1, rule_set)
        collection_lt_data(temp_1, rule_set)
        temp_2[item['source']] = rule_set
        content_list.append(temp_2)

    #content_list.append([item['source'] for item in selset_content])
    with codecs.open("./data/make_data.json", mode='w', encoding='utf-8') as fw:
        fw.write(json.dumps(content_list, ensure_ascii=False))


class CallInterface:
    def __init__(self):
        pass

    def collection_gec_lt_data(self, content):
        """
        collection gec result and collection languagetool result
        :param content: input json format content , exp: {'post_content':"For example, Beijing duck, suger care Fresh ..."}
        :return error_rules_set:  all rule set
        :return gec_rule_num: GEC check rule num
        """
        error_rules_set = []  #Rule set

        gec_response = requests.post(url="http://192.168.1.111:5055/grammar_post", data=content)
        gec_result = json.loads(gec_response.text)

        for gec_rule in gec_result:
            offset = gec_rule['offset']
            id = gec_rule['rule']['id']
            category = gec_rule['rule']['category']
            rule_dict = {'id': id, 'category': category}
            # message = gec_rule['message']
            
            # Remove spaces and "\n" in rules 
            if '\n' or '  ' in gec_rule['message']:
                new_message = re.sub(r'\n', '', gec_rule['message'])
                new_message     = re.sub(r'\s+', ' ', new_message)
            length = gec_rule['length']

            every_rule = {'offset': offset,
                          'rule': rule_dict,
                          'message': new_message,
                          'length': length}

            error_rules_set.append(every_rule)

        #print("### LT rule ###")
        lt_response = requests.post(url="http://192.168.1.103:5050/languagetool_post", data=content)
        lt_result = json.loads(lt_response.text)

        for lt_rule in lt_result:
            offset = lt_rule['offset']
            id = lt_rule['rule']['id']
            category = lt_rule['rule']['category']
            rule_dict = {'id': id, 'category': category}
            message = lt_rule['message']
            length = lt_rule['length']
        
            lt_every_rule = {'offset': offset,
                             'rule': rule_dict,
                             'message': message,
                             'length': length}

            error_rules_set.append(lt_every_rule)

        gec_rule_num = len(gec_result)
        lt_rule_num = len(lt_result)
        origin_rule_num = gec_rule_num + lt_rule_num

        return error_rules_set, gec_rule_num, lt_rule_num, origin_rule_num


class MergeRuleMethod:
    def __init__(self):
        with codecs.open("./all_vocabulary.json", mode='r', encoding='utf-8') as fr:
            vocabulary_json = json.load(fr)
        self.vocabulary = list(vocabulary_json.keys())

    def exist_gold_rule(self, rule_set):
        """
        Does it exist gold gec rule
        :param rule_set: all rule set
        :return golden_rule, common_rule: 
        """
        golden_rule = []   # golden rule , don't merge
        common_rule = []   # Prepare the next step for merging rules
  
        for item in rule_set:
            id = item['rule']['id']
            if id == "golden_gec":
                golden_rule.append(item)
            else:
                common_rule.append(item)
        return golden_rule, common_rule

    def merge_method_remove_repeat(self, rule_set):
        """
        Remove the same rules for location and type
        :param rule_set: all rule set
        :return removed_rule_set: removed the set after the repeat rule
        """
        #print(" >>> Into Remove Repeat >>> ")
        repeat_elem      = set()   # Do-removed element
        removed_rule_set = list()  # Return value after completing the deduplication task
        del_elems        = list()  # The element to be deleted after the second selection

        try:
            # Remove completely repeating elements
            for item in rule_set:
                slice_str = "%s,%s,%s,%s" % (item['offset'], item['length'], item['rule']['category'], item['rule']['id'])
                logging.info("slice:", slice_str)
                repeat_elem.add(slice_str)
            rep_list = list(repeat_elem)

            # Call selection rule function
            index = self._select_rule_tool(rep_list)

            # Delete unnecessary rules after selection
            for i in index:
                del_elems.append(rep_list[i])
            for elem in del_elems:
                rep_list.remove(elem)
            # Restore the extracted element index to a rule
            for elem in rep_list:
                elem_split = elem.split(',')
                for rule in rule_set:
                    if int(elem_split[0]) == rule['offset'] and int(elem_split[1]) == rule['length'] and elem_split[2] == rule['rule']['category'] :
                        removed_rule_set.append(rule)
                        break
            logging.info("LEN:", len(removed_rule_set))
            merge_rules_set_pre = removed_rule_set
            return merge_rules_set_pre
        except:
            logging.info("Merge Remove ERROR!")
            return rule_set


    def merge_method_1(self, rule_set, content):
        """
        The first method of merge rule which find out if there is a wrong word.
        :param rule_set: all rule set
        :param content : the original text 
        :return merge_rules_set_1: Return to the filtered rule set
        """
        #print(" >>> Into Method 1 >>> ")
        punctuation = [".", ",", "!", "?", "...", "<", ">", "(", ")", "{", "}", "[", "]", "@", "#", "$", "%", "^", "&", "*", "-", "+", "=", ":", ";", "'", "/", "|", "~"]
        merge_rules_set_1 = []
        try:
            #print("Pre-processing rule：", len(rule_set))
            for item in rule_set:
                
                start_pos = item['offset']
                end_pos   = start_pos + item['length']
                #_str      = content['post_content'][start_pos:end_pos]
                _str      = content[start_pos:end_pos]
                pro_str   = nltk.word_tokenize(_str)
                for word in pro_str:
                    if word in punctuation:
                        pro_str.remove(word)

                flag = self._isExistVocab_tool(pro_str, self.vocabulary)
                if flag == True:
                    merge_rules_set_1.append(item)
            return merge_rules_set_1
        except:
            logging.info("Merge_1 ERROR!")
            return rule_set


    def merge_method_2(self, rule_set, content):
        """
        The second method is to solve the rule of identifying a large span. 
        :param rule_set: all rule set
        :param content : the original text 
        :return merge_rules_set_2[0]: Return to the filtered rule set
        """
        merge_rules_set_2 = []  # method_2 merge rule result list
        temp_rule         = []  # Intermediate variable list
        try:
            for i in range(len(rule_set)):
                start_pos = rule_set[i]['offset']
                end_pos   = start_pos + rule_set[i]['length']
                length    = rule_set[i]['length']
                if operator.ge(length, 20):
                    #_str = content1['post_content'][start_pos:end_pos]
                    _str = content[start_pos:end_pos]
                    pro_str = nltk.word_tokenize(_str)
                    if operator.ge(len(pro_str), 5):
                        temp_rule.append(rule_set[i])
            merge_rules_set_2.append([item for item in rule_set if item not in temp_rule])
            return merge_rules_set_2[0]
        except:
            logging.info("Merge_2 ERROR!")
            return rule_set


    def merge_method_3(self, rule_set):
        """
        The second method is to solve the rule of identifying a large span.
        :param rule_set: all rule set
        :return: 
        """
        #print(" >>> Into Method 3 >>> ")
        del_index = list()  # The index position of the rule to be deleted
        del_elems = list()  # Rule to be deleted
        try:
            for m in range(len(rule_set)):
                start_m = rule_set[m]['offset']
                end_m   = start_m + rule_set[m]['length']
                length_m= rule_set[m]['length']
                id_m    = rule_set[m]['rule']['id']
                for n in range(m+1, len(rule_set)):
                    start_n = rule_set[n]['offset']
                    end_n   = start_n + rule_set[n]['length']
                    length_n= rule_set[n]['length']
                    id_n    = rule_set[n]['rule']['id']

                    # Part1 : big includes small 
                    # Left half closure (exp: [{......}....] or {..[......]....}, [] is lt , {} is gec )     
                    if start_m <= start_n and end_m > end_n or start_m >= start_n and end_m < end_n: 
                        # GEC includes LT
                        if id_m == 'gec' and id_n == 'gec':
                            if length_m > length_n:
                                del_index.append(m)
                            else:
                                del_index.append(n)
                                
                        elif id_m != 'gec' and id_n != 'gec':
                            if length_m > length_n:
                                del_index.append(m)
                            else:
                                del_index.append(n)
                                
                        # LT includes GEC or GEC includes LT
                        elif id_m == 'gec' and id_n != 'gec' or id_m != 'gec' and id_n == 'gec':
                            if length_m > length_n:
                                del_index.append(m)
                            else:
                                del_index.append(n)
                                   
                    # right half closure (exp: [....{.......}] or {.....[......]}, [] is lt , {} is gec   )  
                    elif start_m < start_n and end_m >= end_n or start_m > start_n and end_m <= end_n:
                        if length_m > length_n:
                            del_index.append(m)
                        else:
                            del_index.append(n)

                    # Part2 : Location intersection cross (exp: [....{....]........}  , [] is lt , {} is gec )
                    elif start_m < start_n and end_m < end_n and start_n < end_m or start_m > start_n and end_m > end_n and end_n > start_m:
                        # length_m = length_n , id_m == id_n == gec,  remove m or n (usually choose the previous one) . 
                        if length_m  == length_n and id_m == 'gec' and id_n == 'gec':
                            del_index.append(m)
                            break
                        # length_m = length_n , id_m != id_n != gec,  remove m or n (usually choose the previous one) . 
                        elif length_m == length_n and id_m != 'gec' and id_n != 'gec':
                            del_index.append(m)
                            break
                        # length_m = length_n , id_m == gec , id_n != gec,  remove m .
                        elif length_m == length_n and id_m == 'gec':
                            del_index.append(n)
                            break
                        # length_m = length_n , id_m != gec , id_n == gec,  retain m .
                        elif length_m == length_n and id_m != 'gec':
                            del_index.append(m)
                            break
                        # length_gec > length_lt or length_gec < length_lt, max(length) = gec or lt, if id_m = gec, remove n . 
                        elif length_m != length_n and id_m == 'gec':
                            del_index.append(n)
                            break
                        # length_gec > length_lt or length_gec < length_lt, max(length) = gec or lt, if id_n = gec, remove m . 
                        elif length_m != length_n and id_m != 'gec':
                            del_index.append(m)
                            break
                        # length_gec > length_lt or length_gec < length_lt, id_m == id_n == gec, remove max(length_m, length_n) .
                        elif length_m != length_n and id_m == 'gec' and id_n == 'gec':
                            if operator.gt(length_m, length_n):
                                del_index.append(m)
                                break
                            else:
                                del_index.append(n)
                                break
                        # length_gec > length_lt or length_gec < length_lt, id_m == id_n == lt, remove min(length_m, length_n) . 
                        elif length_m != length_n and id_m != 'gec' and id_n != 'gec':
                            if operator.gt(length_m, length_n):
                                del_index.append(n)
                                break
                            else:
                                del_index.append(m)


            #print(del_index)
            del_index = list(set(del_index))
            del_index.sort()

            # Delete the rules selected by Merge Method 3
            for i in del_index:
                del_elems.append(rule_set[i])
            for elem in del_elems:
                rule_set.remove(elem)

            merge_rules_set_3 = rule_set
            return merge_rules_set_3
        except:
            logging.info("Merge_3 ERROR!")
            return rule_set

    def regroup_rule(self, golden_rule, rule_set):
        """
        Regrouping golden rule and post-fusion rules
        :param rule_set: all rule set
        :param golden_rule: golden rules
        return final_rules:
        """
        final_rules = []
        for item_1 in golden_rule:
            final_rules.append(item_1)
        for item_2 in rule_set:
            final_rules.append(item_2)
        return final_rules
     
    def _select_rule_tool(self, rep_list):
        """
        Select rules from GEC and LT (TODO: increases fluency semantic judgment) to serve rule-based weighting
        :param rep_list: all rule set
        :return index: 
        """
        index = []
        for i in range(len(rep_list)):
            split_i = rep_list[i].split(",")
            for j in range(i+1, len(rep_list)):
                split_j = rep_list[j].split(",")
                # Determine LT or GEC, choose GEC
                if split_i[0] == split_j[0] and split_i[1] == split_j[1]:
                    if split_i[3] != 'gec':
                        index.append(i)
                    else:
                        index.append(j)
        return index

    def _isExistVocab_tool(self, word_list, vocabulary):
        """
        Judgement if the word is in the vocabulary
        :param word_list: list of words to be tested
        :param vocab: vocabulary
        :return: True is in vocabulary all word
        :return: False in not in vocabulary all word
        """
        for word in word_list:
            if word not in self.vocabulary:
                #print("No Vocab:", word)
                return False
        return True

    def _show_rule_tool(self, args_list):
        """
        Show all rule
        :param rule_set: all rule set
        """
        for item in args_list:
            print(item)

    def _process(self, error_rules_set, content):
        """
        Process of the entire process
        :param error_rules_set: all rule set
        :return merge_rules_set_3: After merge rule of result  
        """ 
        logging.info("Enter merge")
        if len(error_rules_set) != 0:
            # step1: Determine whether there is golden rules
            golden_rule, common_rule = self.exist_gold_rule(error_rules_set)
            # step2: Remove the exact same rules
            merge_rules_set_pre      = self.merge_method_remove_repeat(common_rule)
            # step3: Delete rules with incorrect words
            merge_rules_set_1        = self.merge_method_1(merge_rules_set_pre, content)
            # step4: Delete rules with a large span
            merge_rules_set_2        = self.merge_method_2(merge_rules_set_1, content)
            # step5: Merging overlapping rules
            merge_rules_set_3        = self.merge_method_3(merge_rules_set_2)
            # step6: Regrouping rules
            final_rules              = self.regroup_rule(golden_rule, merge_rules_set_3)
            logging.info("Finish merge")
            return final_rules
        else:
            return error_rules_set


def process(content):
    object = MergeRuleMethod()
    call   = CallInterface()
    # Conventional rule merge
    error_rules_set, gec_rule_num, lt_rule_num, origin_rule_num = call.collection_gec_lt_data(content)
    #print("========================")
    object._show_rule_tool(error_rules_set)
    print("1:", len(error_rules_set))
    merge_rules_set_pre = object.merge_method_remove_repeat(error_rules_set)
    merge_rules_set_1   = object.merge_method_1(merge_rules_set_pre, content)
    merge_rules_set_2   = object.merge_method_2(merge_rules_set_1, content)
    merge_rules_set_3   = object.merge_method_3(merge_rules_set_2)   

    merge_lt_rule_num, merge_gec_rule_num = 0, 0
    for rule in merge_rules_set_3:
        if rule['rule']['id'] == 'gec':
            merge_gec_rule_num += 1
        else:
            merge_lt_rule_num += 1
    merge_rule_num = len(merge_rules_set_3)

    return merge_rules_set_3, gec_rule_num, lt_rule_num, origin_rule_num, merge_rule_num, merge_lt_rule_num, merge_gec_rule_num


def batch_test():

    origin_all_rule_total = 0
    merge_all_rule_total  = 0
    origin_gec_rule_total = 0
    merge_gec_rule_total  = 0
    origin_lt_rule_total  = 0
    merge_lt_rule_total   = 0

    # load data
    with codecs.open("./data/eval_senior_No2.json", mode='r', encoding='utf-8') as fr:
        json_data = json.load(fr)
    sample_num = len(json_data)

    pbar = tqdm(json_data)
    for item in pbar:

        text = json_data[item][0]['content']
        #print(content)
        content  = dict()
        content['post_content'] = text
        merge_rules_set, gec_rule_num, lt_rule_num, origin_rule_num, merge_rule_num, merge_lt_rule_num, merge_gec_rule_num = process(content)

       
        origin_all_rule_total = origin_all_rule_total + origin_rule_num
        merge_all_rule_total  = merge_all_rule_total + merge_rule_num 
        origin_gec_rule_total = origin_gec_rule_total + gec_rule_num
        merge_gec_rule_total  = merge_gec_rule_total + merge_gec_rule_num 
        origin_lt_rule_total  = origin_lt_rule_total + lt_rule_num
        merge_lt_rule_total   = merge_lt_rule_total + merge_lt_rule_num

        pbar.set_description("Processing")
        #time.sleep(0.05)
        pbar.update(1)

    print("==============================================================")
    print("样本总数量           :", len(json_data))
    print("原始检错规则总数     ：", origin_all_rule_total)
    print("原始检错平均每篇错误数:", origin_all_rule_total/sample_num)
    print("规则去重融合处理后总数:", merge_all_rule_total)
    print("规则去重融合每篇错误数:", merge_all_rule_total/sample_num)
    print("原始检测GEC错误总数  :", origin_gec_rule_total)
    print("规则去重融合处理GEC错误总数:", merge_gec_rule_total)
    print("原始检测LT错误总数   :", origin_lt_rule_total)
    print("规则去重融合处理LT错误总数:", merge_lt_rule_total)
    print("原始检错GEC每篇错误数 {} , 规则去重融合处理GEC每篇错误数 {}".format(origin_gec_rule_total/sample_num, merge_gec_rule_total/sample_num))
    print("原始检错LT每篇错误数  {} , 规则去重融合处理LT每篇错误数  {}".format(origin_lt_rule_total/sample_num, merge_lt_rule_total/sample_num))
    print("==============================================================")


def main():
    object = MergeRuleMethod()
    merge_rules_set_3, gec_rule_num, lt_rule_num, origin_rule_num, merge_rule_num, merge_lt_rule_num, merge_gec_rule_num = process(content4)
    print("========================================")
    print("2:", len(merge_rules_set_3))
    object._show_rule_tool(merge_rules_set_3)
    #batch_test()

if __name__ == '__main__':
    main()


