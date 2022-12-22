# PieBot
高性能go-cqhttp的python开发模板

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
