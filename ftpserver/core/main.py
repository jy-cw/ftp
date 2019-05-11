#!/usr/bin/env python
#coding=utf-8

import argparse
from core.ftpserver import FtpHandler
import socketserver
from conf import settings


class ArvgHandler(object):
    def __init__(self):
        parse = argparse.ArgumentParser(description='ftp 服务端使用方法')
        parse.add_argument('command', help='启动服务端:start; 停止服务端:stop',
                           choices=['start', 'stop'])

        self.options = parse.parse_args()

        self.verify_args(self.options)

    def verify_args(self,options):
        '''校验并调用相应的功能'''
        if hasattr(self,options.command):
            func = getattr(self,options.command)
            func()
        else:
            exit("没有这个方法!")


    def start(self):
        print('---\033[32;1mStarting FTP server on %s:%s\033[0m----' %(settings.HOST, settings.PORT))

        server = socketserver.ThreadingTCPServer((settings.HOST, settings.PORT), FtpHandler)
        server.serve_forever()