import re, time,sqlite3
from nonebot.log import logger
from nonebot.adapters.onebot.v11 import Event
from .config import Configs

def debug(text:str):
    '''
    @说明:
        对官方debug方法的扩写,将文件地址写入debug消息方便查看日志
    @返回:
        none
    '''
    logger.debug('\033[95m' + __name__[12:-6] + '\033[0m | ' + str(text))

def get_mod(event:Event):
    msg = event.get_plaintext()
    if '每天' in msg:
        return 1
    elif '每周' in msg:
        return 2
    elif '每月' in msg:
        return 3
    else:
        return 0

def get_date(event:Event,mod) -> tuple:
    now = time.localtime(time.time())
    year = now.tm_year
    month = now.tm_mon
    day = now.tm_mday
    msg = event.get_plaintext().split('提醒我')[0]
    if '年' in msg:
        yearf = re.findall('(\d*)年',msg)[0]
        if len(yearf) == 2:
            yearf = '20' + yearf
        elif len(yearf) == 4:
            pass
        else:
            debug(f'输入格式错误{yearf}')
        year = yearf
    if '月' in msg:
        if '每月' in msg:
            days = {'一':1,'二':2,'三':3,'四':4,'五':5,'六':6,'七':7,'八':8,'九':9,'十':10}
            monthf = re.findall('每月(.*)号')[0]
            try:
                monthf = int(monthf)
            except ValueError:
                if len(monthf) == 3:
                    monthf = days[monthf[0]] * days[monthf[1]] + days[monthf[2]]
                elif len(monthf) == 2:
                    monthf = days[monthf[0]] + days[monthf[1]]
                elif len(monthf) == 1:
                    monthf = days[monthf[1]]
        else:
            monthf = re.findall('(\d*)月',msg)[0]
        month = monthf
    if '日' in msg:
        dayf = re.findall('(\d*)日',msg)
        if len(dayf) <= 2:
            dayf = '20' + dayf
        else:
            debug(f'输入格式错误{dayf}')
        day = dayf
    if '每周' in msg:
        weekdays = {'一':1,'二':2,'三':3,'四':4,'五':5,'六':6,'天':7,'日':7}
        weekday = re.findall('每周(.)')[0]
        try:
            weekday = int(weekday)
        except ValueError:
            weekday = weekdays[weekday]
        day += now.tm_wday - weekday
    if '明天' in msg:
        day += 1
    if '大后天' in msg:
        day += 3
    elif '后天' in msg:
        day += 2
    return int(year), int(month), int(day)

def get_time(event:Event):
    msg = event.get_plaintext().split('提醒我')[0]
    hour = Configs.morning
    min = 0
    if '上午' in msg or '早上' in msg:
        pass # 默认时间就是早上
    if '下午' in msg:
        hour = Configs.afternoon
    if '中午' in msg:
        hour = Configs.noon
    if '晚上' in msg:
        hour = Configs.night
    hourf = re.findall('(\d+)点',msg)
    if hourf:
        if hour < 12:
            hour = int(hourf[0])
        elif hour >= 12:
            hourf = int(hourf)
            if hourf > hour:
                hour = hourf
            else:
                hour = 12 + hourf
    else:
        pass
    minf = re.findall('(\d+)分',msg)
    if minf:
        min = int(minf[0])
    else:
        pass
    return hour, min

def get_notice(event:Event) -> str:
    notice = event.get_plaintext().split('提醒我')[-1]
    return notice

def get_send_time(year,month,day,hour,minute,mod):
    timef = time.mktime((year,month,day,hour,minute,0,1,48,0))
    if mod == 0:
        timef = str(int(timef)) + '_0_0'
    elif mod == 1:
        timef = str(hour) + '_' + str(hour) + '_' + str(minute)
    elif mod == 2:
        timef = str(time.localtime(timef).tm_wday) + '_' + str(hour) + '_' + str(minute)
    elif mod == 3:
        timef = str(day) + '_' + str(hour) + '_' + str(minute)
    return timef

