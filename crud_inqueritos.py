import pymysql
from flask import Flask, render_template, request, redirect, url_for, flash
import os 
from dotenv import load_dotenv
from datetime import datetime
import traceback 
import re
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from io import StringIO
import csv 
import math 

load_dotenv()
basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))

# ===============================================
# 1. CONEXÃO COM MYSQL
# ===============================================

def conectar():
    try:
        conn = pymysql.connect(
            host=os.getenv('DB_HOST'),      
            user=os.getenv('DB_USER'),      
            password=os.getenv('DB_PASSWORD'), 
            database=os.getenv('DB_NAME'),  
            charset='utf8mb4',
            cursorclass=pymysql.cursors.Cursor
        )
        return conn
    except pymysql.Error as e:
        print(f"ERRO DE CONEXÃO COM MYSQL: {e}")
        return None

# ===============================================
# 2. FLASK + LOGIN
# ===============================================

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'chave-padrao-dev')

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class User(UserMixin):
    def __init__(self, id, username, password):
        self.id = id
        self.username = username
        self.password = password

USERS = {
    1: User(1, "gabriel.cintra", "Web010203")
}

@login_manager.user_loader
def load_user(user_id):
    return USERS.get(int(user_id))

# ===============================================
# 3. CRIAÇÃO/ALTERAÇÃO DE TABELAS
# ===============================================

def criar_tabela_se_nao_existe():
    conn = conectar()
    if conn is None: return
    try:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS inqueritos (
                id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
                num_controle VARCHAR(255),
                num_eletronico VARCHAR(255) NOT NULL UNIQUE,
                ano INTEGER NOT NULL,
                num_processo VARCHAR(255),
                data_conclusao DATE,
                delegacia VARCHAR(255),
                data_ultima_atualizacao DATE,
                status VARCHAR(255),
                equipe VARCHAR(255),
                concluir_mes TINYINT(1) DEFAULT 0,
                is_cota TINYINT(1) DEFAULT 0
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)
        
        # ATENÇÃO: Adicionamos is_cota aqui também para o histórico
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS inqueritos_concluidos (
                id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
                num_controle VARCHAR(255),
                num_eletronico VARCHAR(255) NOT NULL,
                ano INTEGER NOT NULL,
                num_processo VARCHAR(255),
                data_conclusao DATE,
                mes INTEGER NOT NULL,
                ano_ref INTEGER NOT NULL,
                data_relato DATE,
                ano_conclusao INTEGER NOT NULL,
                data_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_cota TINYINT(1) DEFAULT 0
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)
        conn.commit()
    except Exception as e:
        print("ERRO AO CRIAR TABELAS:", e)
    finally:
        if conn: conn.close()

def atualizar_tabela_cota():
    """Garante que a coluna is_cota exista nas DUAS tabelas"""
    conn = conectar()
    if conn is None: return
    try:
        cursor = conn.cursor()
        # 1. Tabela Principal
        try:
            cursor.execute("ALTER TABLE inqueritos ADD COLUMN is_cota TINYINT(1) DEFAULT 0")
            print("✅ Coluna 'is_cota' adicionada em 'inqueritos'")
        except: pass 

        # 2. Tabela de Concluídos (NOVO)
        try:
            cursor.execute("ALTER TABLE inqueritos_concluidos ADD COLUMN is_cota TINYINT(1) DEFAULT 0")
            print("✅ Coluna 'is_cota' adicionada em 'inqueritos_concluidos'")
        except: pass
        
        conn.commit()
    finally:
        if conn: conn.close()

# ===============================================
# 4. FUNÇÕES AUXILIARES
# ===============================================

def formatar_data(data_str):
    if not data_str: return None
    data_str = data_str.strip()
    try:
        return datetime.strptime(data_str, '%d/%m/%Y').date()
    except ValueError:
        try:
            return datetime.strptime(data_str, '%Y-%m-%d').date()
        except ValueError:
            return None

def verificar_numero_eletronico(num):
    conn = conectar()
    if conn is None: return True
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM inqueritos WHERE num_eletronico = %s", (num,))
        return cursor.fetchone() is not None
    finally:
        if conn: conn.close()

# ===============================================
# 5. CRUD (LEITURAS COM DICT CURSOR)
# ===============================================

