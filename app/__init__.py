"""
Inicialização da aplicação Flask
"""
from flask import Flask, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from config import config

# Inicializar extensões
db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()

def create_app(config_name='default'):
    """Factory function para criar a aplicação"""
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)
    
    # Inicializar extensões com a app
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    
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
    
    # ===== CRIAÇÃO FORÇADA DAS TABELAS DE BOLETINS =====
    with app.app_context():
        # Importar modelos para garantir que estão registrados
        from app.models.user import User
        from app.models.inquerito import Inquerito, InqueritoConcluido
        from app.models.boletim import Boletim, BoletimConcluir, BoletimFinalizado
        
        # Criar todas as tabelas (se não existirem)
        db.create_all()
        print("✅ Verificação/criação de tabelas concluída!")
        
        # Verificar se as tabelas de boletins foram criadas
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        tabelas = inspector.get_table_names()
        
        if 'boletins' in tabelas:
            print("✅ Tabela 'boletins' OK")
        else:
            print("❌ ERRO: Tabela 'boletins' não foi criada!")
            
        if 'boletins_concluir' in tabelas:
            print("✅ Tabela 'boletins_concluir' OK")
        else:
            print("❌ ERRO: Tabela 'boletins_concluir' não foi criada!")
            
        if 'boletins_finalizados' in tabelas:
            print("✅ Tabela 'boletins_finalizados' OK")
        else:
            print("❌ ERRO: Tabela 'boletins_finalizados' não foi criada!")
        
        # Criar usuário admin padrão
        if not User.query.filter_by(username="gabriel.cintra").first():
            admin = User(username="gabriel.cintra")
            admin.set_password("Web010203")
            db.session.add(admin)
            db.session.commit()
            print("✅ Usuário Admin criado/restaurado.")
    
    return app