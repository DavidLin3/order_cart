from . import t1688
from flask import request, Response, session, redirect, url_for, current_app
from app.models import T1688Shop, T1688Orders, T1688OrderCart
from mongoengine.queryset.visitor import Q
from collections import OrderedDict
import json, time
from bson import ObjectId
from app.t1688_query import t1688_query
from app.t_redis_queue.queue import RedisClient
import os, sys, subprocess
from functools import wraps
from app.add_t1688_cart import add_t1688_cart


MAPPING = {
    'id': '_id',
    'goodsUrl': 'goods_url',
    'goodsTitle': 'goods_title',
    'goodsImg': 'goods_img',
    'storeName': 'corp_name',
    'wwId': 'ww_name',
    'realPerPrice': 'goods_price',
    'goodsSku1': 'goods_sku1',
    'goodsSku2': 'goods_sku2',
    'skuId': 'sku_id'
}

# 登录装饰器
def user_scan_req(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_name" not in session:
            return redirect(url_for('.get_QR_url'))
        return f(*args, **kwargs)
    return decorated_function


@t1688.route('/1688Cart/shopList', methods=['GET', 'POST'])
def get_shop_list():
    '''
    商品库信息及商品库模糊搜索功能，实现组合去重
    '''
    # 查询参数
    ww_id = request.args.get('wwId') or ''
    store_name = request.args.get('storeName') or ''
    goods_title = request.args.get('goodsTitle') or ''
    sku_id = request.args.get('skuId') or ''
    # 分页参数
    page_num = int(request.args.get('pageNum') or 1)
    page_size = int(request.args.get('pageSize') or 20)

    # 从历史订单数据库更新数据到商品库，不覆盖原有数据，保证卖家sku的完整保留
    one_record = T1688Shop.objects.order_by('-_id').first()    # 筛选t1688shop中_id最大值的记录
    max_id = one_record['_id'] if one_record else None
    if max_id:    # 取出历史订单t1688orders中大于此_id的记录
        query_set = T1688Orders.objects(_id__gt=max_id)
    else:    # 商品库为空，取出历史订单所有记录
        query_set = T1688Orders.objects()
    if query_set:    # 将查询结果转化并插入至shop中
        only_records = query_set.aggregate(    # 组合去重
            {
                '$group': {
                    '_id': {'goods_url': "$goods_url", 'goods_sku1': "$goods_sku1", 'goods_sku2': "$goods_sku2"},
                    'id': {'$max': "$_id"},    # 取_id最大值
                    'goods_url': {'$first': "$goods_url"},
                    'goods_title': {'$first': "$goods_title"},
                    'goods_img': {'$first': "$goods_img"},
                    'corp_name': {'$first': "$corp_name"},
                    'ww_name': {'$first': "$ww_name"},
                    'goods_price': {'$first': "$goods_price"},
                    'goods_sku1': {'$first': "$goods_sku1"},
                    'goods_sku2': {'$first': "$goods_sku2"}
                }
            }
        )
        for item in only_records:
            item.pop('_id')
            item['_id'] = item.pop('id')
            item['sku_id'] = ''
            if not max_id:     # 商品库为空，直接保存
                T1688Shop(**item).save()
            else:    # 商品库不为空，查询无重复再保存
                if not T1688Shop.objects(goods_url=item['goods_url'], goods_sku1=item['goods_sku1'], goods_sku2=item['goods_sku2']):
                    T1688Shop(**item).save()

    # 商品库展示
    if ww_id or store_name or goods_title or sku_id:    # 条件查询（模糊查询）
        page_data = T1688Shop.objects(Q(__raw__={'ww_name':{'$regex':ww_id}})
                                 & Q(__raw__={'store_name':{'$regex':store_name}})
                                 & Q(__raw__={'goods_title':{'$regex':goods_title}})
                                 & Q(__raw__={'sku_id':{'$regex':sku_id}})
                                 ).paginate(page=page_num, per_page=page_size)
    else:    # 一般情况（无查询）
        page_data = T1688Shop.objects().paginate(page=page_num, per_page=page_size)

    list_all_query = []
    for item in page_data.items:
        new_each_result = OrderedDict()
        for k, v in MAPPING.items():
            new_each_result[k] = str(item[v]) if item[v] else ''
        list_all_query.append(new_each_result)

    result = {
        'status': 0,
        'total': page_data.total,
        'pageSize': page_size,
        'pageNum': page_data.page,
        'data': {'list': list_all_query},
        'msg': '请求成功'
    }
    return Response(json.dumps(result), mimetype='application/json')


@t1688.route('/1688Cart/saveSku', methods=['GET', 'POST'])
@user_scan_req
def save_sku():
    '''
    保存sku至shop商品库
    '''
    id = request.args.get('id')
    sku_id = request.args.get('skuId')
    shop_order = request.args.get('shopOrder')

    try:
        o_id = ObjectId(id)
        T1688Shop.objects(_id=o_id).update_one(set__sku_id=sku_id)
        result = {'status': 0, 'msg': '请求成功'}
    except Exception:
        current_app.logger.error("sku can't be saved!", exc_info=True)
        result = {'status': 1, 'msg': '保存失败，网络有点问题，请稍后重试'}
    return Response(json.dumps(result), mimetype='application/json')


@t1688.route('/1688Cart/addOrderList', methods=['GET', 'POST'])
def add_order_list():
    '''
    批量或逐个加入采购单
    '''
    redis = RedisClient(db=1)
    user_login_dict = redis.get_login_info_by_img(session['QR'])
    cookie = user_login_dict.get('cookie')    # 获取登录cookie
    # 查询参数
    ids_json = request.args.get('ids') or '{"ids": ["5b7a6aaa3f3e1cceb46c97e3", "5b7a6aaa3f3e1cceb46c97de", "5b7a6aaa3f3e1cceb46c97b4", "5b7a6aaa3f3e1cceb46c97ab", "5b7a6aa93f3e1cceb46c9752"]}'        # 请求字段
    ids_dict = json.loads(ids_json)
    ids = ids_dict['ids']

    order_list = []
    if len(T1688OrderCart.objects) < 50:
        for id in ids:
            if not T1688OrderCart.objects(_id=ObjectId(id)):    # 排除重复加入的订单
                order_dict = T1688Shop.objects(_id=ObjectId(id)).first().to_mongo().to_dict()
                order_list.append(order_dict)
        if order_list:
            final_order_list = t1688_query(order_list, cookie)
            for order_dict in final_order_list:
                T1688OrderCart(**order_dict).save()
            result = {'status': 0, 'msg': '加入成功'}
        else:
            result = {'status': 1, 'msg': '商品已经在采购单里面了，无需重复添加'}
    else:
        result = {'status': 1, 'msg': '加入失败，最多只能加入50个商品'}

    return Response(json.dumps(result), mimetype='application/json')


@t1688.route('/1688Cart/orderList', methods=['GET', 'POST'])
def get_order_list():
    '''
    采购单列表页展示
    '''
    # 分页字段
    page_num = int(request.args.get('pageNum') or 1)
    page_size = int(request.args.get('pageSize') or 20)

    page_data = T1688OrderCart.objects.paginate(page=page_num, per_page=page_size)
    list_all_query = []
    for item in page_data.items:
        new_each_result = OrderedDict()
        for k, v in MAPPING.items():
            new_each_result[k] = str(item[v]) if item[v] else ''
        new_each_result['goodsStock'] = item['goods_stock']
        new_each_result['goodsStatus'] = item['goods_status']
        new_each_result['quantity'] = item['quantity']
        new_each_result['batches'] = item['batches']
        list_all_query.append(new_each_result)

    result = {
        'status': 0,
        'total': page_data.total,
        'pageSize': page_size,
        'pageNum': page_data.page,
        'data': {'list': list_all_query},
        'msg': '请求成功'
    }
    return Response(json.dumps(result), mimetype='application/json')


@t1688.route('/1688Cart/searchView', methods=['GET', 'POST'])
def search_view():
    '''
    采购单关键词联想搜索
    '''
    # 查询字符串
    goods_title = request.args.get('goodsTitle')
    sku_id = request.args.get('skuId')

    shop_list = []
    if goods_title:
        queryset = T1688Shop.objects(__raw__={'goods_title':{'$regex':goods_title}})    # 查询商品名称
        for ob in queryset:
            ob_dict = ob.to_mongo().to_dict()
            shop_dict = {'id': str(ob_dict['_id']), 'goodsTitle': ob_dict['goods_title'], 'skuId': ob_dict['sku_id']}
            shop_list.append(shop_dict)
            if len(shop_list) == 10:    # 取前10条记录
                break
    if sku_id:
        queryset = T1688Shop.objects(__raw__={'sku_id': {'$regex': sku_id}})    # 查询商家sku
        for ob in queryset :
            ob_dict = ob.to_mongo().to_dict()
            shop_dict = {'id': str(ob_dict['_id']), 'goodsTitle': ob_dict['goods_title'], 'skuId': ob_dict['sku_id']}
            shop_list.append(shop_dict)
            if len(shop_list) == 10:
                break
    if shop_list:
        result = {
            'status': 0,
            'data': {'list': shop_list},
            'msg': '请求成功'
        }
    else:
        result = {'status': 1, 'msg': '没有找到相关商品'}
    return Response(json.dumps(result), mimetype='application/json')


@t1688.route('/1688Cart/addCart', methods=['GET', 'POST'])
def add_cart():
    '''
    加入1688进货单，需进一步确认返回给前端的数据
    '''
    cart_parm_json = request.args.get('cartParm') or '{"cartParm": [{"id": "5b7a6aaa3f3e1cceb46c97de", "quantity": "10"}, {"id": "5b7a6aaa3f3e1cceb46c97b4", "quantity": "10"}, {"id": "5b7a6aaa3f3e1cceb46c97ab", "quantity": "6"}, {"id": "5b7a6aa93f3e1cceb46c9752", "quantity": "15"}]}'
    cart_parm_dict = json.loads(cart_parm_json)
    cart_list = cart_parm_dict['cartParm']

    for item in cart_list:    # 查询参数并构造字典列表
        ob = T1688OrderCart.objects(_id=ObjectId(item['id'])).first()
        item['goods_url'] = ob['goods_url']
        item['goods_sku1'] = ob['goods_sku1']
        item['goods_sku2'] = ob['goods_sku2']

    redis = RedisClient(db=1)
    user_login_dict = redis.get_login_info_by_img(session['QR'])
    cookie = user_login_dict.get('cookie')
    order_cart_list = add_t1688_cart(cart_list, cookie)    # 加入淘宝购物车，返回购物车商品信息列表

    result = {
        'status': 0,
        'data': {'list': order_cart_list},
        'msg': '请求成功'
    }
    return Response(json.dumps(result), mimetype='application/json')


@t1688.route('/1688Cart/uploadSku', methods=['GET', 'POST'])
def upload_sku():
    '''
    excel导入卖家sku
    '''
    if request.method == 'POST':
        upload_data = request.get_records(field_name='file')
        # 检查卖家sku是否重复
        sku_list = [item['SKU'] for item in upload_data if item['SKU']!='']
        for i in sku_list:
            if sku_list.count(i) > 1:
                result = {
                    'status': 1,
                    'msg': '导入失败，卖家SKU：{}重复了'.format(i)
                }
                return Response(json.dumps(result), mimetype='application/json')
        # sku导入处理
        match_sum, not_match_sum, forty_more_sum = 0, 0, 0
        for item in upload_data:
            ob = T1688Shop.objects(goods_url=item['商品链接'])
            if not ob:
                not_match_sum += 1
            elif len(str(item['SKU'])) > 40:
                forty_more_sum += 1
            else:
                ob.update_one(set__sku_id=str(item['SKU']))
                match_sum += 1

        result = {
            'status': 0,
            'msg': '导入成功！{0}个商品匹配成功，{1}个商品链接无法匹配，{2}个商品的SKU超过40个字符，插入失败'\
                                                    .format(match_sum, not_match_sum, forty_more_sum)
        }
        return Response(json.dumps(result), mimetype='application/json')
    return '''
    <title>Upload an excel file</title>
    <h1>Excel file upload (csv, tsv, csvz, tsvz only)</h1>
    <form action="" method=post enctype=multipart/form-data><p>
    <input type=file name=file><input type=submit value='导入'>
    </form>
    '''


@t1688.route('/1688Cart/uploadQty', methods=['GET', 'POST'])
def upload_quantity():
    '''
    excel导入采购数量
    '''
    if request.method == 'POST':
        upload_data = request.get_records(field_name='file')
        # 采购数量导入处理
        match_sum, not_match_sum = 0, 0
        for item in upload_data:
            ob = T1688OrderCart.objects(goods_url=item['商品链接'])
            if not ob:
                not_match_sum += 1
            else:
                ob.update_one(set__quantity=str(item['采购数量']))
                match_sum += 1
        result = {
            'status': 0,
            'msg': "导入成功！{0}个商品匹配成功，{1}个商品链接无法匹配".format(match_sum, not_match_sum)
        }
        return Response(json.dumps(result), mimetype='application/json')
    return '''
    <title>Upload an excel file</title>
    <h1>Excel file upload (csv, tsv, csvz, tsvz only)</h1>
    <form action="" method=post enctype=multipart/form-data><p>
    <input type=file name=file><input type=submit value='导入'>
    </form>
    '''


@t1688.route('/1688Cart/remove', methods=['GET', 'POST'])
def remove_order():
    '''
    移除采购单商品
    '''
    id = request.args.get('id')
    T1688OrderCart.objects(_id=ObjectId(id)).delete()
    return Response(json.dumps({"status": 0, "msg": "请求成功"}), mimetype='application/json')


base_dir = os.path.abspath(os.path.dirname(__file__))
@t1688.route('/qrcode', methods=['GET', 'POST'])
def get_QR_url():
    cmd_path = os.path.join(base_dir, '../')
    if sys.platform == 'win32':
        cmd = 'python ' + cmd_path + '/t1688_prepare_start.py'
    else:
        cmd = 'python3 ' + cmd_path + '/t1688_prepare_start.py'

    os.chdir(cmd_path)
    subprocess.Popen(cmd, shell=True, close_fds=True)
    redis = RedisClient(db=1)
    img = redis.pop_QR()
    while not img:
        img = redis.pop_QR()
        time.sleep(0.2)

    session['QR'] = img
    img = bytes.decode(img)
    return Response(json.dumps({'status': 0, 'url': img}), mimetype='application/json')


@t1688.route('/isLogin', methods=['GET', 'POST'])
def get_isLogin():
    user_login_info_dict = None
    if 'QR' in session:
        user_login_info_dict = RedisClient(db=1).get_login_info_by_img(session['QR'])
    if user_login_info_dict is not None and user_login_info_dict.get('nick'):
        session['user_name'] = user_login_info_dict.get('nick')
        return Response(json.dumps({"status": 0}), mimetype='application/json')
    else:
        return Response(json.dumps({"status": 1}), mimetype='application/json')


@t1688.route("/logout/", methods=["GET", "POST"])
def logout():
    session.pop("user_name", None)
    session.pop("QR", None)
    return Response(json.dumps({"status": 0}), mimetype='application/json')