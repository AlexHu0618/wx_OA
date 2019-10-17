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


def handlemsg(data):
    msg = parse_message(data)
    print(msg)
    global mycache
    mutex.acquire()
    mycache.set('openid', msg.source)
    mutex.release()
    if msg.type == 'text':
        reply = TextReply(content=msg.content, message=msg)
        xml = reply.render()
        return xml
    elif msg.type == 'event':
        if msg.event == 'subscribe':
            reply = TextReply(content="谢谢您的关注，兄dei", message=msg)
            print('user: %s is in' % msg.source)
            thd = DbController(func='add_user_subscribe', openid=msg.source)
            thd.start()
            xml = reply.render()
            return xml
        elif msg.event == 'unsubscribe':
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
            print("try to login")
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
    print('start to send temp', time.asctime(time.localtime((time.time()))))
    if isfirst != 1:
        thr = DbController(func='get_specified_remind_openid', mycache=mycache, remind_time=remind_t)
        thr.start()
        thr.join()
        #### send temp to someone
        openid_set = mycache.get('remind_openid_set')
        if openid_set:
            for oid in openid_set:
                test_temp(oid)
        else:
            print('no openid for sending template at ', remind_t)
    mutex.acquire()
    remind_time_list = mycache.get('all_remind_time')
    delta = 10
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
            else:
                continue
    else:
        print('warning! there is no all_remind_time in uwsgi cache')
        thd_get = DbController(func='get_all_remind_time', mycache=mycache)
        thd_get.start()
    mutex.release()
    thread_temp = threading.Timer(delta, send_temp_ontime, [0, remind_time])
    thread_temp.start()
    # openid = mycache.get('openid')
    # if openid:
    #     test_temp(openid)
    #     print('send temp to user: %s' % openid)
    # else:
    #     client = WeChatClient(APPID, APPSECRET)
    #     for oid in client.user.iter_followers():
    #         if oid != 'oHJc4uCZDoyurNGAJpJ-XAv1KaPA':
    #             test_temp(oid)
    #             print('send temp to user: %s' % oid)
    # mutex.release()
    # thread_temp = threading.Timer(3600, send_temp_ontime)
    # thread_temp.start()


def test_temp(openid):
    global mycache
    print('start to temp')
    temp_id = '2a0grjof-d0jLqufeaInT3LZmAIQRLDVO487JH2EsDU'
    data = {
        'touser': openid,
        'template_id': temp_id,
        'url': 'http://weixin.qq.com',
        # 'miniprogram': {
        #     'appid': 'wx7469bbae33c99a3f',
        #     'pagepath': 'index'
        # },
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
                'value': '内科',
                'color': '#001179'
            },
            'keyword3': {
                'value': '舒大夫',
                'color': '#009187'
            },
            'remark': {
                'value': '让我们度过愉快的每一天，一起完成这个小小的问卷吧',
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
    print('got new access_token, expire in %s seconds: ' % expire_in)
    thread_token = threading.Timer(expire_in, update_token_ontime)
    thread_token.start()


thread_gettime = DbController(func='get_all_remind_time', mycache=mycache)
thread_token = threading.Timer(1, update_token_ontime)
thread_temp = threading.Timer(10, send_temp_ontime, [1, None])
thread_gettime.start()
thread_token.start()
thread_temp.start()

#
# def fuc():
#     global mycache
#     time_list = mycache.get('all_remind_time')
#     print('here time thread ', time_list)
#     print(type(time.localtime()))
#     print(type(time_list[0]))
#     dt_now = datetime.datetime.now()
#     dt = time_list[0]
#     delta = (dt.hour * 3600 + dt.minute * 60 + dt.second) - (dt_now.hour * 3600 + dt_now.minute * 60 + dt_now.second)
#     print('delata= ', delta)
#
#
# t1 = datetime.time(13, 0)
# t = DbController(func='get_specified_remind_openid', mycache=mycache, remind_time=t1)
# t.start()
# # thr = threading.Timer(5, fuc)
# # thr.start()

# if __name__ == '__main__':
#     # app.run(debug=False, host='0.0.0.0', port=PORT)