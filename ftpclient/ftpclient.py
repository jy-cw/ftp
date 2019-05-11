#!/usr/bin/env python
#coding=utf-8

import os,json,socket,hashlib,sys
import argparse
import  md5
import getpass

class FtpClient(object):
    def __init__(self):
        parse = argparse.ArgumentParser(description='ftp 客户端使用方法')
        parse.add_argument("-v", "--version", action='version', version='%(prog)s 1.0')
        parse.add_argument('-s','--server',dest='server',help='ftp 服务端的地址')
        parse.add_argument('-P','--Port',type=int,dest='port',help='ftp 服务端的端口')
        parse.add_argument('-u','--username',dest='username',help='用户名')
        parse.add_argument('-p','--password',dest='password',help='密码')

        print(parse.parse_args())
        self.option = parse.parse_args()
        self.verify_args(self.option)
        self.make_connect()

    def verify_args(self, options):
        '''校验参数合法型'''

        if options.username is not None and options.password is not None:
            pass
        elif options.username is None and options.password is None:
            pass
        else:
            exit("用户名和密码必须同时存在或者同时不指定")

        if options.server and options.port:
            if options.port >0 and options.port <65535:
                return True
            else:
                exit("Err:host port must in 0-65535")
        else:
            exit("Error:必须填写server和port, -h 查看帮助信息")

    def make_connect(self):
        self.client = socket.socket()
        self.client.connect((self.option.server,self.option.port))

    def get_response(self):
        '''得到服务器端回复结果'''
        data = self.client.recv (1024)
        # print("server res", data)
        data = json.loads(data.decode())
        return data

    def authenticate(self):
        if self.option.username:
            return self.get_auth_result(self.option.username, self.option.password)
        else:
            retry_count = 0
            while retry_count < 3:
                username = input ("用户名:").strip ()
                password = getpass.getpass("密码:").strip()
                if self.get_auth_result (username, password):
                    return True
                retry_count += 1

    def get_auth_result(self,username,password):
        data_header ={
            'action':'auth',
            'username':username,
            'password':password
        }
        self.client.send(json.dumps(data_header).encode())
        response = self.get_response()
        if response['code'] == 254:
            self.username = username
            return  True
        else:
            print('错误: ',response['msg'])


    def interactive(self):
        if self.authenticate():
            print ("---欢迎 %s 登录FTP---"%self.username)
            self.terminal_display = "[%s@FTP /]$: " % self.username
            while True:
                cmd = input(self.terminal_display)
                if len(cmd) == 0: continue
                cmd_list = cmd.split()
                if hasattr(self,'_%s' %cmd_list[0]):
                    func = getattr(self,'_%s' %cmd_list[0])
                    func(cmd_list)
                else:
                    print('命令错误，请通过help查看帮助信息')

    def _help(self,*args,**kwargs):
        supported_actions = """
               get filename --md5   #下载ftp服务器上的文件到当前目录, --md5可选,可以校验本地和服务器上的md5值
               put filename --md5   #把本地文件上传到ftp服务器上, --md5可选,可以校验本地和服务器上的md5值
               ls              #列出ftp服务器的目录文件
               pwd             #检查当前路径
               cd path         #改变目录
               mkdir dirname   #创建目录
               """
        print (supported_actions)

    def __md5_required(self,cmd_list):
        '''检测命令是否需要进行MD5验证'''
        if '--md5' in cmd_list:
            return True

    def show_progress(self,total):
        received_size = 0
        current_percent = 0
        while received_size < total:
             if int((received_size / total) * 100 )   > current_percent :
                  print("#",end="",flush=True)
                  current_percent = int((received_size / total) * 100 )
             new_size = yield
             received_size += new_size

    def _put(self,*args,**kwargs):
        cmd_list = args[0]
        print ("上传命令列表--", cmd_list)
        if len(cmd_list) == 1:
            print('没带文件参数')
            return

        filename = cmd_list[1]

        if os.path.isfile(filename):
            size = os.path.getsize(filename)
            if self.__md5_required(cmd_list):
                local_md5 = md5.md5sum(filename)
                data_header = {
                    'action': 'put',
                    'filename': filename,
                    'size': size,
                    'md5': local_md5
                }
            else:
                data_header ={
                    'action': 'put',
                    'filename': filename,
                    'size': size,
                    'md5': None
                }
            self.client.send(json.dumps(data_header).encode())
            response = self.get_response()
            if response['code'] == 200:
                process = self.show_progress(size)
                process.__next__()
                f = open (filename, 'rb')
                for  line in f:
                    self.client.send(line)
                    try:
                        process.send(len(line))
                    except StopIteration as e:
                        print("100%")
                print('文件上传完毕')
                f.close()
            else:
                print('错误: ',response['msg'])
            if self.__md5_required (cmd_list):
                md5_recv = self.get_response()
                server_md5 = md5_recv['data']['md5']
                if server_md5 == local_md5:
                    print('服务器上的文件和本地文件md5校验一致,都是: ',local_md5)
                else:
                    print('文件MD5校验不一致，服务器MD5: %s,本地MD5: %s' %(server_md5,local_md5))
        else:
            print(os.getcwd())
            print(filename,'本地文件不存在')

    def _get(self,*args,**kwargs):
        cmd_list = args[0]
        print ("下载命令列表--", cmd_list)
        if len (cmd_list) == 1:
            print ('没带文件参数')
            return
        filename = cmd_list[1]

        if self.__md5_required(cmd_list):
            data_header = {
                'action': 'get',
                'filename': filename,
                'md5': True
            }
        else:
            data_header = {
                'action': 'get',
                'filename': filename,
                'md5': False
            }

        self.client.send (json.dumps (data_header).encode ())
        response = self.get_response ()
        if response['code'] == 257:
            #告诉服务器端可以发送了
            self.client.send(b'1')
            size = response['data']['size']
            recv_size = 0
            m = hashlib.md5 ()
            f = open(filename,'wb')
            process = self.show_progress(size)
            process.__next__()
            while recv_size < size:
                recv_data = self.client.recv(1024)
                f.write(recv_data)
                recv_size += len(recv_data)
                try:
                    process.send(len(recv_data))
                except StopIteration as e:
                    print("100%")
            else:
                print('%s 文件下载完成' % filename)
                f.close()
        else:
                print('错误: ',response['msg'])

        if data_header['md5']:
            server_md5 = response['data']['md5']
            local_md5  = md5.md5sum(filename)
            if server_md5 == local_md5:
                print('服务器文件和本地文件md5校验一致，都是: ', local_md5)
            else:
                print('错误:文件md5校验不一致,服务器MD5: %s,本地MD5: %s' % (server_md5, local_md5))

    def _ls(self,*args,**kwargs):
        data_header = {'action':'ls'}
        self.client.send(json.dumps(data_header).encode())
        response = self.get_response()

        if response.get("code") == 200:
            data = response.get("data")
            if data[0] == 0:
                print(data[1])
            else:
                print('错误: ',data[1])
        else:
            print ("错误: ",response['msg'])


    def _pwd(self,*args,**kwargs):
        data_header = {'action':'pwd'}
        self.client.send(json.dumps(data_header).encode())
        response = self.get_response()
        has_err = False
        if response.get("code") == 200:
            data = response.get("data")
            if data:
                print(data)
            else:
                has_err = True
        else:
            has_err = True

        if has_err:
            print("Error:something wrong.")

    def _cd(self,*args,**kwargs):
        #print("cd args",args)
        if len(args[0]) >1:
            path = args[0][1]
        else:
            path = ''
        data_header = {'action': 'cd','path':path}
        self.client.send(json.dumps(data_header).encode())
        response = self.get_response()
        if response.get("code") == 260:
            self.terminal_display ="[%s@FTP %s]$: " % (self.username,response.get('data').get("current_path"))
        else:
            print(response.get('msg'))

    def _mkdir(self,*args,**kwargs):
        cmd_list = args[0]
        print ("创建目录命令列表--", cmd_list)
        if len(cmd_list) == 1:
            print('没带目录参数')
            return

        dirname = cmd_list[1]
        data_header = {'action':'mkdir','dirname':dirname}
        self.client.send(json.dumps(data_header).encode())
        response = self.get_response()
        if response.get('code') == 200:
            data = response.get('data')
            if data[0] != 0:
                err_msg = data[1]
                print(err_msg)
        else:
            print('错误: ',response.get('msg'))

if __name__ == "__main__":
    ftp = FtpClient()
    ftp.interactive()
