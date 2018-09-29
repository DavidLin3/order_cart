import time, re
from lxml import etree
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from flask import current_app


def add_t1688_cart(cart_list, cookie):
    '''
    加入1688购物车
    '''
    driver = webdriver.Chrome()
    driver.maximize_window()
    wait = WebDriverWait(driver, 10)
    driver.get('https://www.1688.com/')
    for key in cookie:  # 添加cookie
        driver.add_cookie({
            'domain': '.1688.com',
            'name': key,
            'value': cookie[key],
            'path': '/'
        })

    for item in cart_list:
        goods_url, quantity = item['goods_url'], item['quantity']
        goods_sku1, goods_sku2 = item['goods_sku1'], item['goods_sku2']
        driver.get(goods_url)
        time.sleep(0.3)
        html = driver.page_source
        doc = etree.HTML(html)
        driver.execute_script("window.scrollTo(0, 600)")
        try:    # 显示隐藏的sku
            obj_expand = driver.find_element_by_xpath('//div[@class="obj-sku"]/div[@style="display: block;"]')
            obj_expand.click()
        except:
            pass
        if goods_sku1 and goods_sku2:    # 商品属性1和2都存在的情况
            sku1 = re.split(r'：', goods_sku1, 1)[1]
            sku2 = re.split(r'：', goods_sku2, 1)[1]
            try:
                if len(doc.xpath('//div[@class="obj-leading"]//li')) > 1:
                    sku1_matched = wait.until(
                        EC.element_to_be_clickable((By.XPATH, '//div[@class="obj-leading"]//li//a[@title="{}"]'.format(sku1))))
                    sku1_matched.send_keys(Keys.ENTER)
                try:    # sku2是文字的情况
                    input = wait.until(
                        EC.presence_of_element_located((By.XPATH, '//div[@class="obj-sku"]//td[@class="name"]/span[text()="{}"]/../..//input'.format(sku2))))
                except:    # sku2是图片的情况
                    input = wait.until(
                        EC.presence_of_element_located((By.XPATH, '//div[@class="obj-sku"]//td[@class="name"]/span[@title="{}"]/../..//input'.format(sku2))))
                input.send_keys(Keys.BACK_SPACE)    # 清除原有数据
                input.send_keys(quantity)
                time.sleep(0.2)
            except:
                current_app.logger.error('无法选中属性', exc_info=True)

        elif goods_sku1 and not goods_sku2:    # 商品属性1存在，2不存在的情况
            try:
                sku1 = re.split(r'：', goods_sku1, 1)[1]
                try:    # sku1是文字的情况
                    input = driver.find_element_by_xpath(
                        '//div[@class="obj-sku"]//td[@class="name"]/span[text()="{}"]/../..//input'.format(sku1))
                except:    # sku1是图片的情况
                    input = driver.find_element_by_xpath(
                        '//div[@class="obj-sku"]//td[@class="name"]/span[@title="{}"]/../..//input'.format(sku1))
                input.send_keys(Keys.BACK_SPACE)
                input.send_keys(quantity)
                time.sleep(0.2)
            except:
                current_app.logger.error('无法输入数量', exc_info=True)

        else:    # 商品属性1和2都不存在的情况
            try:
                input = driver.find_element_by_xpath('//div[@class="obj-amount fd-clr"]//input')
                input.send_keys(Keys.BACK_SPACE)
                input.send_keys(quantity)
                time.sleep(0.2)
            except:
                current_app.logger.error('无法输入数量', exc_info=True)

        try:    # 加入进货单
            submit = wait.until(EC.element_to_be_clickable((By.XPATH, '//div[@class="obj-order"]/div[1]/a[2]')))
            submit.send_keys(Keys.ENTER)
            time.sleep(0.5)
        except:
            current_app.logger.error('无法加入购物车', exc_info=True)

    # 跳转至进货单，查询进货单状态
    driver.get('https://cart.1688.com/')
    wait.until(EC.presence_of_element_located((By.XPATH, '//div[@id="active-cart"]')))
    html = driver.page_source
    driver.quit()
    doc = etree.HTML(html)
    order_items = doc.xpath('//div[@id="active-cart"]/div')
    order_cart_list = []
    for item in order_items:
        goods_title = item.xpath('.//div[@class="description text-medium"]/a/text()')[0]
        goods_price = item.xpath('.//span[@class=" effective "]/em/text()')[0]
        quantity = item.xpath('.//span[@class="unit-finecontrol"]/input/@value')[0]
        order_cart_list.append({'goodsTitle': goods_title, 'goodsPrice': goods_price, 'quantity': quantity})

    return order_cart_list