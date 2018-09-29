import re, time
from lxml import etree
from selenium import webdriver
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException


def t1688_query(order_list, cookie):
    '''
    查询1688采购商品库存及状态
    :return: 采购单信息列表
    '''
    driver = webdriver.Chrome()
    # option = webdriver.ChromeOptions()
    # option.add_argument('--headless')
    # driver = webdriver.Chrome(chrome_options=option)
    driver.maximize_window()
    wait = WebDriverWait(driver, 5)
    driver.get('https://www.1688.com/')
    for key in cookie:  # 添加cookie
        driver.add_cookie({
            'domain': '.1688.com',
            'name': key,
            'value': cookie[key],
            'path': '/'
        })

    for item in order_list:
        goods_url = item['goods_url']
        goods_sku1 = item['goods_sku1']
        goods_sku2 = item['goods_sku2']
        goods_status = ''
        goods_stock = ''

        driver.get(goods_url)
        # html = driver.page_source
        # doc = etree.HTML(html)
        # new_url = doc.xpath('//a[@title="查看货品最新详情"]/@href')[0]
        # driver.get(new_url)
        # 获取起批量
        html = driver.page_source
        doc = etree.HTML(html)
        amount = doc.xpath('//tr[@class="amount"]/td/span[1]/text()')[0]
        batches = re.search(r'(\d+)', amount).group(1)

        try:
            wait.until(EC.presence_of_element_located((By.XPATH, '//div[@id="mod-detail-bd"]')))   # 判断商品是否存在
            if goods_sku1 and goods_sku2:
                sku1 = re.split(r'：', goods_sku1, 1)[1]
                sku2 = re.split(r'：', goods_sku2, 1)[1]
                try:
                    if len(doc.xpath('//div[@class="obj-leading"]//li')) > 1:
                        sku1_matched = wait.until(
                                        EC.element_to_be_clickable((By.XPATH, '//div[@class="obj-leading"]//li//a[@title="{}"]'.format(sku1))))
                        sku1_matched.send_keys(Keys.ENTER)
                        time.sleep(0.5)
                    html = driver.page_source
                    doc = etree.HTML(html)
                    try:    # sku2是文字的情况
                        goods_stock = doc.xpath('//*[@class="table-sku"]//td[@class="name"]/span[text()="{}"]/../../td[@class="count"]/span/em[1]/text()'.format(sku2))[0]
                    except:    # sku2是图片的情况
                        goods_stock = doc.xpath('//*[@class="table-sku"]//td[@class="name"]/span[@title="{}"]/../../td[@class="count"]/span/em[1]/text()'.format(sku2))[0]
                except:
                    goods_status = '商品属性不存在'
            elif goods_sku1 and not goods_sku2:
                try:
                    sku1 = re.split(r'：', goods_sku1, 1)[1]
                    html = driver.page_source
                    doc = etree.HTML(html)
                    try:    # sku1是文字的情况
                        goods_stock = doc.xpath('//*[@class="table-sku"]//td[@class="name"]/span[text()="{}"]/../../td[@class="count"]/span/em[1]/text()'.format(sku1))[0]
                    except:    # sku1是图片的情况
                        goods_stock = doc.xpath('//*[@class="table-sku"]//td[@class="name"]/span[@title="{}"]/../../td[@class="count"]/span/em[1]/text()'.format(sku1))[0]
                except:
                    goods_status = '商品属性不存在'
            else:
                try:
                    html = driver.page_source
                    doc = etree.HTML(html)
                    goods_stock = re.search(r'(\d+)', doc.xpath('//span[@class="total"]/text()')[0]).group(1)
                except:
                    goods_status = '商品属性不存在'
        except TimeoutException:
            goods_status = '商品已失效'

        # item['goods_url'] = new_url
        item['goods_stock'] = goods_stock
        item['goods_status'] = goods_status
        item['quantity'] = ''
        item['batches'] = batches
        time.sleep(0.5)

    driver.quit()
    return order_list


