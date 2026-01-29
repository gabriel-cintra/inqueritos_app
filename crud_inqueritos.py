import os
from datetime import datetime
import math
import csv
from io import StringIO
# NOVOS IMPORTS PARA O PANDAS
import pandas as pd
from urllib.parse import quote_plus
from dotenv import load_dotenv

from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash

# ===============================================
# 1. CONFIGURAÇÃO E EXTENSÕES
# ===============================================

load_dotenv()
basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'chave-padrao-dev')

# Configuração da URL do Banco de Dados para SQLAlchemy
db_user = os.getenv('DB_USER')
db_pass = os.getenv('DB_PASSWORD')
db_host = os.getenv('DB_HOST')
db_name = os.getenv('DB_NAME')

user_encoded = quote_plus(db_user)
pass_encoded = quote_plus(db_pass)

app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql+pymysql://{user_encoded}:{pass_encoded}@{db_host}/{db_name}'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {'pool_recycle': 280}

db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# ===============================================
# 2. MODELOS (REPRESENTAM AS TABELAS)
# ===============================================

class User(UserMixin, db.Model):
    __tablename__ = 'usuarios'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Inquerito(db.Model):
    __tablename__ = 'inqueritos'
    id = db.Column(db.Integer, primary_key=True)
    num_controle = db.Column(db.String(255))
    num_eletronico = db.Column(db.String(255), unique=True, nullable=False)
    ano = db.Column(db.Integer, nullable=False)
    num_processo = db.Column(db.String(255))
    data_conclusao = db.Column(db.Date)
    delegacia = db.Column(db.String(255))
    data_ultima_atualizacao = db.Column(db.Date)
    status = db.Column(db.String(255))
    equipe = db.Column(db.String(255))
    concluir_mes = db.Column(db.Boolean, default=False)
    is_cota = db.Column(db.Boolean, default=False)

class InqueritoConcluido(db.Model):
    __tablename__ = 'inqueritos_concluidos'
    id = db.Column(db.Integer, primary_key=True)
    num_controle = db.Column(db.String(255))
    num_eletronico = db.Column(db.String(255), nullable=False)
    ano = db.Column(db.Integer, nullable=False)
    num_processo = db.Column(db.String(255))
    data_conclusao = db.Column(db.Date)
    mes = db.Column(db.Integer, nullable=False)
    ano_ref = db.Column(db.Integer, nullable=False)
    ano_conclusao = db.Column(db.Integer, nullable=False)
    data_relato = db.Column(db.Date)
    data_registro = db.Column(db.DateTime, default=datetime.utcnow)
    is_cota = db.Column(db.Boolean, default=False)

# ===============================================
# 3. HELPER FUNCTIONS & LOGIN LOADER
# ===============================================

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def formatar_data(data_str):
    if not data_str: return None
    data_str = data_str.strip()
    for fmt in ('%d/%m/%Y', '%Y-%m-%d'):
        try:
            return datetime.strptime(data_str, fmt).date()
        except ValueError:
            pass
    return None

def criar_admin_padrao():
    if not User.query.filter_by(username="gabriel.cintra").first():
        admin = User(username="gabriel.cintra")
        admin.set_password("Web010203")
        db.session.add(admin)
        db.session.commit()
        print("✅ Usuário Admin criado/restaurado.")

# ===============================================
# 4. ROTAS
# ===============================================

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated: return redirect(url_for('index'))
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('index'))
        flash("Usuário ou senha inválidos.", "danger")
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash("Sessão encerrada.", "info")
    return redirect(url_for('login'))

@app.route('/')
@login_required
def index():
    ordem_col = request.args.get('ordem', 'ano')
    direcao = request.args.get('dir', 'DESC')
    busca = request.args.get('q', '')
    page = request.args.get('page', 1, type=int)
    per_page = 10

    query = Inquerito.query

    if busca:
        t = f"%{busca}%"
        query = query.filter(
            (Inquerito.num_eletronico.like(t)) | 
            (Inquerito.num_controle.like(t)) | 
            (Inquerito.num_processo.like(t))
        )

    if direcao == 'DESC':
        query = query.order_by(getattr(Inquerito, ordem_col).desc())
    else:
        query = query.order_by(getattr(Inquerito, ordem_col).asc())

    paginacao = query.paginate(page=page, per_page=per_page, error_out=False)
    
    return render_template('index.html',
                           inqueritos=paginacao.items,
                           pagination=paginacao,
                           ordem_atual=ordem_col,
                           dir_atual=direcao,
                           busca_atual=busca,
                           total=paginacao.total,
                           pagina_atual=page,
                           total_paginas=paginacao.pages)

