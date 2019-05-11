# FTP
简易FTP服务端、客户端.目前只支持Linux系统
##  FTP服务端

### 服务器配置
```python
# cd /path/ftpserver/conf
# cat settings.py

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
```

### 用户认证配置
```python
# cd /path/ftpserver/conf
# cat accounts.cfg

[用户名]
Password = 密码
```

### 启动
```python
# cd /path/ftpserver
# python bin/ftpserver.py start
```
##  FTP客户端

### 启动
```python
# cd /path/ftpserver
# python ftpclient.py -s server_ip -P server_port -u username -p password
```

参数
```python
  -h, --help            show this help message and exit
  -v, --version         show program's version number and exit
  -s SERVER, --server SERVER
                        ftp 服务端的地址
  -P PORT, --Port PORT  ftp 服务端的端口
  -u USERNAME, --username USERNAME
                        用户名
  -p PASSWORD, --password PASSWORD
                        密码
```
### 功能列表
```python
get filename --md5   #下载ftp服务器上的文件到当前目录, --md5可选,可以校验本地和服务器上的md5值
put filename --md5   #把本地文件上传到ftp服务器上当前路径, --md5可选,可以校验本地和服务器上的md5值
ls              #列出ftp服务器的目录文件
pwd             #检查当前路径
cd path         #改变目录
mkdir dirname   #创建目录
```