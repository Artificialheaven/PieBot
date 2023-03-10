import threading
import time
import websockets
import json
import asyncio
import uuid
import traceback
import obj
import re


class reg:
    reg_list = {
        'apps': [
            # {'re': '(.*)', 'func': <function func at 0x0000000000000000>}
        ],
        'notice': [
            # {'func': <function func at 0x0000000000000000>}
        ],
        'noticeApps': [
            # {'type': 'poke', 'func': <function func at 0x0000000000000000>}
        ],
        'request': [
            # {'func': <function func at 0x0000000000000000>}
        ],
        'requestApps': [
            # {'type': 'poke', 'func': <function func at 0x0000000000000000>}
        ],
        'msgApp': [
            # {'func': <function func at 0x0000000000000000>}
        ]
    }

    def register(self, func_tri):
        def wapper(func):
            def _wapper(*args, **kwargs):
                return func(*args, **kwargs)  # 实际上不会被调用，运行不到这一步

            self.reg_list['apps'].append({'re': func_tri, 'func': func})
            return _wapper

        return wapper

    def registerNotice(self, func):
        def wapper(*args, **kwargs):
            return func(*args, **kwargs)  # 实际上不会被调用，运行不到这一步

        self.reg_list['notice'].append({'func': func})
        return wapper

    def registerNoticeApp(self, notice_type):
        def wapper(func):
            def _wapper(*args, **kwargs):
                return func(*args, **kwargs)  # 实际上不会被调用，运行不到这一步

            self.reg_list['noticeApps'].append({'type': notice_type, 'func': func})
            return _wapper

        return wapper

    def registerRequest(self, func):
        def wapper(*args, **kwargs):
            return func(*args, **kwargs)  # 实际上不会被调用，运行不到这一步

        self.reg_list['request'].append({'func': func})
        return wapper

    def registerRequestApp(self, notice_type):
        def wapper(func):
            def _wapper(*args, **kwargs):
                return func(*args, **kwargs)  # 实际上不会被调用，运行不到这一步

            self.reg_list['requestApps'].append({'type': notice_type, 'func': func})
            return _wapper

        return wapper


