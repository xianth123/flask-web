#!/usr/bin/python
# -*- coding: utf-8 -*-
import os

basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = "lizhixi"
    SQLALCHEMY_COMMIT_ON_TEARDOWN = True
    FLASK_MAIL_SUBJECT_PREFIX = '[Flask]'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    FLASK_ADMIN = "xianth123@qq.com"
    FLASK_POSTS_PER_PAGE = 10
    UPLOAD_FOLDER = basedir + '\uplodes'

    @staticmethod
    def init_app(app):
        pass

class DevelopmentConfig(Config):
    MAIL_SERVER = 'smtp.qq.com'
    MAIL_PROT = 465
    MAIL_USE_TLS = True
    MAIL_USE_SSL = False
    MAIL_USERNAME = "xianth123@qq.com"
    MAIL_PASSWORD = "qmozujeaouqdgadg"
    MAIL_DEBUG = True
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'data.sqlite')

class TextingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'data.sqlite')

class ProductionConfig(Config):
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'data.sqlite')

config = {
    'development': DevelopmentConfig,
    'testing': TextingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}

