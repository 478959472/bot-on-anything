# encoding:utf-8

from model.model import Model
from config import model_conf
from common import const
from common.log import logger
import requests
from requests_toolbelt.multipart.encoder import MultipartEncoder
import time
import uuid
sessions = {}

class ChatGPTDocModel(Model):
    def __init__(self):
        self.acs_token = model_conf(const.BAIDU).get('acs_token')
        self.cookie = model_conf(const.BAIDU).get('cookie')
        # http://10.10.217.176:9776/
        self.base_url = 'http://127.0.0.1:8100/api/questions'
        # self.base_url = 'http://10.10.217.176:9776/api/questions'

    def reply(self, query, context=None):
        logger.info("[BAIDU] query={}".format(query))
        user_id = context.get('session_id') or context.get('from_user_id')
        context['query'] = query

        # 1.create session
        chat_session_id = sessions.get(user_id)
        if not chat_session_id:
            self.new_session(context)
            sessions[user_id] = context['chat_session_id']
        else:
            context['chat_session_id'] = chat_session_id

        # 2.create chat
        flag = self.new_chat(context)
        if not flag:
            return "创建会话失败，请稍后再试"

        # 3.query
        context['reply'] = ''
        self.query(context, 0, 0)

        return context['reply']


    def new_session(self, context):
        # data = {
        #     "sessionName": context['query'],
        #     "timestamp": int(time.time() * 1000),
        #     "deviceType": "pc"
        # }
        # res = requests.post(url=self.base_url+'/session/new', headers=self._create_header(), json=data)
        # print(res.headers)
        # 获取新UUID
        new_uuid = uuid.uuid4()

        # 将UUID转换为字符串
        new_uuid_str = str(new_uuid)
        context['chat_session_id'] = new_uuid_str #res.json()['data']['sessionId']
        logger.info("[BAIDU] newSession: id={}".format(context['chat_session_id']))


    def new_chat(self, context):

        context['model'] = 'GPT Turbo'
        context['parent_chat_id'] = '1'
        return True


    def query(self, context, sentence_id, count):
        headers = self._create_header()
        headers['Acs-Token'] = self.acs_token
        multipart_data = MultipartEncoder(
            fields={
                'question': context['query'],
            'model': context['model'],
            'uuid': '8078d199-aac0-452d-8487-698fc10d3c84',
            }
        )
        headers['Content-Type'] = multipart_data.content_type
        res = requests.post(url=self.base_url,  data=multipart_data, headers= headers)
        logger.debug("[BAIDU] query: sent_id={}, count={}, res={}".format(sentence_id, count, res.text))

        res = res.json()
        if res['answer'] != '':
            context['reply'] += res['answer']
            doc_titles=''
            for item in res['context']:
                if not item['title'] in doc_titles:
                    doc_titles += item['title'] + "\n"
            if len(doc_titles) > 0:
                doc_titles='\n相关文档：\n' + doc_titles
            context['reply'] += doc_titles
            # logger.debug("[BAIDU] query: sent_id={}, reply={}".format(sentence_id, res['data']['text']))
        else:
            context['reply'] += '系统无响应'
        return


    def _create_header(self):
        headers = {
            # 'Host': 'yiyan.baidu.com',
            # 'Origin': 'https://yiyan.baidu.com',
            # 'Referer': 'https://yiyan.baidu.com',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.0.0 Safari/537.36',
            'Cookie': self.cookie
        }
        return headers
