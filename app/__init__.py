"""
Inicialização da aplicação Flask
"""
from flask import Flask, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate  # <-- NOVO IMPORT
from config import config

# Inicializar extensões
db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()  # <-- NOVA INSTÂNCIA

def create_app(config_name='default'):
    """Factory function para criar a aplicação"""
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)
    
    # Inicializar extensões com a app
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)  # <-- INICIALIZAR MIGRATE
    
    login_manager.login_view = 'auth.login'
    
    # Registrar blueprints
    from app.routes import auth, inqueritos, boletins
    
    app.register_blueprint(auth.bp)
    app.register_blueprint(inqueritos.bp)
    app.register_blueprint(boletins.bp)
    
    # ROTA RAIZ - Redireciona para inquéritos
    @app.route('/')
    def index():
        return redirect(url_for('inqueritos.index'))
    
    return app