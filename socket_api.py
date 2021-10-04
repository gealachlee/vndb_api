import socket
import json
import logging
import time
from typing import Optional

lg = logging.getLogger("warning")


class VNDB:
    """
    Class for interacting with the VNDB API
    Example:
    >> vndb = VNDB()
    >> res = vndb.get("get vn basic,details (id = 17)")
    >> print(res)
    {'items': [...], 'more': False, 'num': 1}
    """

    def __init__(self):
        self.sock = socket.socket()
        try:
            self.sock.connect(("api.vndb.org", 19534))
        except Exception as e:
            lg.error(e)
        self._login(
            login_command='login {"protocol":1,"client":"test","clientver":0.1,"username":"ayo",'
                          '"password":"hi-mi-tsu!"}')
        res = self._get_response()
        if res != "ok":
            raise Exception("Not able to login")

    def _login(self, login_command=Optional[str]):
        self._send_command(login_command)

    def _get_response(self):
        finished = False
        whole = ''
        num = 0
        while not finished:  # 通过while循环recv所有信息
            num += 1
            buffer = self.sock.recv(4096)
            try:
                whole += buffer.decode("utf-8")
            except:
                whole += buffer.decode("utf-8", 'ignore')
            if '\x04' in whole or num >= 50:
                finished = True


        whole = whole.replace('\x04', '').strip()

        return whole

    def _send_command(self, cmd, option=True):
        if option is True:
            options = json.dumps({"results": 25, "reverse": False})
            self.sock.send(bytes(f"{cmd}{options}\x04".encode("utf-8")))
        else:
            self.sock.send(bytes(f"{cmd}\x04".encode("utf-8")))

    def dbstat(self):  # 获取"公开的"各类型数据的总量
        """
        :return:dict like {'staff': 22612, 'posts': 0, 'releases': 75452, 'traits': 2855, 'tags': 2632, 'threads': 0,
        'producers': 11217, 'users': 0, 'vn': 29703, 'chars': 93805}
        """
        cmd = f'dbstats'
        self._send_command(cmd, option=False)
        res = self._get_response()
        res = json.loads(' '.join(res.split(' ')[1:]))
        return res

    def get(self, cmd):
        '''
        :param cmd: such as "get vn basic(id = 562)","get vn basic,anime id = [7,11,17]"
        :return: res
        '''
        self._send_command(cmd, option=True)
        res = self._get_response()
        if res.startswith("results"):
            res = res.strip("results")
            res = json.loads(res)  # 默认返回字符串
            res = self.load_all_data(res, cmd, results=25)
            return res

        elif res.startswith("error"):
            res = res.strip("error ")
            res = json.loads(res)
            print(res)
            if res['id'] == 'throttled':
                time.sleep(res['fullwait'])
                self.__init__()
                self._send_command(cmd, option=True)
                res = self._get_response()
                if res.startswith("results"):
                    res = res.strip("results")

                    res = json.loads(res)  # 默认返回字符串
                    res = self.load_all_data(res, cmd, results=25)
                    return res
                else:
                    print("Socket api  -- Unknow error")

    def load_all_data(self, res:dict, cmd:str, results : int =25):
        i = 1
        while res['more'] is True:
            i += 1
            cmd = cmd + json.dumps({"page": i, "results": results})
            print("page=" + str(i))
            self._send_command(cmd)
            res2 = self._get_response().strip("results")
            try:
                res2 = json.loads(res2)
            except:
                print('ERROR')
                print(res2)
                break
            res['more'] = res2['more']
            res['items'].extend(res2['items'])
            res['num'] += res2['num']
            if res2['more'] is False:
                break
            if i > 50:
                check = input("已经收集超过50轮信息,是否继续?(输入1继续)")
                if check != '1':
                    return res
        return res

    def close(self):  # 关闭socket接口
        self.sock.close()

    def _change_user(self, login_command: Optional[str], closelink: Optional[bool]):  # 更改登录vndb的账户
        '''
        :param login_command: vndb账号密码
        :param close: 是否关闭原接口
        '''
        if closelink is True:
            self.close()
            self.sock = socket.socket()
            self.sock.connect(("api.vndb.org", 19534))
        self._login(login_command=login_command)
        res = self._get_response()
        print('change ')
        print(res)
