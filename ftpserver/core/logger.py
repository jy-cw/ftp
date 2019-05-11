#!/usr/bin/env python
#coding=utf-8

import logging
from logging import handlers
from conf import settings


def logger(log_type):
    logger = logging.getLogger(log_type)
    logger.setLevel(settings.LOG_LEVEL)

    #输出到屏幕上
    ch = logging.StreamHandler()
    ch.setLevel(settings.LOG_LEVEL)

    #写入到日志文件中，并且有回滚功能
    log_file = '%s/%s' %(settings.LOG_DIR,settings.LOG_TYPES[log_type])
    fh =  handlers.TimedRotatingFileHandler(log_file,when='M',interval=10,backupCount=3)
    fh.setLevel(settings.LOG_LEVEL)

    #设置格式
    formatter =  logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    #给handler 配置日志ges
    ch.setFormatter(formatter)
    fh.setFormatter(formatter)


    #给logger配置handler

    logger.addHandler(ch)
    logger.addHandler(fh)
    return logger
