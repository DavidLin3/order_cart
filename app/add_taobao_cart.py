import time, re
from lxml import etree
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from flask import current_app


def add_taobao_cart(cart_list, cookie):
    '''
    加入淘宝购物车
    '''
    driver = webdriver.Chrome()
    # options = webdriver.ChromeOptions()
    # options.add_argument('--headless')
    # driver = webdriver.Chrome(chrome_options=options)
    driver.maximize_window()
    wait = WebDriverWait(driver, 30)

    driver.get('https://www.taobao.com/')
    for key in cookie:  # 添加cookie
        driver.add_cookie({
            'domain': '.taobao.com',
            'name': key,
            'value': cookie[key],
            'path': '/'
        })

    for item in cart_list:    # 逐个加入购物车
        goods_url, goods_sku1, goods_sku2, quantity = item['goods_url'], item['goods_sku1'], item['goods_sku2'], item['quantity']
        driver.get(goods_url)
        wait.until(EC.presence_of_element_located((By.XPATH, '//*[contains(@id, "Stock")]')))
        html = driver.page_source
        doc = etree.HTML(html)
        goods_sku = [goods_sku1, goods_sku2]
        for item in goods_sku:
            if item:
                data_property = re.split(r':', item)[0]
                sku = re.split(r':', item)[1]
                if len(doc.xpath('//ul[@data-property="{}"]/li'.format(data_property))) != 1:    # 商品属性只有1个时，已自动选中
                    try:
                        sku_matched = wait.until(
                            EC.element_to_be_clickable((By.XPATH, '//ul[@data-property="{0}"]/li//span[text()="{1}"]/..'.format(data_property, sku))))
                        sku_matched.send_keys(Keys.ENTER)
                        time.sleep(0.2)
                    except:
                        current_app.logger.error('无法选中属性', exc_info=True)
        try:
            input = wait.until(
                EC.presence_of_element_located((By.XPATH, '//*[contains(@class, "tb-amount")]//input')))
            input.send_keys(Keys.BACK_SPACE)
            input.send_keys(quantity)
            time.sleep(0.3)
        except:
            current_app.logger.error('无法输入数量', exc_info=True)
        try:
            submit = wait.until(
                EC.element_to_be_clickable((By.XPATH, '//div[contains(@class, "tb-action")]/div[2]/a')))
            submit.send_keys(Keys.ENTER)
            time.sleep(0.2)
        except:
            current_app.logger.error('无法加入购物车', exc_info=True)
        time.sleep(0.5)

    # 跳转至购物车，查询购物车状态
    driver.get('https://cart.taobao.com/')
    wait.until(EC.presence_of_element_located((By.XPATH, '//div[@id="J_OrderList"]')))
    html = driver.page_source
    driver.quit()
    doc = etree.HTML(html)
    order_items = doc.xpath('//div[@id="J_OrderList"]/div')
    order_cart_list = []
    for item in order_items:
        goods_title = item.xpath('.//div[@class="item-basic-info"]/a/text()')[0]
        goods_price = item.xpath('.//em[@class="J_Price price-now"]/text()')[0]
        quantity = item.xpath('.//div[@class="item-amount "]/input/@data-now')[0]
        order_cart_list.append({'goodsTitle': goods_title, 'goodsPrice': goods_price, 'quantity': quantity})

    return order_cart_list

