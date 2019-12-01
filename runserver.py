from flask import Flask
from flask import request
import requests
import json
import threading
import time
import datetime
from uwsgi_cache.cache import CacheManager
from wechatpy.utils import check_signature
from wechatpy.exceptions import InvalidSignatureException
from wechatpy import parse_message
from wechatpy.replies import TextReply
from models import DbController
from wechatpy import WeChatClient
from myLogger import mylogger


# APPID = 'wx94d947291c14ff43'
# APPSECRET = 'd9bbcd79a0ada896e3153e2bf0297785'
# TOKEN = 'Alex0618'
# ACCESS_TOKEN = '26_iJWdrITdsK-LEiioyoPUpydwXEp1P0sy8B8H0mo05HejEW0Sb7XV-nYklRmN1fSuI_QM-rUBZQg4dismgxDw-xgMOzJgySB8vUEBikujeE6K7aIc8qBVX_JkyfgXCKdABAFKS'
# EncodingAESKey = 'HCGFuWJBbaGyBH0N7N95zFVsQcaIDo1vcllpK5fOf8U'
# OPENID = ''
# PORT = 80

APPID = 'wx8400049e6d5ecb05'
APPSECRET = '1a32902bc0a3783b7770c4303da010db'
TOKEN = 'SDF666sys'
PORT = 5009

app = Flask(__name__)

mycache = CacheManager('mycache', 0)
mycache.set('access_tocken', '')
mycache.set('openid', '')

mutex = threading.Lock()
client = WeChatClient(APPID, APPSECRET)


def handlemsg(data):
    msg = parse_message(data)
    print(msg)
    global mycache, client
    mutex.acquire()
    mycache.set('openid', msg.source)
    mutex.release()
    if msg.type == 'text':
        if msg.content == '审核端':
            resp = 'http://www.lele.fit/mobile/'
        else:
            resp = msg.content
        reply = TextReply(content=resp, message=msg)
        xml = reply.render()
        return xml
    elif msg.type == 'event':
        if msg.event == 'subscribe':
            reply = TextReply(content="谢谢您的关注!!", message=msg)
            print('user: %s is in' % msg.source)
            user = client.user.get(msg.source)
            thd = DbController(func='add_user_subscribe', openid=msg.source, unionid=user['unionid'])
            thd.start()
            xml = reply.render()
            return xml
        elif msg.event == 'unsubscribe':
            thd = DbController(func='delete_user_subscribe', openid=msg.source)
            thd.start()
            print('user: %s has outed' % msg.source)
            return ''
        else:
            return ''
    else:
        reply = TextReply(content="nothing", message=msg)
        xml = reply.render()
        return xml


@app.route('/', methods=['POST', 'GET'])
def hello_world():
    try:
        if request.method == 'GET':
            print("request.args ", request.args)
            signature = request.args.get("signature", "")
            timestamp = request.args.get("timestamp", "")
            nonce = request.args.get("nonce", "")
            echostr = request.args.get("echostr", "")
            # echostr是微信用来验证服务器的参数，需原样返回
            if echostr:
                try:
                    print('正在验证服务器签名')
                    check_signature(TOKEN, signature, timestamp, nonce)
                    print('验证签名成功')
                    return echostr
                except InvalidSignatureException as e:
                    print('检查签名出错: '.format(e))
                    return 'Check Error'
            else:
                return "nothing"
        # 也可以通过POST与GET来区别
        # 不是在进行服务器验证，而是正常提交用户数据
        elif request.method == 'POST':
            print('接收并处理用户消息')
            xml = handlemsg(request.data)
            return xml
        else:
            pass
    # 处理异常情况或忽略
    except Exception as e:
        print('获取参数失败: '.format(e))


def send_temp_ontime(isfirst, remind_t):
    global mycache, APPID, APPSECRET
    global thread_temp
    thr = threading.current_thread()
    print('current thread ', thr.getName())
    print('current active thread: ', threading.activeCount())
    print('start to send temp', time.asctime(time.localtime((time.time()))))
    if not isfirst and remind_t:
        thr = DbController(func='get_specified_remind_openid', mycache=mycache, remind_time=remind_t)
        thr.start()
        thr.join()
        #### send temp to someone
        openid_set = mycache.get('remind_openid_set')
        if openid_set:
            for oid in openid_set:
                test_temp(oid)
            mylogger.info('sent remind info to %s' % str(openid_set))
        else:
            print('no openid for sending template at ', remind_t)
    mutex.acquire()
    remind_time_list = mycache.get('all_remind_time')
    delta = 60
    remind_time = None
    if remind_time_list:
        dt_now = datetime.datetime.now()
        seconds_now = dt_now.hour * 3600 + dt_now.minute * 60 + dt_now.second
        for i in remind_time_list:
            seconds_temp = i.hour * 3600 + i.minute * 60 + i.second
            delta = seconds_temp - seconds_now
            if delta >= 0:
                remind_time = i
                break
            elif remind_time_list.index(i) + 1 == len(remind_time_list):
                # it is the last one, then clear list and delta to 00:00, the list will be update
                mycache.set('all_remind_time', None)
                delta = 24 * 3600 - seconds_now
                break
            else:
                continue
    else:
        print('warning! there is no all_remind_time in uwsgi cache')
        thd_get = DbController(func='get_all_remind_time', mycache=mycache)
        thd_get.start()
    mutex.release()
    thread_temp = threading.Timer(delta, send_temp_ontime, [False, remind_time])
    thread_temp.start()