class Bot:
    ws_url = 'ws://127.0.0.1:6700'
    bot = {
        'id': 10001,
        'name': 'Bot',
    }
    msg = {}
    logger = obj.logger()
    revc_api = {}
    group_list = {}
    friend_list = {}

    def __init__(self, ws_url):
        self.recv_api = {}
        self.reg = reg()
        self.ws_url = ws_url

    def run(self):
        self._run()

    def _run(self):
        try:
            self.loop = asyncio.get_event_loop()
            t = self.loop.create_task(self._runWebsocket())
            self.loop.run_until_complete(t)
            # self.loop.run_forever()
        except KeyboardInterrupt as kb:
            self.logger.info('Shutting Down!')
            self.logger.__del__()

    def stop(self):
        self.loop.stop()

    async def _runWebsocket(self):
        while True:
            async with websockets.connect(self.ws_url) as self.ws:
                threading.Thread(target=self._Bot_init).start()
                while True:
                    try:
                        res = await self.ws.recv()
                        threading.Thread(target=self._jsonParse, args=(res,)).start()  # 多线程防止堵塞
                    except (Exception, BaseException) as e:
                        print(traceback.format_exc())
                        time.sleep(5)

    async def _sendWebsocket(self, data):
        await self.ws.send(data)

    def _Bot_init(self):
        def get_group_list():  # get_group_list
            id = f'{uuid.uuid1()}'
            data = {'action': 'get_group_list', 'params': {}, 'echo': id}
            ret = self._send_data(data, id)
            gl = ret['data']
            for i in gl:
                gi = obj.group_info(
                    id=i['group_id'],
                    name=i['group_name'],
                    create_time=i['group_create_time'],
                    level=i['group_level'],
                    member_count=i['member_count'],
                    max_member_count=i['max_member_count']
                )
                self.group_list[i['group_id']] = gi
            self.logger.info(f'获取到群列表，共 {len(self.group_list)} 个。')

        def get_friend_list():
            id = f'{uuid.uuid1()}'
            data = {'action': 'get_friend_list', 'params': {}, 'echo': id}
            ret = self._send_data(data, id)
            fl = ret['data']
            for i in fl:
                fi = obj.friend_info(
                    id=i['user_id'],
                    name=i['nickname'],
                    remark=i['remark']
                )
                self.friend_list[i['user_id']] = fi
            self.logger.info(f'获取到好友列表，共 {len(self.friend_list)} 个。')

        def get_gocq_ver():
            id = f'{uuid.uuid1()}'
            data = {'action': 'get_version_info', 'params': {}, 'echo': id}
            ret = self._send_data(data, id)
            self.logger.info('当前使用GO-CQHTTP版本：' + ret['data']['app_version'])

        self.logger.info('Bot.py开始初始化期间功能可能不完整。')
        get_gocq_ver()
        get_group_list()
        get_friend_list()

        # 以下是初始化代码
        self.logger.info('Bot.py初始化完成。')

    def _jsonParse(self, t):
        # 事件分拣
        try:
            js = json.loads(t)
            if 'echo' in js:
                # 回声，API响应数据
                self._ret_api(js['echo'], js)
                return
            post_type = js['post_type']
            self.bot[id] = int(js['self_id'])
            if post_type == 'message':  # 消息事件
                self._message(js)
            if post_type == 'request':
                self._request(js)
            if post_type == 'notice':
                self._notice(js)
            if post_type == 'meta_event':
                self._meta(js)
        except (Exception, BaseException) as e:
            print(traceback.format_exc())
            time.sleep(5)

    def _ret_api(self, echo, js):
        self.recv_api[echo] = {'recv': True, 'data': js['data']}

    def _message(self, js: dict):
        msg_type = js['message_type']
        if msg_type == 'private':
            self.logger.info(
                f'收到好友 {js["sender"]["nickname"]}({js["sender"]["user_id"]}) 的消息： {js["message"]} ({js["message_id"]})')
            _sender = obj.sender(
                user_id=js["sender"]["user_id"],
                nickname=js["sender"]['nickname'],
                sex=js["sender"]['sex'],
                age=js["sender"]['age'],
                card=js["sender"]['card'],
                area=js["sender"]['area'],
                level=js["sender"]['level'],
                role=js["sender"]['role'],
                title=js["sender"]['title']
            )
            message = obj.Message(
                send_time=js['time'],
                self_id=js['self_id'],
                message_type=js['message_type'],
                sub_type=js['sub_type'],
                message_id=js['message_id'],
                user_id=js['user_id'],
                message=js['message'],
                raw_message=js['raw_message'],
                font=js['font'],
                sender=_sender,
                reply=self.send_private_msg
            )
            self.msg[js['message_id']] = message
            for i in self.reg.reg_list['apps']:
                if re.match(i['re'], js["message"]):
                    i['func'](message)
        if msg_type == 'group':
            self.logger.info(
                f'收到群 {self.group_list[js["group_id"]].name}({js["group_id"]}) 内 {js["sender"]["nickname"]}({js["sender"]["user_id"]}) 的消息： {js["message"]} ({js["message_id"]})')
            _sender = obj.sender(
                user_id=js["sender"]["user_id"],
                nickname=js["sender"]['nickname'],
                sex=js["sender"]['sex'],
                age=js["sender"]['age'],
                card=js["sender"]['card'],
                area=js["sender"]['area'],
                level=js["sender"]['level'],
                role=js["sender"]['role'],
                title=js["sender"]['title']
            )
            message = obj.Message(
                send_time=js['time'],
                self_id=js['self_id'],
                group_id=js["group_id"],
                message_type=js['message_type'],
                sub_type=js['sub_type'],
                message_id=js['message_id'],
                user_id=js['user_id'],
                message=js['message'],
                raw_message=js['raw_message'],
                font=js['font'],
                sender=_sender,
                reply=self.send_group_msg
            )
            self.msg[js['message_id']] = message
            for i in self.reg.reg_list['apps']:
                if re.match(i['re'], js["message"]):
                    i['func'](message)

    def _notice(self, js: dict):
        if js['notice_type'] == 'friend_recall':
            # 私聊消息撤回
            self.logger.info(
                f'好友 {js["user_id"]} 撤回了消息：{self.msg[js["message_id"]].message} ({js["message_id"]})')
        if js['notice_type'] == 'group_recall':
            # 群聊消息撤回
            self.logger.info(
                f'{js["user_id"]} 在群 {self.group_list[js["group_id"]].name}({js["group_id"]}) 撤回了消息：'
                f'{self.msg[js["message_id"]].message} ({js["message_id"]})')
        if js['notice_type'] == 'group_increase':
            # 群成员增加
            if js['sub_type'] == 'approve':
                self.logger.info(f'管理员 {js["operator_id"]} 已同意 {js["user_id"]} 加入群 '
                                 f'{self.group_list[js["group_id"]].name}({js["group_id"]})')
            elif js['sub_type'] == 'invite':
                self.logger.info(f'管理员 {js["operator_id"]} 邀请 {js["user_id"]} 加入群 '
                                 f'{self.group_list[js["group_id"]].name}({js["group_id"]})')
        if js['notice_type'] == 'group_decrease':
            # 群成员减少
            if js['sub_type'] == 'leave':
                self.logger.info(f'成员 {js["user_id"]} 离开群 '
                                 f'{self.group_list[js["group_id"]].name}({js["group_id"]})')
            if js['sub_type'] == 'kick':
                self.logger.info(f'管理员 {js["operator_id"]} 将 {js["user_id"]} 踢出群 '
                                 f'{self.group_list[js["group_id"]].name}({js["group_id"]})')
            if js['sub_type'] == 'kick_me':
                self.logger.warn(f'管理员 {js["operator_id"]} 将 自己{js["user_id"]} 踢出群 '
                                 f'{self.group_list[js["group_id"]].name}({js["group_id"]})')
        if js['notice_type'] == 'group_admin':
            # 群管理变动
            if js['sub_type'] == 'set':
                self.logger.info(f'{js["user_id"]} 成为群 '
                                 f'{self.group_list[js["group_id"]].name}({js["group_id"]}) 的管理员')
            if js['sub_type'] == 'unset':
                self.logger.info(f'{js["user_id"]} 被取消群 '
                                 f'{self.group_list[js["group_id"]].name}({js["group_id"]}) 的管理员')
        if js['notice_type'] == 'group_upload':
            # 群文件上传
            self.logger.info(f'{js["user_id"]} 在群 {self.group_list[js["group_id"]].name}({js["group_id"]}) 上传文件 '
                             f'file={js["file"]}')
        if js['notice_type'] == 'group_ban':
            # 群禁言
            if js["user_id"] == 0:
                self.logger.info(f'群 {self.group_list[js["group_id"]].name}({js["group_id"]}) 开启全群禁言 '
                                 f'，操作人{js["operator_id"]} ({js["duration"]})')
            else:
                self.logger.info(
                    f'{js["user_id"]} 在群 {self.group_list[js["group_id"]].name}({js["group_id"]}) 被禁言 '
                    f'{js["duration"]}秒，操作人{js["operator_id"]}')
        if js['notice_type'] == 'friend_add	':
            # 好友已添加
            self.logger.info(f'{js["user_id"]} 已添加为好友。')
        if js['notice_type'] == 'poke':
            # 戳一戳（群内&好友）
            if len(js) == 8:  # 好友
                self.logger.info(f'{js["user_id"]} 戳了戳自己({js["target_id"]})')
            else:
                self.logger.info(
                    f'{js["user_id"]} 在群 {self.group_list[js["group_id"]].name}({js["group_id"]}) 戳了戳 '
                    f'{js["target_id"]}')
        if js['notice_type'] == 'lucky_king':
            # 群红包运气王提示
            self.logger.info(f'{js["user_id"]} 在群 {self.group_list[js["group_id"]].name}({js["group_id"]}) 发送的红包'
                             f'的运气王为 {js["target_id"]}')
        if js['notice_type'] == 'honor':
            # 群成员荣誉变更提示
            if js['honor_type'] == 'talkative':
                self.logger.info(f'{js["user_id"]} 在群 {self.group_list[js["group_id"]].name}({js["group_id"]}) 成为'
                                 f'龙王')
            if js['honor_type'] == 'performer':
                self.logger.info(f'{js["user_id"]} 在群 {self.group_list[js["group_id"]].name}({js["group_id"]}) 获得'
                                 f'群聊之火')
            if js['honor_type'] == 'emotion':
                self.logger.info(f'{js["user_id"]} 在群 {self.group_list[js["group_id"]].name}({js["group_id"]}) 获得'
                                 f'快乐源泉')
        if js['notice_type'] == 'title':
            # 群成员头衔变更
            self.logger.info(f'{js["user_id"]} 在群 {self.group_list[js["group_id"]].name}({js["group_id"]}) 获得头衔'
                             f'{js["title"]}')
        if js['notice_type'] == 'group_card':
            # 群成员名片更新
            self.logger.info(f'{js["user_id"]} 在群 {self.group_list[js["group_id"]].name}({js["group_id"]}) 更新群名片'
                             f'从 {js["card"]}')
        if js['notice_type'] == 'offline_file':
            # 接收到离线文件
            self.logger.info(f'{js["user_id"]} 在群 {self.group_list[js["group_id"]].name}({js["group_id"]}) 上传文件 '
                             f'url={js["url"]}')
        if js['notice_type'] == 'client_status':
            # 其他客户端在线状态变更
            if js['online']:
                self.logger.info(f'账号在{js["device_name"]}({js["device_kind"]}) 上登陆。')
            else:
                self.logger.info(f'账号在{js["device_name"]}({js["device_kind"]}) 上登陆。')
        if js['notice_type'] == 'essence':
            # 精华消息变更
            if js["sub_type"] == 'add':
                self.logger.info(
                    f'{js["operator_id"]} 在群 {self.group_list[js["group_id"]].name}({js["group_id"]}) 设置'
                    f'精华消息= {js["message_id"]}')
            else:
                self.logger.info(
                    f'{js["operator_id"]} 在群 {self.group_list[js["group_id"]].name}({js["group_id"]}) 取消'
                    f'精华消息= {js["message_id"]}')

        if len(self.reg.reg_list['notice']) > 0:
            for i in self.reg.reg_list['notice']:
                i['func'](js)
        if len(self.reg.reg_list['noticeApps']) > 0:
            for i in self.reg.reg_list['noticeApps']:
                if js['notice_type'] == i['type']:
                    i['func'](js)

    def _request(self, js: dict):
        if js['request_type'] == 'friend':
            request = obj.Request(
                user_id=js['user_id'],
                comment=js['comment'],
                flag=js['flag'],
                reply=self.set_friend_add_request,
                n_type='friend')
            for i in self.reg.reg_list['request']:
                i['func'](request)
            self.logger.info(f'{js["user_id"]} 想添加您为好友。')
        if js['request_type'] == 'group':
            request = obj.Request(
                group_id=js['group_id'],
                sub_type=js['sub_type'],
                user_id=js['user_id'],
                comment=js['comment'],
                flag=js['flag'],
                reply=self.set_group_add_request,
                n_type='group')
            if js['sub_type'] == 'add':
                self.logger.info(f'{js["user_id"]} 想加入群 {self.group_list[js["group_id"]].name}({js["group_id"]})。')
            elif js['sub_type'] == 'invite':
                self.logger.info(
                    f'{js["user_id"]} 想邀请自己加入群 {self.group_list[js["group_id"]].name}({js["group_id"]})。')
            for i in self.reg.reg_list['request']:
                i['func'](request)

    def _meta(self, js: dict):
        self.logger.debug(f'收到meta：{js}')

    def _send_data(self, data, id):
        # 发包，取响应数据
        asyncio.run(self._sendWebsocket(json.dumps(data)))
        while True:
            if id in self.recv_api:
                ret = self.recv_api[id]
                del self.recv_api[id]
                return ret

    def _send_data_no_ret(self, data):
        # 发包，没有响应
        asyncio.run(self._sendWebsocket(json.dumps(data)))

    def send_data(self, data: dict):
        # 发包，取响应数据
        id = f'{uuid.uuid1()}'
        if "echo" in data:
            id = data["echo"]
        else:
            data["echo"] = id
        asyncio.run(self._sendWebsocket(json.dumps(data)))
        while True:
            if id in self.recv_api:
                ret = self.recv_api[id]
                del self.recv_api[id]
                return ret

    def send_group_msg(self, group_id, message):
        id = f'{uuid.uuid1()}'
        sdata = {'action': 'send_group_msg', 'params': {'group_id': int(group_id), 'message': message}, 'echo': id}
        return self._send_data(sdata, id)

    def send_private_msg(self, user_id, message):
        id = f'{uuid.uuid1()}'
        sdata = {'action': 'send_private_msg', 'params': {'user_id': int(user_id), 'message': message}, 'echo': id}
        return self._send_data(sdata, id)

    def send_msg(self, user_id: int = None, group_id: int = None, message_type: str = None, message=None):
        if not message_type:
            if group_id: message_type = 'group'
            if user_id: message_type = 'private'
            if not group_id and not user_id: return None
        if message_type == 'group':
            return self.send_group_msg(group_id, message)
        else:
            return self.send_private_msg(user_id, message)

    def delete_msg(self, message_id):
        id = f'{uuid.uuid1()}'
        sdata = {'action': 'delete_msg', 'params': {'message_id': int(message_id)}, 'echo': id}
        return self._send_data(sdata, id)

    def mark_msg_as_read(self, message_id):
        id = f'{uuid.uuid1()}'
        sdata = {'action': 'mark_msg_as_read', 'params': {'message_id': int(message_id)}, 'echo': id}
        return self._send_data(sdata, id)

    def set_group_kick(self, group_id, user_id, reject_add_request=False):
        id = f'{uuid.uuid1()}'
        sdata = {'action': 'set_group_kick', 'params': {'group_id': int(group_id), 'user_id': int(user_id),
                                                        'reject_add_request': reject_add_request}, 'echo': id}
        return self._send_data(sdata, id)

    def set_group_ban(self, group_id, user_id, duration):
        id = f'{uuid.uuid1()}'
        sdata = {'action': 'set_group_ban',
                 'params': {'group_id': int(group_id), 'user_id': int(user_id), 'duration': duration}, 'echo': id}
        return self._send_data(sdata, id)

    def get_group_info(self, group_id) -> obj.group_info:
        return self.group_list[int(group_id)]

    def get_friend_info(self, user_id) -> obj.friend_info:
        return self.friend_list[int(user_id)]

    def set_group_whole_ban(self, group_id, enable):
        sdata = {'action': 'set_group_whole_ban',
                 'params': {'group_id': int(group_id), 'enable': enable}}
        self._send_data_no_ret(sdata)

    def set_group_admin(self, group_id, user_id, enable):
        sdata = {'action': 'set_group_admin',
                 'params': {'group_id': int(group_id), 'user_id': user_id, 'enable': enable}}
        self._send_data_no_ret(sdata)

    def set_group_card(self, group_id, user_id, card):
        sdata = {'action': 'set_group_card',
                 'params': {'group_id': int(group_id), 'user_id': user_id, 'card': card}}
        self._send_data_no_ret(sdata)

    def set_group_name(self, group_id, group_name):
        sdata = {'action': 'set_group_card',
                 'params': {'group_id': int(group_id), 'group_name': group_name}}
        self._send_data_no_ret(sdata)

    def set_group_leave(self, group_id, is_dismiss=False):
        sdata = {'action': 'set_group_leave',
                 'params': {'group_id': int(group_id), 'is_dismiss': is_dismiss}}
        self._send_data_no_ret(sdata)

    def set_group_special_title(self, group_id, user_id, special_title):
        sdata = {'action': 'set_group_special_title',
                 'params': {'group_id': int(group_id), 'user_id': user_id, 'special_title': special_title}}
        self._send_data_no_ret(sdata)

    def send_group_sign(self, group_id):
        sdata = {'action': 'send_group_sign',
                 'params': {'group_id': int(group_id)}}
        self._send_data_no_ret(sdata)

    def set_friend_add_request(self, flag, approve=True, remark=""):
        sdata = {'action': 'set_friend_add_request',
                 'params': {'flag': flag, 'approve': approve, 'remark': remark}}
        self._send_data_no_ret(sdata)

    def set_group_add_request(self, flag, sub_type, approve=True, reason=""):
        sdata = {'action': 'set_group_add_request',
                 'params': {'flag': flag, 'sub_type': sub_type, 'approve': approve, 'reason': reason}}
        self._send_data_no_ret(sdata)


if __name__ == '__main__':
    Bot = Bot('ws://127.0.0.1:6700')
    Bot.run()
    while True:
        cmd = input()
        if cmd == 'exit':
            exit()
        if cmd[0:6] == 'group:' or cmd[0:6] == 'Group:':
            _cmd = cmd.split(' ')
            id = _cmd[0].replace(cmd[0:6], '')
            print('return=>', Bot.send_group_msg(id, _cmd[1]))
        if cmd[0:8] == 'private:' or cmd[0:8] == 'Private:':
            _cmd = cmd.split(' ')
            print(_cmd)
            id = _cmd[0].replace(cmd[0:8], '')
            print('return=>', Bot.send_private_msg(id, _cmd[1]))
