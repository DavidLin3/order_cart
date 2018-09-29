from flask_mongoengine import MongoEngine


db = MongoEngine()

# taobao
class Shop(db.Document):
    meta = {'collection': 'shop'}

    _id = db.ObjectIdField()
    goods_url = db.StringField()
    goods_title = db.StringField()
    goods_img = db.StringField()
    store_name = db.StringField()
    ww_name = db.StringField()
    real_per_price = db.StringField()
    goods_sku1 = db.StringField()
    goods_sku2 = db.StringField()
    sku_id = db.StringField()

    def __str__(self):
        return super().__str__()


class Orders(db.Document):
    meta = {'collection': 'orders'}

    _id = db.ObjectIdField()
    order_id = db.StringField()
    store_url = db.StringField()
    store_name = db.StringField()
    ww_name = db.StringField()
    true_name = db.StringField()
    city = db.StringField()
    tel = db.StringField()
    alipay_id = db.StringField()
    trade_time = db.StringField()
    pay_time = db.StringField()
    confirm_time = db.StringField()
    goods_total_price = db.StringField()
    post_fee = db.StringField()
    real_pay = db.StringField()
    delivery_addr = db.StringField()
    delivery_type = db.StringField()
    delivery_company = db.StringField()
    delivery_id = db.StringField()
    buy_message = db.StringField()
    nick = db.StringField()
    goods_img = db.StringField()
    goods_title = db.StringField()
    goods_url = db.StringField()
    goods_sku1 = db.StringField()
    goods_sku2 = db.StringField()
    goods_status = db.StringField()
    goods_price = db.StringField()
    goods_count = db.StringField()
    goods_discount = db.StringField()
    goods_taobao_discount = db.StringField()
    goods_tmall_discount = db.StringField()
    real_per_price = db.StringField()

    def __str__(self):
        return super().__str__()


class OrderCart(db.Document):
    meta = {'collection': 'order_cart'}

    _id = db.ObjectIdField()
    goods_url = db.StringField()
    goods_title = db.StringField()
    goods_img = db.StringField()
    store_name = db.StringField()
    ww_name = db.StringField()
    real_per_price = db.StringField()
    goods_sku1 = db.StringField()
    goods_sku2 = db.StringField()
    sku_id = db.StringField()
    goods_stock = db.StringField()
    goods_status = db.StringField()
    quantity = db.StringField()

    def __str__(self):
        return super().__str__()


# 1688
class T1688Orders(db.Document):
    meta = {'collection': 't1688orders'}

    _id = db.ObjectIdField()
    order_id = db.StringField()
    alipay_id = db.StringField()
    buy_message = db.StringField()
    confirm_time = db.StringField()
    corp_name = db.StringField()
    corp_url = db.StringField()
    delivery_addr = db.StringField()
    delivery_company = db.StringField()
    delivery_id = db.StringField()
    goods_count = db.StringField()
    goods_discount = db.StringField()
    goods_img = db.StringField()
    goods_price = db.StringField()
    goods_sku1 = db.StringField()
    goods_sku2 = db.StringField()
    goods_status = db.StringField()
    goods_title = db.StringField()
    goods_total_price = db.StringField()
    goods_url = db.StringField()
    nick = db.StringField()
    pay_time = db.StringField()
    post_fee = db.StringField()
    real_pay = db.StringField()
    tel = db.StringField()
    trade_time = db.StringField()
    ww_name = db.StringField()

    def __str__(self):
        return super().__str__()


class T1688Shop(db.Document):
    meta={'collection': 't1688shop'}

    _id = db.ObjectIdField()
    goods_url = db.StringField()
    goods_title = db.StringField()
    goods_img = db.StringField()
    corp_name = db.StringField()
    ww_name = db.StringField()
    goods_price = db.StringField()
    goods_sku1 = db.StringField()
    goods_sku2 = db.StringField()
    sku_id = db.StringField()

    def __str__(self):
        return super().__str__()


class T1688OrderCart(db.Document):
    meta = {'collection': 't1688order_cart'}

    _id = db.ObjectIdField()
    goods_url = db.StringField()
    goods_title = db.StringField()
    goods_img = db.StringField()
    corp_name = db.StringField()
    ww_name = db.StringField()
    goods_price = db.StringField()
    goods_sku1 = db.StringField()
    goods_sku2 = db.StringField()
    sku_id = db.StringField()
    goods_stock = db.StringField()
    goods_status = db.StringField()
    quantity = db.StringField()
    batches = db.StringField()

    def __str__(self):
        return super().__str__()