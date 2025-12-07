# Arquivo: crud_inqueritos.py

import psycopg2
from flask import Flask, render_template, request, redirect, url_for, flash
from datetime import datetime
import csv
from io import StringIO
import re 
import os
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user # Flask-Login

# ===============================================
# 1. CONFIGURAÇÃO DE CONEXÃO COM POSTGRESQL (LOCAL)
# ===============================================
# DB_NAME = "inqueritos_db"       
# DB_USER = "postgres"
# DB_PASS = "Gco@010203"      # <<< SUA SENHA LOCAL FIXA >>>
# DB_HOST = "localhost"
# DB_PORT = "5432"
DATABASE_URL = os.getenv("DATABASE_URL")
DB_NAME = os.environ.get("DB_NAME")       
DB_USER = os.environ.get("DB_USER")
DB_PASS = os.environ.get("DB_PASS")
DB_HOST = os.environ.get("DB_HOST")
DB_PORT = os.environ.get("DB_PORT")

app = Flask(__name__)
# Chave secreta para Flash e Flask-Login (fixa localmente)
app.secret_key = 'chave_muito_secreta_para_flash' 

# ===============================================
# 2. CONFIGURAÇÃO DO FLASK-LOGIN
# ===============================================

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login' 

# --- MODELO E AUTENTICAÇÃO DE USUÁRIO ---

class User(UserMixin):
    """Classe para representar um usuário do sistema."""
    def __init__(self, id, username, password):
        self.id = id
        self.username = username
        self.password = password

# Usuário de Teste Único (Credenciais fixas para acesso local)
USERS = {
    1: User(1, "gabriel.cintra", "Web010203") 
}

@login_manager.user_loader
def load_user(user_id):
    """Função obrigatória para recarregar o usuário a partir do ID da sessão."""
    return USERS.get(int(user_id))

# -----------------------------------------------
# 3. FUNÇÕES DE CONEXÃO E ESTRUTURA (ORDEM CORRETA PARA INICIALIZAÇÃO)
# -----------------------------------------------

def conectar():
    """Conecta ao banco de dados PostgreSQL usando Variáveis de Ambiente."""
    try:
        conn = psycopg2.connect(
            # Passando os valores diretamente das Variáveis de Ambiente
            dbname=os.environ.get("DB_NAME"),
            user=os.environ.get("DB_USER"),
            password=os.environ.get("DB_PASS"),
            host=os.environ.get("DB_HOST"), 
            port=os.environ.get("DB_PORT") 
        )
        return conn
    except psycopg2.Error as e:
        # Se houver erro, ele será impresso no log do Render
        print(f"ERRO DE CONEXÃO NO RENDER: {e}") 
        return None