def test_temp(openid):
    global mycache
    print('start to temp')
    temp_id = '2a0grjof-d0jLqufeaInT3LZmAIQRLDVO487JH2EsDU'
    data = {
        'touser': openid,
        'template_id': temp_id,
        # 'url': 'http://weixin.qq.com',
        'miniprogram': {
            'appid': 'wx7469bbae33c99a3f',
            'pagepath': 'pages/tabBar/home'
        },
        'topcolor': '#FF0000',
        'data': {
            'first': {
                'value': '舒大夫关爱你的每一天',
                'color': '#173177'
            },
            'keyword1': {
                'value': '中山六院',
                'color': '#003108'
            },
            'keyword2': {
                'value': '结直肠肛门外科',
                'color': '#001179'
            },
            'keyword3': {
                'value': '舒大夫',
                'color': '#009187'
            },
            'remark': {
                'value': '让我们度过愉快的每一天，一起去完成这个小小的问卷吧',
                'color': '#345678'
            }
        }
    }
    print('start to post')
    print(json.dumps(data))
    access_token = mycache.get('access_token')
    print(access_token)
    res = requests.post('https://api.weixin.qq.com/cgi-bin/message/template/send?access_token=%s' % access_token, data=json.dumps(data))
    print(res.text)


def get_token():
    """
    :http请求方式: GET
    https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid=APPID&secret=APPSECRET
    :获取用户 access_token
    :return:
    """
    global APPID, APPSECRET
    url = 'https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid=%s&secret=%s' % (APPID, APPSECRET)
    token_str = requests.get(url).content.decode()

    token_json = json.loads(token_str)
    token = token_json.get('access_token')
    seconds_expire = token_json.get('expires_in')
    return token, seconds_expire


def update_token_ontime():
    global thread_token
    global mycache
    print('start to get access_token: ', time.asctime(time.localtime((time.time()))))
    mutex.acquire()
    access_token, expire_in = get_token()
    mycache.set('access_token', access_token)
    mutex.release()
    mylogger.info('update new access_token')
    print('got new access_token, expire in %s seconds: ' % expire_in)
    thread_token = threading.Timer(expire_in, update_token_ontime)
    thread_token.start()


def handle_tasks_ontime():
    global thread_timer
    time_cur = time.localtime(time.time())
    h_cur = time_cur.tm_hour
    if h_cur == 1:  ## update day on 01:00 everyday
        thread_update_day = DbController(func='update_day_oneday')
        thread_update_day.start()
        print('change the day one day', time_cur)
        mylogger.info('change the day one day')
    if h_cur == 14:  ## clear all need_answer_module
        thread_clear_module = DbController(func='clear_need_answer_module')
        thread_clear_module.start()
        print('clear all the need_answer_module', time_cur)
        mylogger.info('clear all the need_answer_module')
    if h_cur == 7 or h_cur == 19:
        thread_keep_conn = DbController(func='keep_conn_activated')
        thread_keep_conn.start()
        print('keep DB connection activated at ', time_cur)
        mylogger.info('keep DB connection activated')
    thread_timer = threading.Timer(3600, handle_tasks_ontime)
    thread_timer.start()


thread_gettime = DbController(func='get_all_remind_time', mycache=mycache)
thread_token = threading.Timer(1, update_token_ontime)
thread_temp = threading.Timer(10, send_temp_ontime, [True, None])
thread_timer = threading.Timer(3600, handle_tasks_ontime)  ## poll every hour
thread_gettime.start()
thread_token.start()
thread_temp.start()
thread_timer.start()


# # def fuc():
# #     global mycache
# #     time_list = mycache.get('all_remind_time')
# #     print('here time thread ', time_list)
# #     print(type(time.localtime()))
# #     print(type(time_list[0]))
# #     dt_now = datetime.datetime.now()
# #     dt = time_list[0]
# #     delta = (dt.hour * 3600 + dt.minute * 60 + dt.second) - (dt_now.hour * 3600 + dt_now.minute * 60 + dt_now.second)
# #     print('delata= ', delta)
#
#
# t1 = datetime.time(21, 30)
# t = DbController(func='test')
# t.start()
# # thr = threading.Timer(5, fuc)
# # thr.start()
#
# if __name__ == '__main__':
#     app.run(debug=False, host='0.0.0.0', port=PORT)