def check_file():
    try:
        with open('data/database.db','r') as f:
            pass
    except FileNotFoundError:
        a = sqlite3.connect('data/database.db')
        b = a.cursor()
        b.execute('''create table notice(flug text,user_id text,timef text,notice text,mod int)''')
        b.close()
        a.commit()
        a.close()

def add(flug, user_id, timef, notice, mod):
    a = sqlite3.connect('data/database.db')
    b = a.cursor()
    b.execute(f'''insert into notice (flug,user_id,timef,notice,mod) values('{flug}','{user_id}','{timef}','{notice}','{mod}')''')
    b.close()
    a.commit()
    a.close()

def get_time_msg():
    '''
    @说明:
        根据时间查询满足时间条件的
    @返回:
        
    '''
    
    a = sqlite3.connect('data/database.db')
    b = a.cursor()
    b.execute('''select * from notice''')
    notices = dict()
    flugs = list()
    try:
        now = int(time.time())
        content = b.fetchmany()[0]
        while content:
            # debug(content)
            timef = tuple(map(int,content[2].split('_')))
            struct_now = time.localtime(float(now))
            if content[4] == 0:
                if now == timef[0]:
                    insert = {content[1]:content[3]}
                    notices.update(insert)
                    flugs.append(content[0])
            elif content[4] == 1:
                timeCompare = struct_now.tm_hour,struct_now.tm_hour,struct_now.tm_min
                if timeCompare == timef:
                    insert = {content[1]:content[3]}
                    notices.update(insert)
            elif content[4] == 2:
                timeCompare = struct_now.tm_wday,struct_now.tm_hour,struct_now.tm_min
                if timeCompare == timef:
                    insert = {content[1]:content[3]}
                    notices.update(insert)
            elif content[4] == 3:
                timeCompare = struct_now.tm_mday,struct_now.tm_hour,struct_now.tm_min
                if timeCompare == timef:
                    insert = {content[1]:content[3]}
                    notices.update(insert)
            content = b.fetchmany()[0]
    except IndexError:
        pass
    b.close()
    a.commit()
    a.close()
    return notices,flugs

def delete_flug(flugs:list,user_id = '') -> str:
    check_file()
    a = sqlite3.connect('data/database.db')
    b = a.cursor()
    flugs = list(flugs)
    for flug in flugs:
        debug(f'将删除flug:{flug}')
        user_id == 'and user_id = ' + user_id
        sql = f'delete from notice where flug = ?{user_id}'
        b.execute(sql,(f'{flug}',))
    b.close()
    a.commit()
    a.close()
    return '删除成功'

def get_flug_msg(flug,user_id):
    check_file()
    a = sqlite3.connect('data/database.db')
    b = a.cursor()
    sql = 'select * from notice where flug = ? and user_id = ?'
    b.execute(sql,(f'{flug}',f'{user_id}'))
    notice = b.fetchmany()[0][3]
    debug(f'获取flug信息:{notice}')
    b.close()
    a.commit()
    a.close()
    return notice

def get_mod_msg(mod):
    check_file()
    content = dict()
    a = sqlite3.connect('data/database.db')
    b = a.cursor()
    if mod != 4:
        mod = mod % 4
        sql = 'select * from notice where mod = ?'
        b.execute(sql,(f'{mod}',))
    if mod == 4:
        sql = 'select * from notice'
        b.execute(sql)
    notice = b.fetchmany()
    while notice:
        up = {notice[0][0]:notice[0][3]}
        content.update(up)
        debug(f'获取flug信息:{up}')
        notice = b.fetchmany()
    b.close()
    a.commit()
    a.close()
    return content

def get_user_msg(user_id):
    mod_list = ['一次性任务','每日任务','每周任务','每月任务']
    check_file()
    content = dict()
    a = sqlite3.connect('data/database.db')
    b = a.cursor()
    sql = 'select * from notice where user_id = ?'
    b.execute(sql,(f'{user_id}',))
    notice = b.fetchmany()
    debug(notice)
    while notice:
        up = {notice[0][0]:notice[0][3] + mod_list[notice[0][4]]}
        content.update(up)
        debug(f'获取flug信息:{up}')
        notice = b.fetchmany()
    b.close()
    a.commit()
    a.close()
    return content