# encoding=utf-8
############################################################################
#      class.tju.edu.cn 自动选课脚本
#      仅供技术交流，请勿用于真实选课
#      使用方法:
#           将下面的classes中设置好要选的课程代码(每行一个,用逗号隔开)(如信息检索的04761)，然后运行 python fuck_class.py
#           only_query = True 时只会查询是否有课剩余，不会选课，可用于检验软件和课程代码正确性，only_query = False 时会不断刷新课程，在课程出现剩余名额时进行选课
#           输入用户名和密码后登陆
############################################################################
import pdb

import requests
import re
import getpass
import time
from PIL import Image
import six

classes = [
    # '04757',
    # '04758',
    # '04759',
    '04734',
    '04761',
    # '04614'
    # '04762',
]

only_query = False  # 为True时，只查询不选课
delay = .8  # 选课之间的延时， 单位为秒
try_time = 999999  # 总的抢课次数


def color_print(text='', color=0, end='\n'):
    print('\033[1;3%dm' % color, end='')
    print(text, end='')
    print('\033[0m', end=end)


def LoginByPost(username, password):
    headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
        'Host': 'sso.tju.edu.cn',
        'Origin': 'https://sso.tju.edu.cn',
        'Referer': 'https://sso.tju.edu.cn/cas/login?service=http%3A%2F%2Fclasses.tju.edu.cn%2Feams%2FhomeExt.action',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.121 Safari/537.36',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'same-origin',
        'Sec-Fetch-User': '?1',
        'Upgrade-Insecure-Requests': '1',
    }
    # Create a session
    s = requests.session()

    # Get status by GET the login main page
    validation = 'https://sso.tju.edu.cn/cas/login?service=http%3A%2F%2Fclasses.tju.edu.cn%2Feams%2FhomeExt.action'

    res = s.get(validation, stream=True)
    res.encoding = 'utf-8'
    respon = res.text
    # print(respon)

    loginUrl = 'https://sso.tju.edu.cn/cas/login?service=http%3A%2F%2Fclasses.tju.edu.cn%2Feams%2FhomeExt.action'

    pattern = 'name="execution" value="(.*?)"'

    # searching `execution` param by RegEx matching
    a = re.search(pattern, respon)
    if a:
        a = a.group(1)
    execution = a

    # 验证码
    kaptcha = 'https://sso.tju.edu.cn/cas/images/kaptcha.jpg'
    res = s.get(kaptcha, stream=True)
    res.encoding = 'utf-8'
    
    im = Image.open(six.BytesIO(res.content))
    im.show()
    # print(execution)
    # ready for posting data
    captcha = input('请输入验证码: ')

    postData = {'username': username, 'password': password, 'execution': execution, '_eventId': 'submit', 'geolocation=': '', 'captcha': captcha}

    # res.encoding = 'gb2312'

    #########################
    #     登陆的Post请求
    #########################
    rs = s.post(loginUrl, data=postData)

    # print(rs.status_code)
    if rs.status_code != 200:
        if 'Captcha Mismatch' in rs.text:
            color_print('验证码错误', 1)
        else:
            color_print('账号或密码错误', 1)
        return
    color_print('登陆成功', 2)

    electclass_url = 'http://classes.tju.edu.cn/eams/stdElectCourse!defaultPage.action'
    # get一下选课系统
    res = s.get(electclass_url, stream=True)

    time.sleep(1)  # 点击前要sleep 1秒，防止出现`请不要过快点击`
    #########################
    #   点击 ==进入选课==>
    #########################
    postData = {'electionProfile.id': '679'}
    rs = s.post(electclass_url, data=postData)
    if '请不要过快点击' in rs.text:
        color_print('操作频率过快，请调整延迟时间后后重试', 1)
        return
    # 查询系统url
    import json
    time.sleep(1)

    #####################################
    #   查询剩余人数(缓解一下服务器压力^_^)
    #####################################
    class_query_url = 'http://classes.tju.edu.cn/eams/stdElectCourse!queryLesson.action?profileId=679'
    for trys in range(try_time):
        print('正在进行第 %d/%d 次尝试:' % (trys, try_time))
        if len(classes) == 0:
            return
        for c in classes:
            postData = {'lessonNo': c}
            rs = s.post(class_query_url, data=postData)

            # print(rs.text)

            pattern = "id:([0-9]{6}),no:'%s',name:'(.*?)'" % c
            a = re.search(pattern, rs.text)
            if a:
                idx = a.group(1)
                name = a.group(2)
                print('选课id: %s, 课程名称: %s(%s)' % (idx, name, c))

                pattern = "lessonId2Counts={(.*})}"
                a = re.search(pattern, rs.text)
                if a:
                    counts = a.group(1)
                else:
                    color_print('查询课程%s剩余人数时出错，请联系开发人员' % c, 1)
                    return

                counts = '{%s}' % counts
                counts = counts.replace('sc', "'sc'").replace('lc', "'lc'")  # lc是总数 sc是已选的课程数
                counts = counts.replace("'", '"')  # 单引号替换成双引号
                # print(counts)
                counts = json.loads(counts)
                remains = counts[idx]  # {'sc': 90, 'lc': 90}
                remain = remains['lc'] - remains['sc']
                if remain > 0:
                    color_print('  课程已选人数: %d/%d' % (remains['sc'], remains['lc']), 2, end='')
                    ############################
                    #      人数未满 开始选课
                    ############################
                    if only_query:
                        color_print(' (仅查询模式，需要选课将only_query改为False后重试)', 2)

                    else:
                        print()
                        elect_post_url = 'http://classes.tju.edu.cn/eams/stdElectCourse!batchOperator.action?profileId=679'
                        color_print('  正在尝试选课%s...' % c, 3, end='')
                        postData = {'optype': 'true', 'operator0': '%s:true:0' % idx}
                        rs = s.post(elect_post_url, data=postData)
                        if '成功' in rs.text:
                            color_print('  恭喜你！选课成功，课程名称:%s(%s)' % (name, c), 2)
                            classes.remove(c)
                        elif '你已经选过' in rs.text:
                            color_print('  失败:你已经选过%s(%s)' % (name, c), 1)
                            classes.remove(c)
                        elif '冲突' in rs.text:
                            color_print('  选课 %s(%s) 失败: 课程冲突' % (name, c), 1)
                            classes.remove(c)
                        elif '失败' in rs.text:
                            color_print('  失败:课程人数已满，%s(%s)' % (name, c), 1)
                            classes.remove(c)
                        else:
                            print(rs.text)
                            pdb.set_trace()

                        """
                            optype=true&operator0=385449%3Atrue%3A0
                        """

                else:
                    color_print('  课程人数已满: %d/%d' % (remains['sc'], remains['lc']), 1, end='')
                    if only_query:
                        color_print(' (仅查询模式，需要选课将only_query改为False后重试)', 1)
                    else:
                        print()

            else:
                color_print('没有找到课程%s' % c, 1)

            time.sleep(delay)

    return True


if __name__ == '__main__':
    username = input('Enter your username (201*******): ')
    passwd = getpass.getpass("Enter your password: ")
    # username = '2019******'
    # passwd = '666666'
    while True:
        try:
            LoginByPost(username, passwd)
            break
        except:
            color_print('网络异常，延时1分钟后重试...', 1)
            time.sleep(60)