# ESTA FUNÇÃO ESTÁ AGORA DEFINIDA ANTES DE SER CHAMADA NO FINAL DO ARQUIVO
def criar_tabela_se_nao_existe():
    """Cria a tabela de inquéritos se ela ainda não existir."""
    conn = conectar()
    if conn is None: return
    try:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS inqueritos (
                id SERIAL PRIMARY KEY,
                num_controle TEXT,
                num_eletronico TEXT NOT NULL,
                ano INTEGER NOT NULL,
                num_processo TEXT,
                data_conclusao DATE,
                delegacia TEXT,
                data_ultima_atualizacao DATE,
                status TEXT,
                equipe TEXT
            )
        """)
        conn.commit()
    finally:
        if conn: conn.close()

# --- FUNÇÕES AUXILIARES DE PROCESSAMENTO ---
def formatar_data(data_str):
    if not data_str:
        return None
    try:
        return datetime.strptime(data_str, '%d/%m/%Y').date()
    except ValueError:
        return None

# -----------------------------------------------
# 4. FUNÇÕES CRUD
# -----------------------------------------------

def criar_inquerito_manual(num_controle, num_eletronico, ano, num_processo, data_conclusao):
    conn = conectar()
    if conn is None: return
    try:
        cursor = conn.cursor()
        sql = """
            INSERT INTO inqueritos (num_controle, num_eletronico, ano, num_processo, data_conclusao)
            VALUES (%s, %s, %s, %s, %s)
        """
        cursor.execute(sql, (num_controle, num_eletronico, ano, num_processo, data_conclusao))
        conn.commit()
        flash("Inquérito cadastrado com sucesso!", "success")
    except Exception as e:
        flash(f"Erro ao cadastrar inquérito: {e}", "danger")
        conn.rollback()
    finally:
        if conn: conn.close()

def listar_inqueritos(ordenar_por='ano', direcao='DESC'):
    conn = conectar()
    if conn is None: return []
    
    colunas_validas = {'ano': 'ano', 'num_controle': 'num_controle', 'data_conclusao': 'data_conclusao'}
    direcoes_validas = {'ASC', 'DESC'}
    
    coluna = colunas_validas.get(ordenar_por, 'ano')
    direcao = direcao if direcao in direcoes_validas else 'DESC'
    
    try:
        cursor = conn.cursor()
        sql = f"SELECT * FROM inqueritos ORDER BY {coluna} {direcao}"
        cursor.execute(sql)
        inqueritos = cursor.fetchall()
        return inqueritos
    finally:
        if conn: conn.close()

def buscar_inquerito(id):
    conn = conectar()
    if conn is None: return None
    try:
        cursor = conn.cursor()
        sql = "SELECT * FROM inqueritos WHERE id = %s"
        cursor.execute(sql, (id,))
        return cursor.fetchone()
    finally:
        if conn: conn.close()

def atualizar_inquerito(id, num_controle, num_eletronico, ano, num_processo, data_conclusao):
    conn = conectar()
    if conn is None: return
    try:
        cursor = conn.cursor()
        sql = """
            UPDATE inqueritos SET num_controle = %s, num_eletronico = %s, ano = %s, 
            num_processo = %s, data_conclusao = %s 
            WHERE id = %s
        """
        cursor.execute(sql, (num_controle, num_eletronico, ano, num_processo, data_conclusao, id))
        conn.commit()
        flash("Inquérito atualizado com sucesso!", "success")
    except Exception as e:
        flash(f"Erro ao atualizar inquérito: {e}", "danger")
        conn.rollback()
    finally:
        if conn: conn.close()

def deletar_inquerito(id):
    conn = conectar()
    if conn is None: return
    try:
        cursor = conn.cursor()
        sql = "DELETE FROM inqueritos WHERE id = %s"
        cursor.execute(sql, (id,))
        conn.commit()
        flash("Inquérito excluído com sucesso!", "success")
    except Exception as e:
        flash(f"Erro ao excluir inquérito: {e}", "danger")
        conn.rollback()
    finally:
        if conn: conn.close()

def inserir_em_massa(dados_csv):
    conn = conectar()
    if conn is None: return 0
    linhas_inseridas = 0
    linhas_com_erro = 0

    f = StringIO(dados_csv)
    f.readline() 
    reader = csv.reader(f, delimiter='\t') 

    try:
        cursor = conn.cursor()
        sql = """
            INSERT INTO inqueritos (num_eletronico, ano, delegacia, data_ultima_atualizacao, data_conclusao, status, equipe)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        for row in reader:
            if not row or len(row) < 7: continue 
            
            try:
                num_eletronico = row[0]
                
                match = re.search(r'\.(\d{4})\.', num_eletronico)
                ano = int(match.group(1)) if match else 0
                
                delegacia = row[2]
                data_atualizacao = formatar_data(row[3])
                data_conclusao = formatar_data(row[4])
                status = row[5]
                equipe = row[6]
                
                cursor.execute(sql, (num_eletronico, ano, delegacia, data_atualizacao, data_conclusao, status, equipe))
                linhas_inseridas += 1
            except Exception as row_e:
                linhas_com_erro += 1
                print(f"Erro ao processar linha: {row}, Erro: {row_e}")

        conn.commit()
        if linhas_com_erro > 0:
             flash(f"Atenção! {linhas_inseridas} inquéritos importados, mas {linhas_com_erro} linhas tiveram erro de formatação.", "warning")
        else:
            flash(f"Sucesso! {linhas_inseridas} inquéritos importados.", "success")
        return linhas_inseridas
    except Exception as e:
        conn.rollback()
        flash(f"Erro fatal na importação: {e}", "danger")
        return 0
    finally:
        if conn: conn.close()

