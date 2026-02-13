"""
Configurações centralizadas do Sistema Jurídico MP
"""
import os
from urllib.parse import quote_plus
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))

class Config:
    """Configurações base do sistema"""
    
    # Secret Key
    SECRET_KEY = os.getenv('SECRET_KEY', 'chave-padrao-dev-mudar-em-producao')
    
    # Banco de Dados
    DB_USER = os.getenv('DB_USER')
    DB_PASSWORD = os.getenv('DB_PASSWORD')
    DB_HOST = os.getenv('DB_HOST')
    DB_NAME = os.getenv('DB_NAME')
    
    # Encode credenciais para URL
    user_encoded = quote_plus(DB_USER) if DB_USER else ''
    pass_encoded = quote_plus(DB_PASSWORD) if DB_PASSWORD else ''
    
    SQLALCHEMY_DATABASE_URI = f'mysql+pymysql://{user_encoded}:{pass_encoded}@{DB_HOST}/{DB_NAME}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {'pool_recycle': 280}
    
    # Flask-Login
    LOGIN_VIEW = 'auth.login'
    
    # Paginação
    ITEMS_PER_PAGE = 10
    
    # Upload de arquivos
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max
    ALLOWED_EXTENSIONS = {'xlsx', 'xls', 'csv'}
    
    @staticmethod
    def init_app(app):
        pass

class DevelopmentConfig(Config):
    """Configurações de desenvolvimento"""
    DEBUG = True

class ProductionConfig(Config):
    """Configurações de produção"""
    DEBUG = False

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
