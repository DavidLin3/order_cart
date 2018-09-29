import re, time
from lxml import etree
from selenium import webdriver
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException


def taobao_query(order_list, cookie):
    '''
    查询淘宝商品库存及状态
    :return: 采购单信息列表
    '''
    driver = webdriver.Chrome()
    # option = webdriver.ChromeOptions()
    # option.add_argument('--headless')
    # driver = webdriver.Chrome(chrome_options=option)
    # iframe_wait = WebDriverWait(driver, 0.2)
    driver.maximize_window()
    wait = WebDriverWait(driver, 5)

    driver.get('https://www.taobao.com/')
    for key in cookie:  # 添加cookie
        driver.add_cookie({
            'domain': '.taobao.com',
            'name': key,
            'value': cookie[key],
            'path': '/'
        })

    for order_item in order_list:
        goods_url, goods_sku1, goods_sku2 = order_item['goods_url'], order_item['goods_sku1'], order_item['goods_sku2']
        driver.get(goods_url)
        goods_status = ''
        goods_stock = ''
        # try:    # 处理反爬虫弹窗
        #     iframe_wait.until(EC.presence_of_element_located((By.XPATH, '//iframe[@id="sufei-dialog-content"]')))
        #     driver.switch_to.frame(driver.find_elements_by_tag_name("iframe")[0])
        #     close = wait.until(EC.element_to_be_clickable((By.XPATH, '//div[@class="sufei-dialog-close"]')))
        #     close.send_keys(Keys.ENTER)
        # except:
        #     pass
        try:
            wait.until(EC.presence_of_element_located((By.XPATH, '//*[contains(@id, "Stock")]')))   # 判断商品是否存在
            html = driver.page_source
            doc = etree.HTML(html)

            goods_sku = [goods_sku1, goods_sku2]
            for item in goods_sku:
                if item:
                    try:
                        data_property = re.split(r':', item)[0]
                        sku = re.split(r':', item)[1]
                        if len(doc.xpath('//ul[@data-property="{}"]/li'.format(data_property))) != 1:  # 商品属性只有1个时，已自动选中
                            sku_matched = wait.until(
                                EC.element_to_be_clickable((By.XPATH, '//ul[@data-property="{0}"]/li//span[text()="{1}"]/..'.format(data_property, sku))))
                            sku_matched.send_keys(Keys.ENTER)
                    except:
                        goods_status = '商品属性不存在'
            if goods_status == '':    # 商品属性存在，获取stock
                html = driver.page_source
                doc = etree.HTML(html)
                if doc.xpath('//*[@id="J_SpanStock"]'):
                    goods_stock = doc.xpath('//*[@id="J_SpanStock"]/text()')[0]    # 淘宝
                else:
                    goods_stock = re.search(r"(\d+)", doc.xpath('//*[@id="J_EmStock"]/text()')[0]).group(1)    # 天猫
        except TimeoutException:
            goods_status = '商品已失效'

        order_item['goods_stock'] = goods_stock
        order_item['goods_status'] = goods_status
        order_item['quantity'] = ''
        time.sleep(1)

    driver.quit()
    return order_list