@app.route('/adicionar', methods=['POST'])
@login_required
def adicionar():
    try:
        novo = Inquerito(
            num_controle=request.form['num_controle'],
            num_eletronico=request.form['num_eletronico'],
            ano=int(request.form['ano']),
            num_processo=request.form['num_processo'],
            data_conclusao=formatar_data(request.form['data_conclusao']),
            is_cota=(1 if 'is_cota' in request.form else 0)
        )
        
        if Inquerito.query.filter_by(num_eletronico=novo.num_eletronico).first():
            flash("Nº Eletrônico já existe!", "danger")
            return redirect(url_for('index'))

        db.session.add(novo)
        db.session.commit()
        flash("Inquérito cadastrado!", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Erro ao adicionar: {e}", "danger")
    
    return redirect(url_for('index'))

@app.route('/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar(id):
    item = Inquerito.query.get_or_404(id)
    
    if request.method == 'POST':
        item.num_controle = request.form['num_controle']
        novo_eletronico = request.form['num_eletronico']
        item.ano = int(request.form['ano'])
        item.num_processo = request.form['num_processo']
        item.data_conclusao = formatar_data(request.form['data_conclusao'])
        item.is_cota = (1 if 'is_cota' in request.form else 0)

        if novo_eletronico != item.num_eletronico:
            if Inquerito.query.filter_by(num_eletronico=novo_eletronico).first():
                flash("Este Nº Eletrônico já existe em outro registro.", "danger")
                return render_template('editar.html', inquerito=item, data_conclusao_iso=str(item.data_conclusao) if item.data_conclusao else "")
            item.num_eletronico = novo_eletronico

        try:
            db.session.commit()
            flash("Atualizado com sucesso!", "success")
            return redirect(url_for('index'))
        except Exception as e:
            db.session.rollback()
            flash(f"Erro: {e}", "danger")

    data_iso = item.data_conclusao.isoformat() if item.data_conclusao else ""
    return render_template('editar.html', inquerito=item, data_conclusao_iso=data_iso)

@app.route('/deletar/<int:id>')
@login_required
def deletar(id):
    item = Inquerito.query.get_or_404(id)
    try:
        db.session.delete(item)
        db.session.commit()
        flash("Excluído!", "success")
    except:
        db.session.rollback()
        flash("Erro ao excluir.", "danger")
    return redirect(url_for('index'))

@app.route('/marcar_concluir/<int:id>')
@login_required
def rota_marcar_concluir(id):
    item = Inquerito.query.get_or_404(id)
    item.concluir_mes = bool(int(request.args.get('v', 0)))
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/concluir_mes')
@login_required
def concluir_mes():
    hoje = datetime.now()
    dados = Inquerito.query.filter_by(concluir_mes=True).order_by(Inquerito.data_conclusao.asc()).all()
    return render_template('concluir_mes.html', inqueritos=dados, mes=hoje.month, ano=hoje.year)

@app.route('/relatar/<int:id>', methods=['POST'])
@login_required
def relatar(id):
    item = Inquerito.query.get_or_404(id)
    data_ref = item.data_conclusao if item.data_conclusao else datetime.now().date()
    concluido = InqueritoConcluido(
        num_controle=item.num_controle,
        num_eletronico=item.num_eletronico,
        ano=item.ano,
        num_processo=item.num_processo,
        data_conclusao=item.data_conclusao,
        mes=data_ref.month,
        ano_ref=data_ref.year,
        ano_conclusao=data_ref.year,
        data_relato=datetime.now().date(),
        is_cota=item.is_cota
    )
    try:
        db.session.add(concluido)
        db.session.delete(item)
        db.session.commit()
        flash("Relatado e Arquivado.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Erro ao relatar: {e}", "danger")
    return redirect(url_for('concluir_mes'))

@app.route('/relatorios')
@login_required
def relatorios():
    hoje = datetime.now()
    mes = request.args.get('mes', hoje.month, type=int)
    ano = request.args.get('ano', hoje.year, type=int)
    dados = InqueritoConcluido.query.filter_by(mes=mes, ano_ref=ano).order_by(InqueritoConcluido.data_relato.desc()).all()
    return render_template('relatorios.html', 
                           inqueritos=dados, 
                           mes_atual=mes, ano_atual=ano,
                           anos_disponiveis=list(range(hoje.year-2, hoje.year+1)),
                           meses_do_ano=[(1,'Jan'),(2,'Fev'),(3,'Mar'),(4,'Abr'),(5,'Mai'),(6,'Jun'),(7,'Jul'),(8,'Ago'),(9,'Set'),(10,'Out'),(11,'Nov'),(12,'Dez')])

@app.route('/desfazer_relato/<int:id>')
@login_required
def rota_desfazer_relato(id):
    concluido = InqueritoConcluido.query.get_or_404(id)
    restaurado = Inquerito(
        num_controle=concluido.num_controle,
        num_eletronico=concluido.num_eletronico,
        ano=concluido.ano,
        num_processo=concluido.num_processo,
        data_conclusao=concluido.data_conclusao,
        is_cota=concluido.is_cota,
        concluir_mes=False
    )
    try:
        db.session.add(restaurado)
        db.session.delete(concluido)
        db.session.commit()
        flash("Restaurado para a lista principal.", "success")
    except:
        db.session.rollback()
        flash("Erro ao restaurar.", "danger")
    return redirect(url_for('relatorios'))

@app.route('/importar_massa', methods=['GET', 'POST'])
@login_required
def importar_massa():
    if request.method == 'POST':
        dados = request.form.get('dados_inqueritos', '')
        reader = csv.reader(StringIO(dados), delimiter='\t')
        try: next(reader) 
        except: pass
        count = 0
        erros = 0
        for row in reader:
            if len(row) < 7: continue
            try:
                num_eletronico = row[0].strip()
                if Inquerito.query.filter_by(num_eletronico=num_eletronico).first():
                    continue
                novo = Inquerito(
                    num_eletronico=num_eletronico,
                    ano=int(row[1].strip()),
                    delegacia=row[2].strip() or None,
                    data_ultima_atualizacao=formatar_data(row[3]),
                    data_conclusao=formatar_data(row[4]),
                    status=row[5].strip() or 'Em Cartório',
                    equipe=row[6].strip() or None,
                    is_cota=False
                )
                db.session.add(novo)
                count += 1
            except:
                erros += 1
        try:
            db.session.commit()
            flash(f"Importados: {count}. Erros/Duplicados: {erros}", "success")
        except:
            db.session.rollback()
            flash("Erro crítico na importação.", "danger")
        return redirect(url_for('index'))
    return render_template('importar.html')

# ===============================================
# ATUALIZAÇÃO: ROTA COMPARADOR COM ORDENAÇÃO
# ===============================================
@app.route('/comparar_vencidos', methods=['GET', 'POST'])
@login_required
def comparar_vencidos():
    resultados = []
    nao_encontrados = []
    
    if request.method == 'POST':
        if 'arquivo_excel' not in request.files:
            flash("Nenhum arquivo enviado.", "danger")
            return redirect(request.url)
        
        file = request.files['arquivo_excel']
        if file.filename == '':
            flash("Nenhum arquivo selecionado.", "danger")
            return redirect(request.url)
            
        try:
            # Lê o Excel
            df = pd.read_excel(file)
            df.dropna(how='all', inplace=True)
            
            # Tenta achar a coluna 'Nº Inquérito' ou pega a primeira
            coluna_chave = None
            for col in df.columns:
                if 'inquérito' in str(col).lower() or 'inquerito' in str(col).lower():
                    coluna_chave = col
                    break
            if not coluna_chave:
                coluna_chave = df.columns[0]
                
            # Lista limpa do Excel (remove espaços e converte pra string)
            lista_excel = df[coluna_chave].dropna().astype(str).str.strip().tolist()
            
            # 1. Busca no banco todos de uma vez
            # Usamos set(lista_excel) na query para evitar buscar duplicados desnecessariamente
            resultados = Inquerito.query.filter(Inquerito.num_eletronico.in_(lista_excel)).all()
            
            # 2. Lógica de Ordenação Inteligente (Ano Crescente + Nº Controle Numérico Crescente)
            def chave_ordenacao(inq):
                # Tenta converter num_controle para inteiro para ordenar corretamente (1, 2, 10...)
                # Se não for número (ex: tem letra), joga pro final da lista
                try:
                    nc = int(inq.num_controle)
                except (ValueError, TypeError):
                    nc = 9999999
                return (inq.ano, nc)

            # Aplica a ordenação na lista de resultados
            resultados.sort(key=chave_ordenacao)
            
            # 3. Verifica quais não foram encontrados (Comparando quem veio do banco com a lista do Excel)
            encontrados_set = {iq.num_eletronico for iq in resultados}
            # Mantém a ordem original do Excel para os não encontrados, apenas para conferência
            for num in lista_excel:
                if num not in encontrados_set:
                    nao_encontrados.append(num)
            
            if not resultados:
                flash("Nenhum inquérito do arquivo foi encontrado na base de dados.", "warning")
            else:
                flash(f"Processamento concluído! {len(resultados)} registros localizados e ordenados.", "success")
                
        except Exception as e:
            flash(f"Erro ao processar o arquivo: {str(e)}", "danger")

    return render_template('comparar_vencidos.html', resultados=resultados, nao_encontrados=nao_encontrados)

# ===============================================
# 5. INICIALIZAÇÃO
# ===============================================

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        criar_admin_padrao()
    app.run(debug=True)