def criar_inquerito_manual(num_controle, num_eletronico, ano, num_processo, data_conclusao, is_cota):
    conn = conectar()
    if conn is None: return
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO inqueritos
            (num_controle, num_eletronico, ano, num_processo, data_conclusao, is_cota)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (num_controle, num_eletronico, ano, num_processo, data_conclusao, is_cota))
        conn.commit()
        flash("Inquérito cadastrado!", "success")
    except Exception as e:
        flash(f"Erro: {e}", "danger")
        if conn: conn.rollback()
    finally:
        if conn: conn.close()

def listar_inqueritos(ordenar_por='ano', direcao='DESC', busca=None, pagina=1, itens_por_pagina=10):
    conn = conectar()
    if conn is None: return [], 0

    colunas_permitidas = ['id', 'num_controle', 'num_eletronico', 'ano', 'data_conclusao']
    if ordenar_por not in colunas_permitidas: ordenar_por = 'ano'
    if direcao.upper() not in ['ASC', 'DESC']: direcao = 'DESC'
    offset = (pagina - 1) * itens_por_pagina

    try:
        cursor = conn.cursor(pymysql.cursors.DictCursor) # DictCursor
        where_clause = ""
        params = []
        
        if busca:
            termo = f"%{busca}%"
            where_clause = "WHERE num_eletronico LIKE %s OR num_controle LIKE %s OR num_processo LIKE %s"
            params = [termo, termo, termo]

        cursor.execute(f"SELECT COUNT(*) as total FROM inqueritos {where_clause}", params)
        total_registros = cursor.fetchone()['total']

        sql_data = f"SELECT * FROM inqueritos {where_clause} ORDER BY {ordenar_por} {direcao} LIMIT %s OFFSET %s"
        params.extend([itens_por_pagina, offset])
        
        cursor.execute(sql_data, params)
        return cursor.fetchall(), total_registros
    except Exception as e:
        print(f"Erro listar: {e}")
        return [], 0
    finally:
        if conn: conn.close()

def buscar_inquerito(id):
    conn = conectar()
    if conn is None: return
    try:
        cursor = conn.cursor(pymysql.cursors.DictCursor) # DictCursor
        cursor.execute("SELECT * FROM inqueritos WHERE id=%s", (id,))
        return cursor.fetchone()
    finally:
        if conn: conn.close()

