# PieBot
高性能go-cqhttp的python开发模板

[Artificial Heaven](https://moeiris.asia/)

# 开始
- need python >= 3.8
- install requirements.txt
    ```bash
    pip install -r requirements.txt
    ```

# 使用方法
```python
import import bot
from obj import Message, group_info, friend_info
# 导入必要库
```

```python
Bot = bot.Bot('ws://127.0.0.1:5700')
# 创建bot对象，以后所有的操作都要使用它
```

```python
@Bot.reg.register('你好')                                         # 注册函数，使用正则匹配
def say_hello(message: Message):
    Bot.send_group_msg(message.group_id, '你好呀')                # 发送群消息，message对象可以取obj.py查看
# 注册函数以供调用
```

```python
Bot.run()
# 启动websocket连接至go-cqhttp
```

# 点歌的例子

需要先运行下述命令，才可以运行本点歌例子。
'''bash
pip install -r requirements.txt
pip install requests
'''

main.py
'''python
import re, requests, json, traceback
import urllib.parse

import bot
from obj import Message, group_info, friend_info

Bot = bot.Bot('ws://127.0.0.1:6700')    # 这里写 正向Websocket 地址
reg = Bot.reg                           # 这是用来简化装饰器的


@reg.register('''点歌 (.*)''')
def diange_(message: Message):
    song = re.match('''点歌 (.*)''', message.message).group(1)
    ret = requests.get(f'http://cloud-music.pl-fe.cn/search?keywords={urllib.parse.quote(song).encode()}&limit=1').text
    data = json.loads(ret)
    try:
        id = data['result']['songs'][0]['id']
        message.reply(f'[CQ:music,type=163,id={id}]')
    except KeyError as e:
        message.reply('坏了，没找到歌曲。')
    except (Exception, BaseException) as e:
        print(traceback.format_exc())


Bot.run()
'''
