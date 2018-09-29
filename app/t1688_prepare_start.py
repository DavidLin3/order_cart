#!/usr/bin/env python
# -*- coding: utf-8 -*-
from selenium import webdriver
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from lxml import etree

import sys
sys.path.append('../')
from app.t_redis_queue.queue import RedisClient


def get_login_info():
    option = webdriver.ChromeOptions()
    option.add_argument('--headless')
    driver = webdriver.Chrome(chrome_options=option)
    wait = WebDriverWait(driver, 120)

    login_url = 'https://login.1688.com/member/signin.htm'
    driver.get(login_url)
    driver.switch_to.frame(driver.find_elements_by_tag_name("iframe")[0])  # 切换到第1个iframe结构中

    # 获取二维码
    try:
        wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="J_QRCodeImg"]/img')))
    except TimeoutException:
        driver.quit()
        return

    html = driver.page_source
    result = etree.HTML(html)
    img = 'https:' + result.xpath('//*[@id="J_QRCodeImg"]/img/@src')[0]
    RedisClient(db=1).push_QR(img)  # 放入列表消息队列

    # 获取登录的会员名
    try:
        wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="alibar"]/div[1]/div[2]/ul/li[1]/div[1]/span/a')))
        nick = driver.find_element_by_xpath('//*[@id="alibar"]/div[1]/div[2]/ul/li[1]/div[1]/span/a').text
    except TimeoutException:
        driver.quit()
        return

    origin_cookies = driver.get_cookies()
    driver.quit()

    cookie = {}
    for single_cookie in origin_cookies:
        cookie[single_cookie['name']] = single_cookie['value']

    if nick and cookie:
        info_dict = {'nick': nick,
                     'cookie': cookie}
        RedisClient(db=1).push_login_info(img, info_dict)  # 放入键值对消息队列
    else:
        print('error! not get login info!')


if __name__ == '__main__':
    get_login_info()
