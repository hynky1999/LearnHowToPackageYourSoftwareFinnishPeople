from decouple import config
import os
basedir = os.path.abspath(os.path.dirname(__file__))


class Config(object):

    # seret key is set in __ini__.py
    #SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'

    LANGUAGES = ['en', 'fi', 'fa', 'el', 'it', 'zh']

    """
    #SQLITE3 connection settings: 

    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    """

    # MariaDB mysql database settings

    MYSQL_USER = config('MYSQL_USER')
    MYSQL_PASSWORD = config('MYSQL_PASSWORD')
    MYSQL_SERVER = config('MYSQL_SERVER')
    MYSQL_DB = config('MYSQL_DB')

    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://'+MYSQL_USER+':' + \
        MYSQL_PASSWORD+'@'+MYSQL_SERVER+'/'+MYSQL_DB+'?charset=utf8mb4'

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": 300,
        "max_overflow": 30,
        "pool_size": 20
    }

    TEMPLATES_AUTO_RELOAD = True

    DEBUG = True
