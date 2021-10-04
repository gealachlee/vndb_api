import json
import warnings
import pprint
import os
from socket_api import *
from typing import Optional


# Author : gealach
# Created time :2021/10/2

total_flag_dict = {
    'vn': ['basic', 'details', 'relations', 'staff'],  # extra :'anime','tags', 'stats', 'screens'
    'release': ['basic', 'details', 'vn', 'producers'],
    'producer': ['basic', 'details', 'relations'],
    'character': ['basic', 'details', 'meas', 'traits', 'vns', 'voiced', 'instances'],
    'staff': ['basic', 'details', 'aliases', 'vns', 'voiced'],
    #'quote': ['basic'],
    #'ulist-labels': ['basic'],
    #'votelist': ['basic', 'labels']
}


class TotalData():
    """
    对各类数据类型进行进一步封装,汇总同类型数据
    """

    def __init__(self, typ: Optional[str]):
        self.data = []
        self._typ = typ

    def add(self, data):
        if data:
            self.data.append(data)

    @property
    def typ(self):
        return self._typ

    @typ.setter
    def typ(self, typ):
        if 'typ' not in total_flag_dict.keys():
            raise Exception(f"Type is not in {total_flag_dict.keys()}")
        warnings.warn("If you reset type, you can't use any iter method")
        self._typ = typ

    def getType(self):
        return self.typ

    def getData(self):
        warnings.warn(f"Total data may be too big .Be careful about Memory Error")
        return self.data

    def setData(self, insertid: int, data: dict):
        assert isinstance(insertid, int)
        assert isinstance(data, dict)
        self.add(data=data)

    def get_idList(self):
        idList = []
        for each in self.data:
            idList.append(each['id'])
        return idList

    def __iter__(self):
        for index, value in enumerate(self.data):
            yield value

    def __str__(self):
        return f'Type <-{self.typ}->, includes {self.__len__()} data.'

    def __len__(self):
        return len(self.data)

    def __call__(self, data):
        self.add(data=data)


class Collector():
    def __init__(self, totaldata: Optional[TotalData], flag: Optional[str] = None, filter=None):
        """
        typ: 收集数据的内容形如vn,release,producer,character,staff,quote,user,ulist-labels,ulist
        more details read: https://vndb.org/d11
        """

        self.typ = totaldata.typ
        self.flag = self._setFlag(flag)
        self.filter = self._setFilter(filter)
        self.totaldata = totaldata

    def _setFlag(self, flag=None) -> str:
        if flag is None:
            flags = total_flag_dict.get(self.typ)
            flag_str = ','.join(flags)
            flag = flag_str
        return flag

    def _setFilter(self, filter=None) -> str:
        if filter is None:
            if self.typ == 'votelist' or self.typ == 'ulist-labels':
                filter = '(uid = {})'
            else:
                filter = '(id = {})'
        return filter

    def collect(self, vndb, filter):
        string = f'get {self.getTyp()} {self.flag} {filter}'
        data = vndb.get(string)
        res = data.get('items')
        for perData in res:
            self.totaldata.add(perData)
        pprint.pprint(res)

    def collectAll(self):
        vndb = VNDB()
        recent_id = self.get_recent_id()
        i = 1
        while i <= recent_id:
            if i % 500 == 0:  # 每收集500个数据重新登录一次vndb
                vndb = VNDB()
            idlist = list(range(i, i + 20))
            filter = self.filter.format(idlist)
            self.collect(vndb, filter=filter)
            i = i + 20
            print(i)

    def __iter__(self):
        for each in self.totaldata:
            yield each

    def get_recent_id(self):
        vndb = VNDB()
        result_dict = vndb.dbstat()
        result_dict['release'] = result_dict.pop('releases')  # dbstat()返回的key与type不匹配
        result_dict['producer']=result_dict.pop('producers')
        result_dict['character']=result_dict.pop('chars')
        pprint.pprint(result_dict)
        return result_dict.get(self.getTyp())

    def getTyp(self):
        return self.typ

    def setTyp(self, newTyp):
        warnings.warn('After changing the type, note that the flags(filter) needs to change as you change')
        self.typ = newTyp

    def __str__(self):
        return f'class <Collector> ,collects {self.getTyp()} information'

    def get_keys(self):
        return self.totaldata.keys()


class SaveData:
    def saveID(self):
        raise NotImplementedError

    def saveData(self):
        raise NotImplementedError


class Saver(SaveData):

    def __init__(self, collector: Optional[Collector]):
        self.collector = collector

    def saveID(self, encoding='utf-8', path=None) -> None:
        '''
        :param path: save path ,default: work directory + datetime
        '''
        if path is None:
            path = f"{os.getcwd()}\\{self.collector.typ}_{time.strftime('%Y-%m-%d')}_saveID.txt"
        with open(path, 'a+', encoding=encoding) as f:
            f.write(str(list(self.collector.totaldata.get_idList())))
        f.close()

    def saveData(self, encoding='utf-8', path=None) -> None:
        '''
        :param path: save path ,default: work directory + datetime
        '''
        if path is None:
            path = f"{os.getcwd()}\\{self.collector.typ}_{time.strftime('%Y-%m-%d')}_saveData.txt"
        with open(path, 'a+', encoding=encoding) as f:
            for index, each in enumerate(self.collector.totaldata.data):
                f.write(json.dumps(self.collector.totaldata.data[index]))
        f.close()


if __name__ == "__main__":
    totalData = TotalData(typ='character')
    collector = Collector(totalData)
    collector.collectAll()
    saver = Saver(collector=collector)
    saver.saveData()
