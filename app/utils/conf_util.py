#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
from configparser import ConfigParser

BASE_DIR = os.path.dirname(__file__)


def closest_cfg(filename='history.cfg', path='../', prevpath=None):
    """
    return the path  of the closest history.cfg file
    :param filename: default  get file name
    :param path:
    :param prevpath:
    :return:
    """
    if path == prevpath:
        return ''

    path = os.path.abspath(path)
    cfgfile = os.path.join(path, filename)
    if os.path.exists(cfgfile):
        return cfgfile
    return closest_cfg(os.path.dirname(path), path)


def get_config(filename='run.cfg', path=''):
    """
    more about read: https://docs.python.org/3/library/configparser.html
    :param filename:
    :param path:
    :return:
    """
    cfg = ConfigParser()
    path = os.path.join(BASE_DIR, path)
    cfg.read(closest_cfg(filename=filename, path=path))
    return cfg


if __name__ == '__main__':
    cfg = get_config()
    print(cfg.get('mongodb', 'ORDER_COLLECTION'))
