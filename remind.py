import datetime
import re
from typing import Callable


# 中文描述的日期
_date_ch = r"[今明后]天"
# 中文描述的时段
_front_time_ch = r"([上中下]午)|([早晚]上)|(凌晨)"
# 中文描述的时间
_time_ch = r"(\d{1,2}点)+(\d{1,2}分+)?"

# 时间戳格式的日期
_date_ts = r"\d{1,2},\d{1,2}"
# 时间戳格式的时间
_time_ts = r"\d{1,2}:\d{1,2}"

# 日期
_date = r"(%s)|(%s)" % (_date_ch, _date_ts)
# 时间
_time = r"(%s)|(%s)" % (_time_ch, _time_ts)
# 时间格式检查
_re_check = r"(%s)? ?(%s)? ?(%s)" % (_date, _front_time_ch, _time)

_re_check = re.compile(_re_check)

# 检查时间范围是否正确
check_time = {
    '凌晨': lambda set_time: set_time in range(0,  7),
    '早上': lambda set_time: set_time in range(4,  11),
    '上午': lambda set_time: set_time in range(0,  13),
    '中午': lambda set_time: set_time in range(10, 15),
    '下午': lambda set_time: set_time in range(12, 24),
    '晚上': lambda set_time: set_time in range(17, 24),
    None: lambda set_time: True
}

help_word = '''
指令格式为: 时间 + 提醒 + 事件

    时间最多可以有 3 个片段: 日期 + 上下午/早晚上/凌晨 + 时间
        日期可以是中文形式的: 今/明/后天
            也可以是数字形式的: 04,08

        使用 12 小时描述时间段时, 不可使用 24 小时制描述具体时间
            即: 下午20:00 是非法的时间描述

        时间可以是中文形式的: 9点10分 / 9点
            也可以是数字形式的: 9:10

    日期 和 上下午 是可选的, 3 个片段之间可以使用空格隔开
        中文和数字形式的时间描述可以混用
        例: 今天晚上9:00提醒我去取快递

    提醒关键词必须有, 否则此定时任务不生效
    事件无要求, 随意写
'''


class TimeCommand(object):

    def __init__(self):
        '''
        在 check_set_time 之后都是 str, parse_* 之后为转换尾对应数据
        '''
        self.help_word = help_word

    def check_set_time(self, _set_time: str) -> Callable:
        '''
        检查提取出来的 set_time 格式是否符合规范, 此处还应该检查时间是否正确
        '''
        match_res = _re_check.match(_set_time)
        if match_res and _set_time == match_res.group(0):
            return match_res
        else:
            raise ValueError("Non-standard format! Please send '帮助' for help!")

    def set_time_datetime(self, _set_time: str) -> Callable:
        '''
        从匹配结果里提取出 datetime()
        '''
        date_time = self.check_set_time(_set_time)
        _date = date_time.group(1)
        _front_time_ch = date_time.group(4)
        _time = date_time.group(8)

        date = self.parse_date(_date) or datetime.datetime.now().date()
        times = self.parse_time(_time, _front_time_ch)

        if times:
            return datetime.datetime.combine(date, times)
        else:
            raise ValueError('请不要混合使用12小时制和24小时制描述时间')

    def parse_date(self, _date: str) -> Callable:
        '''
        将 _date_ch / _date_ts 形式的字符串转换成 datetime.date()
        '''
        if not isinstance(_date, str):
            return None
        today = datetime.date.today()

        # 如果时间是 _date_ts 格式的 --,--
        if ',' in _date:
            date = [int(num) for num in _date.split(',')]
            date = today.replace(month=date[0], day=date[-1])

            if date >= today:
                return date
            else:
                return None

        # 如果时间是 _date_ch : 今天/明天/后天
        if _date == '今天':
            date = today
        elif _date == '明天':
            date = today.replace(day=today.day + 1)
        elif _date == '后天':
            date = today.replace(day=today.day + 2)

        return date

    def parse_time(self, _time: str,  _front_time_ch: str = None) -> Callable:
        '''
        将 _time_ch / _time_ts 形式的字符串转换成 datetime.time()
        若 time 不正确, 如 下午13点 之类的, 将返回错误
        '''
        # 提取 _time_ts 格式的时间, --:--
        if not isinstance(_time, str):
            return None

        if ':' in _time:
            times = [int(num) for num in _time.split(':')]
            times = datetime.time(times[0], times[-1])

        # 提取 _time_ch 格式的时间, *点*分 / *点
        if '点' in _time:
            times = [int(num) for num in re.findall(r"\d{1,2}", _time)]
            if len(times) == 2:
                times = datetime.time(times[0], times[-1])
            else:
                times = datetime.time(times[0])

        # 对于上午和中午 12 点之前的时间不进行 +12 操作
        if _front_time_ch and _front_time_ch not in ['凌晨', '早上', '上午']:
            if _front_time_ch == '中午' and times.hour > 10 and times.hour <= 12:
                pass
            else:
                try:
                    times = times.replace(hour=times.hour + 12)
                except ValueError:
                    return None

        # 此处 check 时间范围, 凌晨, 早上, 上午, 中午, 下午, 晚上 的时间范围是否正确
        if check_time[_front_time_ch](times.hour):
            return times
        else:
            return None

    def msg_to_command(self, message: str) -> tuple:
        '''
        必须包含关键词: 提醒

        将自然语句, 处理成命令格式 (set_time:datetime(), item:str), 并返回
        命令语句一般是: 时间 + 提醒 + 事件
        eg: 
            今天下午三点提醒我取快递 -> (datetime(year, month, day, 15), "取快递")

        时间有: 今/明/后 天 + 上/下/中 午 (晚上) + *点*分 /
            上中下午/ 晚 + *点*分 /
            *点*分
        也可以直接是一个时间戳 2019.06.01 19:35 / 06.01 18:00 / 18:00
        '''
        msg = message.split('提醒')
        set_time = msg[0]
        item = msg[-1]
        set_time = self.set_time_datetime(set_time)
        item = self.parse_item(item)

        if set_time >= datetime.datetime.now():
            return (set_time, item)
        else:
            raise ValueError("设置的时间必须在此刻之后!")

    def parse_item(self, item: str) -> str:
        '''
        对 item 内容的提取
        '''
        if item[0] == '我':
            return item[1:]
        else:
            return item


if __name__ == "__main__":
    test = TimeCommand()
    while True:
        times = input()
        print(test.msg_to_command(times))
