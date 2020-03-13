import time
import asyncio
import traceback

from aiocqhttp import CQHttp
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from bilibili import monitor
from remind import TimeCommand

bot = CQHttp(api_root='http://127.0.0.1:5700/')

last_time = int(time.time())
sched = AsyncIOScheduler()
str_to_command = TimeCommand()

# 处理私聊消息
@bot.on_message('private')
async def handle_msg(context):
    '''
    接受私聊的定时消息, 如几点提醒我干啥事
    '''
    # 命令解析
    if '帮助' in context['message']:
        return {'reply': str_to_command.help_word}
    if '提醒' not in context['message']:
        return None

    try:
        set_time, item = str_to_command.msg_to_command(context['message'])
    except ValueError as error:
        return {'reply': str(error)}
    except Exception:
        await bot.send({'user_id': '1005982788'}, context['message'])
        await bot.send({'user_id': '1005982788'}, str(traceback.format_exc()))
        return {'reply': '发生错误, 已提交错误报告'}

    sched.add_job(bot.send, 'date', run_date=set_time, args=[
        {'user_id': context['user_id']}, item
    ])

    return {'reply': '好的, 将在{0}提醒您{1}'.format(str(set_time), item)}


async def dynamic_and_live_repost():
    global last_time
    status = await monitor(last_time)

    live_rooms = status['live']
    new_dynamics = status['dynamic']

    if new_dynamics != []:
        for dynamic in new_dynamics:
            await bot.send({'group_id': '905731311'}, dynamic[0]['dynamic'] + '\n' + 'https://t.bilibili.com/'+dynamic[0]['dynamic_id'])

    if live_rooms != []:
        for room in live_rooms:
            try:
                await bot.send({'group_id': '905731311'}, 'https://live.bilibili.com/21672023')
            except Exception:
                traceback.print_exc()

    last_time = int(time.time())
    print(last_time)

sched.add_job(dynamic_and_live_repost, 'interval', seconds=30)

sched.start()
bot.run(host='127.0.0.1', port=8080, loop=asyncio.get_event_loop())
