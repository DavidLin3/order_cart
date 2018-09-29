import redis
import os
from configparser import ConfigParser

BASE_DIR = os.path.dirname(__file__)


class RedisClient(object):
    def __init__(self, db=0):
        cfg = self.__get_config()
        host = cfg.get('redis', 'REDIS_HOST')
        port = cfg.get('redis', 'REDIS_PORT')
        self.db = redis.Redis(host=host, port=port, db=db)

        # 获取默认爬虫订单的周期时间
        self.default_time = cfg.get('settings', 'DEFAULT_TIME')

    def push_QR(self, img):
        self.db.rpush('QR', img)

    def pop_QR(self):
        return self.db.lpop('QR')

    # 存放user_login_info
    # {'nick':'', 'cookie':''}
    # user_login_info  type:dict
    def push_login_info(self, img, user_login_info):
        self.db.set(img, str(user_login_info))

    # return type:dict
    def get_login_info_by_img(self, img):
        str_img = self.db.get(img)
        if str_img is not None:
            return eval(bytes.decode(str_img))

    def __get_config(self, filename='run.cfg', path='../'):
        cfg = ConfigParser()
        path = os.path.join(BASE_DIR, path)
        cfg.read(self.__closest_cfg(filename=filename, path=path))
        return cfg

    def __closest_cfg(self, filename='run.cfg', path='.', prevpath=None):
        if path == prevpath:
            return ''

        path = os.path.abspath(path)
        cfgfile = os.path.join(path, filename)
        if os.path.exists(cfgfile):
            return cfgfile
        return self.__closest_cfg(os.path.dirname(path), path)