def contar_total_registros():
    conn = conectar()
    if conn is None: return 0
    total = 0
    try:
        cursor = conn.cursor()
        sql = "SELECT COUNT(*) FROM inqueritos"
        cursor.execute(sql)
        total = cursor.fetchone()[0] 
        return total
    except Exception as e:
        print(f"Erro ao contar registros: {e}")
        return 0
    finally:
        if conn: conn.close()    

# -----------------------------------------------
# 5. ROTAS DE AUTENTICAÇÃO
# -----------------------------------------------

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Rota para exibir o formulário de login e processar a submissão."""
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = USERS.get(1) 
        
        if user and user.username == username and user.password == password:
            login_user(user) 
            flash('Login bem-sucedido!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Usuário ou senha inválidos.', 'danger')
            return redirect(url_for('login'))
            
    return render_template('login.html')

@app.route('/logout')
@login_required 
def logout():
    """Rota para encerrar a sessão do usuário."""
    logout_user()
    flash('Você saiu do sistema.', 'info')
    return redirect(url_for('login'))


# -----------------------------------------------
# 6. ROTAS FLASK PROTEGIDAS (ADICIONAR @login_required)
# -----------------------------------------------

@app.route('/')
@login_required 
def index():
    """Página principal que lista os inquéritos."""
    ordenar_por = request.args.get('ordem', 'ano')
    direcao = request.args.get('dir', 'DESC')
    
    inqueritos = listar_inqueritos(ordenar_por, direcao)
    total_registros = contar_total_registros() 
    
    return render_template('index.html', 
                            inqueritos=inqueritos,
                            ordem_atual=ordenar_por,
                            dir_atual=direcao,
                            total=total_registros)

@app.route('/adicionar', methods=['POST'])
@login_required 
def adicionar():
    """Processa a adição manual de um novo inquérito."""
    num_controle = request.form['num_controle']
    num_eletronico = request.form['num_eletronico']
    
    try:
        ano = int(request.form['ano'])
    except ValueError:
        flash("Erro: O campo Ano deve ser um número válido.", "danger")
        return redirect(url_for('index'))
        
    num_processo = request.form['num_processo']
    data_conclusao_str = request.form['data_conclusao']
    
    data_conclusao = formatar_data(data_conclusao_str)
    
    criar_inquerito_manual(num_controle, num_eletronico, ano, num_processo, data_conclusao)
    return redirect(url_for('index'))

@app.route('/editar/<int:id>', methods=['GET', 'POST'])
@login_required 
def editar(id):
    """Exibe o formulário de edição e processa a atualização."""
    inquerito = buscar_inquerito(id)
    if not inquerito:
        flash("Inquérito não encontrado!", "danger")
        return redirect(url_for('index'))

    if request.method == 'POST':
        num_controle = request.form['num_controle']
        num_eletronico = request.form['num_eletronico']
        
        try:
            ano = int(request.form['ano'])
        except ValueError:
            flash("Erro: O campo Ano deve ser um número válido.", "danger")
            return redirect(url_for('index'))
            
        num_processo = request.form['num_processo']
        data_conclusao = formatar_data(request.form['data_conclusao'])
        
        atualizar_inquerito(id, num_controle, num_eletronico, ano, num_processo, data_conclusao)
        return redirect(url_for('index'))
    
    data_conclusao_iso = inquerito[5].isoformat() if inquerito[5] else ''
    
    return render_template('editar.html', 
                            inquerito=inquerito, 
                            data_conclusao_iso=data_conclusao_iso)

@app.route('/deletar/<int:id>')
@login_required 
def deletar(id):
    """Processa a exclusão de um inquérito."""
    deletar_inquerito(id)
    return redirect(url_for('index'))

@app.route('/importar_massa', methods=['GET', 'POST'])
@login_required 
def importar_massa():
    """Exibe o formulário de importação e processa o CSV/TXT."""
    if request.method == 'POST':
        dados_brutos = request.form.get('dados_inqueritos', '')
        if dados_brutos:
            inserir_em_massa(dados_brutos)
        else:
            flash("Nenhum dado fornecido para importação.", "warning")
        
        return redirect(url_for('index'))
        
    return render_template('importar.html')

# --- INICIALIZAÇÃO DO SERVIDOR ---
if __name__ == '__main__':
    # Esta chamada agora está no local correto, garantindo que a função exista.
    criar_tabela_se_nao_existe() 
    app.run(debug=True)