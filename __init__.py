import re,time

import nonebot

from .utils import *
from nonebot import on_command, on_regex, get_bot, require, plugin
from nonebot.matcher import Matcher
from nonebot.params import ArgStr, CommandArg
from nonebot.adapters.onebot.v11 import Event

scheduler = require('nonebot_plugin_apscheduler').scheduler

version = 'v1.0'
__plugin_meta__ = plugin.PluginMetadata(
    name=__name__[12:-9],
    description='一个计划提醒插件',
    usage=f'''\
日程提醒{version}
[什么时候]提醒我[提醒事项] (不需要命令提示符) 创建提醒事项
删除 (flug)|删除所有[每天|每周|每月|(无)] 删除任务,不知道flug可以直接发送删除命令,会提示可删除命令
查询任务列表 顾名思义\
''',
    extra={'version':version}
)
pr = 11
setting = on_regex('提醒我',priority=pr,block=True)
@setting.handle()
async def setting_(event:Event):
    mod = get_mod(event)
    year, month, day = get_date(event,mod)
    hour, minute = get_time(event)
    notice = get_notice(event)
    send_time = get_send_time(year=year,month=month,day=day,hour=hour,minute=minute,mod=mod)
    flug = str(int(time.time()))[4:-2]
    user_id = event.get_user_id()
    check_file()
    add(flug=flug, user_id=user_id, timef=send_time, notice=notice, mod=mod)
    await setting.finish('已完成提醒设置,flug为{}'.format(flug))

@scheduler.scheduled_job("cron" , minute = '*/1')
async def found_every_minutes():
    '''
    @说明:
        每隔一分钟检查一次表格是否可以提醒
    @返回:
        无
    '''
    bot = get_bot()
    check_file()
    content,flugs = get_time_msg() # 为{user_id:msg,user_id:msg,......}
    for send in content:
        await bot.call_api( api='send_private_msg',
                            user_id=send,
                            message=content[send])
        delete_flug(flugs = flugs)

delete = on_command('删除',priority=pr,block=True)
@delete.handle()
async def delete_(matcher:Matcher,event:Event,arg = CommandArg()):
    user_id = event.get_user_id()
    if arg:
        flug = re.findall('\d{4}',str(arg))
        if flug:
            send = get_flug_msg(flug[0],user_id)
            if send:
                await matcher.send('任务为:' + str(send))
                matcher.set_arg('flugs',flug[0])
            else:
                await matcher.send('不存在此flug')
                matcher.set_arg('flugs',0)
        else:
            mod = get_mod(event)
            msg = event.get_plaintext()
            if '所有' in msg:
                mod += 4
                # 对应的删除模式:删除每天:1,删除每周:2,删除每月:3,删除所有:4,删除所有每天:5,删除所有每周:6,删除所有每月:7
            content:dict = get_mod_msg(mod=mod) #返回dic:{flug:notice......}
            send = ''
            for key in content:
                send += 'flug:' + key + '\n'
                send += '消息:' + content[key] + '\n\n'
            if send:
                if mod < 4:
                    await matcher.send('有以下任务:\n' + send[:-2])
                else:
                    await matcher.send('将删除以下任务:\n' + send[:-2])
                    flugs = ''
                    for flug in content:
                        flugs += flug + '_'
                    matcher.set_arg('flugs', flugs[:-1])
            else:
                await matcher.send('当前无提醒任务')
    else:
        content = get_user_msg(user_id)
        send = '可删除内容:\n'
        if content:
            for flug in content.keys():
                send += f'flug:{flug}\n内容:{content[flug]}\n\n'
            await matcher.send(send[:-2])
        else:
            await matcher.send('无可删除内容')
            matcher.set_arg('flugs',0)
        pass

@delete.got('flugs','请发送所需删除的flug')
async def _(event:Event,matcher:Matcher,flugs:str = ArgStr('flugs')):
    flugs:list = flugs.split('_')
    user_id = event.get_user_id()
    # print(nonebot.get_driver().config.dict())
    if user_id in nonebot.get_driver().config.dict()['superusers']:
        user_id = ''
    send = delete_flug(flugs,user_id=user_id)
    if flugs[0] != '0':
        await matcher.send(send)

check = on_command('查询任务列表',priority=pr,block=True)
@check.handle()
async def _(event:Event):
    user_id = event.get_user_id()
    content = get_user_msg(user_id=user_id)
    send = str()
    for key in content:
                send += 'flug:' + key + '\n'
                send += '消息:' + content[key] + '\n\n'
    if send:
        await check.finish(f'您的任务列表如下:\n{send[:-2]}')
    else:
        await check.finish('您暂未指定任务')