def atualizar_inquerito(id, num_controle, num_eletronico, ano, num_processo, data_conclusao, is_cota):
    conn = conectar()
    if conn is None: return
    try:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE inqueritos
            SET num_controle=%s, num_eletronico=%s, ano=%s,
                num_processo=%s, data_conclusao=%s, is_cota=%s
            WHERE id=%s
        """, (num_controle, num_eletronico, ano, num_processo, data_conclusao, is_cota, id))
        conn.commit()
        flash("Atualizado!", "success")
    except Exception as e:
        flash(f"Erro: {e}", "danger")
        if conn: conn.rollback()
    finally:
        if conn: conn.close()

def deletar_inquerito(id):
    conn = conectar()
    if conn is None: return
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM inqueritos WHERE id=%s", (id,))
        conn.commit()
        flash("Excluído!", "success")
    except Exception as e:
        flash(f"Erro: {e}", "danger")
        if conn: conn.rollback()
    finally:
        if conn: conn.close()

# ===============================================
# 6. FLUXO DE CONCLUSÃO (ATUALIZADO PARA COTA)
# ===============================================

def marcar_concluir(id, novo_valor):
    conn = conectar()
    if conn is None: return
    try:
        cursor = conn.cursor()
        cursor.execute("UPDATE inqueritos SET concluir_mes=%s WHERE id=%s", (novo_valor, id))
        conn.commit()
    except Exception as e:
        if conn: conn.rollback()
    finally:
        if conn: conn.close()

def listar_para_concluir_mes():
    conn = conectar()
    if conn is None: return []
    try:
        cursor = conn.cursor(pymysql.cursors.DictCursor) # DictCursor para segurança no template
        cursor.execute("SELECT * FROM inqueritos WHERE concluir_mes = 1 ORDER BY data_conclusao ASC")
        return cursor.fetchall()
    finally:
        if conn: conn.close()

def mover_para_concluidos(id):
    conn = conectar()
    if conn is None: return False
    try:
        # Lê como Dict para pegar os campos pelo nome
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        cursor.execute("SELECT * FROM inqueritos WHERE id=%s", (id,))
        item = cursor.fetchone()
        if not item: return False

        # Dados base
        data_conclusao = item['data_conclusao']
        data_ref = data_conclusao if data_conclusao else datetime.now().date()
        
        # INSERÇÃO (Agora incluindo is_cota)
        cursor_insert = conn.cursor() # Cursor normal para insert
        cursor_insert.execute("""
            INSERT INTO inqueritos_concluidos
            (num_controle, num_eletronico, ano, num_processo, data_conclusao,
             mes, ano_ref, ano_conclusao, data_relato, is_cota)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,CURDATE(), %s)
        """, (
            item['num_controle'], 
            item['num_eletronico'], 
            item['ano'], 
            item['num_processo'], 
            item['data_conclusao'], 
            data_ref.month, 
            data_ref.year, 
            data_ref.year,
            item['is_cota'] # <--- LEVANDO A COTA JUNTO
        ))

        cursor_insert.execute("DELETE FROM inqueritos WHERE id=%s", (id,))
        conn.commit()
        return True
    except Exception as e:
        print(f"Erro mover: {e}")
        if conn: conn.rollback()
        return False
    finally:
        if conn: conn.close()

def listar_inqueritos_concluidos(mes, ano):
    conn = conectar()
    if conn is None: return []
    try:
        cursor = conn.cursor(pymysql.cursors.DictCursor) # DictCursor
        # Adicionamos is_cota ao SELECT
        cursor.execute("""
            SELECT id, num_eletronico, num_processo, data_conclusao, data_relato, num_controle, data_registro, is_cota
            FROM inqueritos_concluidos
            WHERE mes = %s AND ano_ref = %s
            ORDER BY data_relato DESC
        """, (mes, ano))
        return cursor.fetchall()
    finally:
        if conn: conn.close()

def desfazer_relato(id):
    conn = conectar()
    if conn is None: return False
    try:
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        cursor.execute("SELECT * FROM inqueritos_concluidos WHERE id=%s", (id,))
        item = cursor.fetchone() 
        if not item: return False

        cursor_insert = conn.cursor()
        # Ao restaurar, mantemos o status de Cota original!
        cursor_insert.execute("""
            INSERT INTO inqueritos (
                num_controle, num_eletronico, ano, num_processo, data_conclusao, concluir_mes, is_cota
            ) VALUES (%s, %s, %s, %s, %s, 0, %s) 
        """, (
            item['num_controle'], 
            item['num_eletronico'], 
            item['ano'], 
            item['num_processo'], 
            item['data_conclusao'],
            item['is_cota'] # <--- RESTAURANDO A COTA
        ))

        cursor_insert.execute("DELETE FROM inqueritos_concluidos WHERE id=%s", (id,))
        conn.commit()
        return True
    except Exception as e:
        print(f"Erro desfazer: {e}")
        if conn: conn.rollback()
        return False
    finally:
        if conn: conn.close()

def inserir_em_massa(dados):
    conn = conectar()
    if conn is None:
        flash("Erro de conexão.", "danger")
        return 0
    
    # ... (Lógica de importação mantida igual, apenas garantindo que is_cota=0 no insert padrão)
    # Para economizar espaço, mantenha sua função inserir_em_massa anterior, 
    # ela já inseria com is_cota=0, então está compatível.
    # Vou resumir aqui para completar o arquivo:
    reader = csv.reader(StringIO(dados), delimiter='\t')
    try: next(reader) 
    except: pass
    linhas = 0
    try:
        cursor = conn.cursor()
        for row in reader:
            if len(row) < 7: continue
            try:
                if verificar_numero_eletronico(row[0].strip()): continue
                cursor.execute("""
                    INSERT INTO inqueritos (num_eletronico, ano, delegacia, data_ultima_atualizacao, 
                    data_conclusao, status, equipe, is_cota) VALUES (%s, %s, %s, %s, %s, %s, %s, 0)
                """, (row[0].strip(), int(row[1]), row[2], formatar_data(row[3]), formatar_data(row[4]), row[5], row[6]))
                linhas += 1
            except: pass
        conn.commit()
        flash(f"Importado: {linhas}", "success")
        return linhas
    except Exception as e:
        return 0
    finally:
        if conn: conn.close()

# ===============================================
# 7. ROTAS (IGUAIS AO ANTERIOR, COMPATÍVEIS COM DICT)
# ===============================================

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated: return redirect(url_for('index'))
    if request.method == 'POST':
        if request.form['username'] == USERS[1].username and request.form['password'] == USERS[1].password:
            login_user(USERS[1])
            return redirect(url_for('index'))
        flash("Erro login", "danger")
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/')
@login_required
def index():
    ordem = request.args.get('ordem', 'ano')
    direcao = request.args.get('dir', 'DESC')
    busca = request.args.get('q', '')
    pagina = int(request.args.get('page', 1))
    dados, total = listar_inqueritos(ordem, direcao, busca, pagina)
    paginas = math.ceil(total / 10)
    return render_template('index.html', inqueritos=dados, ordem_atual=ordem, dir_atual=direcao, busca_atual=busca, total=total, pagina_atual=pagina, total_paginas=paginas)

@app.route('/adicionar', methods=['POST'])
@login_required
def adicionar():
    is_cota = 1 if 'is_cota' in request.form else 0
    # ... capturar outros campos ...
    # Simplificado para caber na resposta, use sua logica de captura
    try:
        criar_inquerito_manual(request.form['num_controle'], request.form['num_eletronico'], int(request.form['ano']), request.form['num_processo'], formatar_data(request.form['data_conclusao']), is_cota)
    except: flash("Erro dados", "danger")
    return redirect(url_for('index'))

@app.route('/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar(id):
    item = buscar_inquerito(id)
    if not item: return redirect(url_for('index'))
    if request.method == 'POST':
        is_cota = 1 if 'is_cota' in request.form else 0
        atualizar_inquerito(id, request.form['num_controle'], request.form['num_eletronico'], int(request.form['ano']), request.form['num_processo'], formatar_data(request.form['data_conclusao']), is_cota)
        return redirect(url_for('index'))
    data_iso = item['data_conclusao'].isoformat() if item['data_conclusao'] else ""
    return render_template('editar.html', inquerito=item, data_conclusao_iso=data_iso)

@app.route('/deletar/<int:id>')
@login_required
def deletar(id):
    deletar_inquerito(id)
    return redirect(url_for('index'))

@app.route('/marcar_concluir/<int:id>')
@login_required
def rota_marcar_concluir(id):
    marcar_concluir(id, int(request.args.get('v', 1)))
    return redirect(url_for('index'))

@app.route('/concluir_mes')
@login_required
def concluir_mes():
    hoje = datetime.now()
    dados = listar_para_concluir_mes()
    return render_template('concluir_mes.html', inqueritos=dados, mes=hoje.month, ano=hoje.year)

@app.route('/relatar/<int:id>', methods=['POST'])
@login_required
def relatar(id):
    mover_para_concluidos(id)
    return redirect(url_for('concluir_mes'))

@app.route('/relatorios')
@login_required
def relatorios():
    hoje = datetime.now()
    mes = int(request.args.get('mes', hoje.month))
    ano = int(request.args.get('ano', hoje.year))
    dados = listar_inqueritos_concluidos(mes, ano)
    return render_template('relatorios.html', inqueritos=dados, mes_atual=mes, ano_atual=ano, anos_disponiveis=list(range(hoje.year-2, hoje.year+1)), meses_do_ano=[(1,'Jan'),(2,'Fev'),(3,'Mar'),(4,'Abr'),(5,'Mai'),(6,'Jun'),(7,'Jul'),(8,'Ago'),(9,'Set'),(10,'Out'),(11,'Nov'),(12,'Dez')])

@app.route('/desfazer_relato/<int:id>')
@login_required
def rota_desfazer_relato(id):
    desfazer_relato(id)
    return redirect(url_for('relatorios'))

@app.route('/importar_massa', methods=['GET', 'POST'])
@login_required
def importar_massa():
    if request.method == 'POST': inserir_em_massa(request.form.get('dados_inqueritos', ''))
    return render_template('importar.html')

if __name__ == '__main__':
    criar_tabela_se_nao_existe()
    atualizar_tabela_cota() # Atualiza as duas tabelas agora
    app.run(debug=True)