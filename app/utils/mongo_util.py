#!/usr/bin/env python
# -*- coding: utf-8 -*-
from app.utils.conf_util import get_config



class MongoSetting():
    """
    获取mongodb配置信息
    """

    def __init__(self, filename='run.cfg', path=''):
        self.conf = get_config(filename=filename, path=path)

    @property
    def mongo_uri(self):
        return self.conf.get('mongodb', 'MONGO_URI')

    @property
    def mongo_database(self):
        return self.conf.get('mongodb', 'MONGO_DATABASE')

    @property
    def mongo_port(self):
        return self.conf.get('mongodb', 'MONGO_PORT')

    @property
    def history_collection(self):
        return self.conf.get('mongodb', 'HISTORY_COLLECTION')

    @property
    def shop_collection(self):
        return self.conf.get('mongodb', 'SHOP_COLLECTION')

    @property
    def order_collection(self):
        return self.conf.get('mongodb', 'ORDER_COLLECTION')


