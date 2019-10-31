import os
basedir = os.path.abspath(os.path.dirname(__file__))


# base class include common configure
class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'hard to guess string'  # the secret key for creating encryption to \
                                                                         # protect form data from CSRF attack by flask-WTF
    SQLALCHEMY_COMMIT_ON_TEARDOWN = True  # the key for commiting db changes autoly after every end of require

    SQLALCHEMY_POOL_SIZE = 100

    @staticmethod
    def init_app(app):  # initialize configure
        pass


class DevelopmentConfig(Config):
    DEBUG = True
    #SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL') or \
    #    'sqlite:///' + os.path.join(basedir, 'data-dev.sqlite')
    #SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://sa:123456@localhost/equipmentsdb'    # '?charset=utf8' is need if insert chinese
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://sa:123456@47.104.179.47/dp_questionnaire_sys?autocommit=true'
    # SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://dp_tester:123456@localhost/dp_questionnaire_sys?autocommit=true'
    SQLALCHEMY_TRACK_MODIFICATIONS = False


class ProductionConfig(Config):
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://sa:123456@47.104.179.47/dp_questionnaire_sys?autocommit=true'
    # SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://dp_tester:123456@localhost/dp_questionnaire_sys?autocommit=true'
    SQLALCHEMY_TRACK_MODIFICATIONS = False



config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,

    'default': DevelopmentConfig
}


logconfigs = {
    "version": 1,
    "disable_existing_loggers": False,

    "formatters": {
        "simple": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        }
    },

    "handlers": {

        "console": {
            "class": "logging.StreamHandler",
            "level": "DEBUG",
            "formatter": "simple",
            "stream": "ext://sys.stdout"
        },

        "info_file_handler": {
            "class": "logging.handlers.TimedRotatingFileHandler",
            "level": "INFO",
            "formatter": "simple",
            "filename": "./logs/info.log",
            "when": "midnight",
            "backupCount": 20,
            "encoding": "utf8",
            "filters": [
                "filter_by_name",
            ]
        },

        "error_file_handler": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "ERROR",
            "formatter": "simple",
            "filename": "./logs/errors.log",
            "maxBytes": 1024*1024*10,      # 日志大小10M
            "backupCount": 20,             # 最多保存20份日志，写完时轮转
            "encoding": "utf8"
        }
    },

    "filters": {
        "filter_by_name": {
            "class": "logging.Filter",
            "name": "root"
        }
    },

    "loggers": {
        "mymodule": {
            "level": "INFO",
            "handlers": [
                "info_file_handler",
                "error_file_handler"
            ],
            "propagate": "no"
        }
    },

        "root": {
            "level": "INFO",
            "handlers": [
                # "console",
                "info_file_handler",
                "error_file_handler"
            ]
        }
}