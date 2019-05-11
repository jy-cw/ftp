#!/usr/bin/env python
#coding=utf-8

import os,json,socketserver
import configparser,subprocess
import sys,hashlib,re
from core import md5
from conf import settings
from core import logger

STATUS_CODE  = {
    200 : "Task finished",
    250 : "Invalid cmd format, e.g: {'action':'get','filename':'test.py','size':344}",
    251 : "Invalid cmd ",
    252 : "Invalid auth data",
    253 : "Wrong username or password",
    254 : "Passed authentication",
    255 : "Filename doesn't provided",
    256 : "File doesn't exist on server",
    257 : "ready to send file",
    258 : "md5 verification",
    259 : "path doesn't exist on server",
    260 : "path changed",
}

logger = logger.logger('access')

class FtpHandler(socketserver.BaseRequestHandler):

    def handle(self):
        while True:
            try:
                self.data = self.request.recv(1024).strip()
                logger.info('客户端地址: ' + self.client_address[0])
                logger.info ('客户端请求头:'+ self.data.decode())
                # print('客户端地址:',self.client_address[0])
                # print('客户端请求头:',self.data.decode())
                if not self.data:
                    logger.info ('客户端:%s 已经断开连接' % self.client_address[0])
                    # print('客户端断开')
                    break
                data = json.loads(self.data.decode())
                if data['action'] is not None:
                    if hasattr(self,'_%s' %data['action']):
                        func = getattr(self,'_%s' %data['action'])
                        func(data)
                    else:
                        logger.error('不支持这个命令: '+ data['action'])
                        # print('不支持这个命令: ',data['action'])
                        self.send_response (250)
                else:
                    logger.error ("命令格式错误")
                    # print ("命令格式错误")
                    self.send_response(250)
            except ConnectionResetError as e:
                logger.info(e)
                # print('err:',e)
                break

    def send_response(self,code,data=None):
        response = {
            'code':code,
            'msg':STATUS_CODE[code]
        }
        if data:
            response['data']=data

        self.request.send(json.dumps(response).encode())
        logger.info ('服务器返回头:'+ json.dumps(response))
        # print('服务器返回头:',response)

    def _put(self,*args,**kwargs):
        data = args[0]
        filename = data['filename']
        if filename == '':
            self.send_response(255)
        size = data['size']
        logger.info('准备接受的 %s 文件总大小为:%s' % (filename,size))
        # print ('准备接受的 %s 文件总大小为:%s' % (filename,size))
        #告诉客户端可以上传了
        self.send_response(200)
        recv_size = 0
        file_abs_path = "%s/%s" % (self.current_dir, data.get('filename').split('/')[-1])
        f = open(file_abs_path,'wb')
        while recv_size < size:
            recv_data = self.request.recv(1024)
            f.write(recv_data)
            recv_size += len(recv_data)
        else:
            f.close()
            logger.info('%s 已经上传完毕' %(file_abs_path))
            # print('%s 已经上传完毕' %(file_abs_path))
        if data['md5']:
            server_md5 = md5.md5sum(file_abs_path)
            self.send_response(200,data={'md5':server_md5})


    def _get(self,*args,**kwargs):
        data = args[0]
        filename = data['filename']
        if filename == '':
            self.send_response(255)
        file_abs_path = "%s/%s" % (self.current_dir, data.get('filename'))
        if os.path.isfile(file_abs_path):
            f = open(file_abs_path,'rb')
            size = os.path.getsize(file_abs_path)
            if data['md5']:
                server_md5 = md5.md5sum(file_abs_path)
                self.send_response(257,data={'size':size,'md5':server_md5})
            else:
                self.send_response(257,data={'size':size})
            self.request.recv(1024)
            for line in f:
                self.request.send(line)
            logger.info('下载 %s 文件结束' %(file_abs_path))
            # print('下载 %s 文件结束' %(file_abs_path) )
            f.close()
        else:
            logger.info('服务器文件 %s 不存在' %file_abs_path)
            # print('服务器文件 %s 不存在' %file_abs_path)
            self.send_response(259)

    def _auth(self,*args,**kwargs):
        data = args[0]
        if data['username'] == '' or data['password'] == '':
            self.send_response(252)

        user = self.authenticate(data["username"], data["password"])
        if user is None:
            self.send_response (253)
        else:
            logger.info('用户: %s 认证通过' % user['Username'])
            # print ("认证通过", user['Username'])
            # self.user = user
            # self.user['username'] = data.get ("username")

            self.home_dir = "%s/home/%s" % (settings.BASE_DIR, data["username"])
            cmd = 'mkdir %s' % self.home_dir
            subprocess.getstatusoutput(cmd)

            self.current_dir = self.home_dir
            logger.info('用户当前目录为:'+self.current_dir)
            # print('用户当前目录为:',self.current_dir)
            self.send_response (254)


    def authenticate(self, username, password):
        '''验证用户合法性，合法就返回用户数据'''

        config = configparser.ConfigParser ()
        config.read (settings.ACCOUNT_FILE)
        if username in config.sections ():
            _password = config[username]["Password"]
            if _password == password:
                # print ("认证通过..", username)
                config[username]["Username"] = username
                #返回一个用户Section地址<Section: username>
                return config[username]

    def _ls(self,*args,**kwargs):
        res = self.run_cmd ("ls -lh %s" % self.current_dir)
        self.send_response (200, data=res)

    def _pwd(self,*args,**kwargs):
        current_relative_dir = self.get_relative_path(self.current_dir)
        self.send_response(200,data=current_relative_dir)

    def _cd(self, *args,**kwargs):
        """change dir"""
        #print( args,kwargs)
        if args[0]:
            dest_path = "%s/%s" % (self.current_dir,args[0]['path'] )
        else:
            dest_path = self.home_dir


        real_path = os.path.realpath(dest_path)
        logger.info("服务器上真实路径:"+ real_path)
        # print("服务上真实路径", real_path)
        if real_path.startswith(self.home_dir):# accessable
            if os.path.isdir(real_path):
                self.current_dir = real_path
                current_relative_dir = self.get_relative_path(self.current_dir)
                self.send_response(260, {'current_path':current_relative_dir})
            else:
                self.send_response(259)
        else:
            logger.info ("抱歉，您没有权限去 %s 目录" % real_path)
            # print("抱歉，您没有权限去 %s 目录" % real_path)
            current_relative_dir = self.get_relative_path(self.current_dir)
            self.send_response(260, {'current_path': current_relative_dir})

    def _mkdir(self,*args,**kwargs):
        '''创建目录'''
        dirname = args[0]['dirname']
        ftp_dirname_path = self.current_dir + '/' + dirname
        res = self.run_cmd('mkdir -p ' + ftp_dirname_path)
        self.send_response(200,data=res)

    def get_relative_path(self, abs_path):
        """返回用户的ftp虚拟目录路径"""
        relative_path = re.sub ("%s" % self.home_dir, '', abs_path)
        logger.info("ftp虚拟路径: %s\n服务器上真实路径: %s"% (relative_path, abs_path))
        # print ("ftp虚拟路径: %s\n服务器上真实路径: %s"% (relative_path, abs_path))
        if relative_path == '':
            relative_path ='/'
        return relative_path

    def run_cmd(self, cmd):
        cmd_result = subprocess.getstatusoutput(cmd)
        return cmd_result


if __name__ == '__main__':
    HOST,PORT = '0.0.0.0',9999
