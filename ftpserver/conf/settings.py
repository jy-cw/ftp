import os,logging
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

#ftp根目录,用户的家目录在此目录下
USER_HOME = "%s/home" % BASE_DIR

#日志配置
LOG_DIR =  "%s/log" % BASE_DIR
LOG_LEVEL = logging.DEBUG

LOG_TYPES = {
    'transaction': 'transactions.log',
    'access': 'access.log',
}

#用户登录认证
ACCOUNT_FILE = "%s/conf/accounts.cfg" % BASE_DIR

#服务端ip和端口
HOST = "0.0.0.0"
PORT = 9999


