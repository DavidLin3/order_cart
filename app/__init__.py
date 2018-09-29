from flask import Flask
import flask_excel as excel
import logging, datetime

app = Flask(__name__)
app.debug = True
app.config['SECRET_KEY'] = 'af2fad8cfe1f4c5feeac4aa5edf6fcc8f3'
app.config['SESSION_REFRESH_EACH_REQUEST'] = False
app.config['PERMANENT_SESSION_LIFETIME'] = datetime.timedelta(seconds=60)


app.config['MONGODB_SETTINGS'] = {
    'db': 'history_scrapy20180917',
    'host': '127.0.0.1',
    'port': 27017
}

from .models import db
db.init_app(app)
excel.init_excel(app)

# 日志系统配置
handler = logging.FileHandler('flask.log', encoding='UTF-8')
handler.setLevel(logging.ERROR)
logging_format = logging.Formatter('%(asctime)s - %(levelname)s - %(filename)s - %(funcName)s - %(lineno)s - %(message)s')
handler.setFormatter(logging_format)
app.logger.addHandler(handler)


from app.taobao import taobao as taobao_blueprint
from app.t1688 import t1688 as t1688_blueprint
app.register_blueprint(taobao_blueprint, url_prefix='/api/v1.0/taobao')
app.register_blueprint(t1688_blueprint, url_prefix='/api/v1.0/1688')
