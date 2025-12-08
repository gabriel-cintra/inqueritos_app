import pymysql
from flask import Flask, render_template, request, redirect, url_for, flash
from datetime import datetime
import csv
from io import StringIO
import re
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user



# ===============================================
# 1. CONEXÃO REMOTA COM MYSQL
# ===============================================

def conectar():
    """Conecta ao MySQL remoto."""
    try:
        conn = pymysql.connect(
            host='gabrielcintra.mysql.pythonanywhere-services.com',
            user='gabrielcintra',
            password='Gco@010203',
            database='gabrielcintra$default',
            charset='utf8mb4',
            cursorclass=pymysql.cursors.Cursor
        )
        return conn
    except pymysql.Error as e:
        print(f"ERRO DE CONEXÃO COM MYSQL: {e}")
        return None


# ===============================================
# 2. CONFIGURAÇÃO DO FLASK + LOGIN
# ===============================================

app = Flask(__name__)
app.secret_key = 'chave_muito_secreta_para_flash'

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
# 3. CRIAÇÃO DA TABELA
# ===============================================

def criar_tabela_se_nao_existe():
    conn = conectar()
    if conn is None:
        return
    try:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS inqueritos (
                id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
                num_controle TEXT,
                num_eletronico TEXT NOT NULL,
                ano INTEGER NOT NULL,
                num_processo TEXT,
                data_conclusao DATE,
                delegacia TEXT,
                data_ultima_atualizacao DATE,
                status TEXT,
                equipe TEXT
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)

        # Garante unicidade do número eletrônico
        try:
            cursor.execute("""
                ALTER TABLE inqueritos
                ADD UNIQUE (num_eletronico)
            """)
        except:
            pass  # Já existe

        conn.commit()
    except Exception as e:
        print(f"ERRO AO CRIAR TABELA: {e}")
    finally:
        conn.close()


def formatar_data(data_str):
    if not data_str:
        return None
    try:
        return datetime.strptime(data_str, '%d/%m/%Y').date()
    except ValueError:
        return None


# ===============================================
# 4. FUNÇÕES CRUD
# ===============================================

def verificar_numero_eletronico(num_eletronico):
    """Verifica se o número eletrônico já existe no banco."""
    conn = conectar()
    if conn is None:
        return True
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id FROM inqueritos WHERE num_eletronico = %s",
            (num_eletronico,)
        )
        resultado = cursor.fetchone()
        return resultado is not None
    finally:
        conn.close()


def criar_inquerito_manual(num_controle, num_eletronico, ano, num_processo, data_conclusao):

    # Verificação de duplicidade
    if verificar_numero_eletronico(num_eletronico):
        flash("O Nº Eletrônico informado já está cadastrado.", "danger")
        return

    conn = conectar()
    if conn is None:
        return
    try:
        cursor = conn.cursor()
        sql = """
            INSERT INTO inqueritos
            (num_controle, num_eletronico, ano, num_processo, data_conclusao)
            VALUES (%s, %s, %s, %s, %s)
        """
        cursor.execute(sql, (num_controle, num_eletronico, ano, num_processo, data_conclusao))
        conn.commit()
        flash("Inquérito cadastrado com sucesso!", "success")
    except Exception as e:
        flash(f"Erro ao cadastrar: {e}", "danger")
        conn.rollback()
    finally:
        conn.close()


def listar_inqueritos(ordenar_por='ano', direcao='DESC'):
    conn = conectar()
    if conn is None:
        return []
    try:
        coluna = ordenar_por if ordenar_por in ['ano', 'num_controle', 'data_conclusao'] else 'ano'
        direcao = direcao if direcao in ['ASC', 'DESC'] else 'DESC'

        cursor = conn.cursor()
        cursor.execute(f"SELECT * FROM inqueritos ORDER BY {coluna} {direcao}")
        return cursor.fetchall()
    finally:
        conn.close()


def buscar_inquerito(id):
    conn = conectar()
    if conn is None:
        return None
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM inqueritos WHERE id = %s", (id,))
        return cursor.fetchone()
    finally:
        conn.close()


def atualizar_inquerito(id, num_controle, num_eletronico, ano, num_processo, data_conclusao):
    conn = conectar()
    if conn is None:
        return
    try:
        cursor = conn.cursor()
        sql = """
            UPDATE inqueritos
            SET num_controle=%s, num_eletronico=%s, ano=%s,
                num_processo=%s, data_conclusao=%s
            WHERE id=%s
        """
        cursor.execute(sql, (num_controle, num_eletronico, ano, num_processo, data_conclusao, id))
        conn.commit()
        flash("Atualizado com sucesso!", "success")
    except Exception as e:
        flash(f"Erro ao atualizar: {e}", "danger")
        conn.rollback()
    finally:
        conn.close()


def deletar_inquerito(id):
    conn = conectar()
    if conn is None:
        return
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM inqueritos WHERE id = %s", (id,))
        conn.commit()
        flash("Excluído com sucesso!", "success")
    except Exception as e:
        flash(f"Erro ao excluir: {e}", "danger")
        conn.rollback()
    finally:
        conn.close()


def inserir_em_massa(dados_csv):
    conn = conectar()
    if conn is None:
        return 0

    linhas_ok = 0
    linhas_erro = 0

    f = StringIO(dados_csv)
    f.readline()
    reader = csv.reader(f, delimiter='\t')

    try:
        cursor = conn.cursor()
        sql = """
            INSERT INTO inqueritos
            (num_eletronico, ano, delegacia, data_ultima_atualizacao,
             data_conclusao, status, equipe)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """

        for row in reader:
            if len(row) < 7:
                continue

            try:
                num_eletronico = row[0]

                # Ignora duplicados silenciosamente
                if verificar_numero_eletronico(num_eletronico):
                    linhas_erro += 1
                    continue

                ano_match = re.search(r'\.(\d{4})\.', num_eletronico)
                ano = int(ano_match.group(1)) if ano_match else 0

                delegacia = row[2]
                data_atualizacao = formatar_data(row[3])
                data_conclusao = formatar_data(row[4])
                status = row[5]
                equipe = row[6]

                cursor.execute(sql, (num_eletronico, ano, delegacia,
                                     data_atualizacao, data_conclusao,
                                     status, equipe))
                linhas_ok += 1

            except Exception as e:
                print("Erro na linha CSV:", e)
                linhas_erro += 1

        conn.commit()

        if linhas_erro > 0:
            flash(f"{linhas_ok} registros importados; {linhas_erro} duplicados/erro.", "warning")
        else:
            flash(f"Importação concluída: {linhas_ok} itens.", "success")

    except Exception as e:
        flash(f"Erro na importação: {e}", "danger")
        conn.rollback()
    finally:
        conn.close()


def contar_total_registros():
    conn = conectar()
    if conn is None:
        return 0
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM inqueritos")
        return cursor.fetchone()[0]
    finally:
        conn.close()


# ===============================================
# 5. ROTAS
# ===============================================

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = USERS.get(1)

        if user and user.username == username and user.password == password:
            login_user(user)
            return redirect(url_for('index'))

        flash("Credenciais inválidas.", "danger")

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
    ordem = request.args.get('ordem', 'ano')
    direcao = request.args.get('dir', 'DESC')
    dados = listar_inqueritos(ordem, direcao)
    total = contar_total_registros()
    return render_template('index.html',
                           inqueritos=dados,
                           ordem_atual=ordem,
                           dir_atual=direcao,
                           total=total)


@app.route('/adicionar', methods=['POST'])
@login_required
def adicionar():

    num_controle = request.form['num_controle']
    num_eletronico = request.form['num_eletronico']
    ano = int(request.form['ano'])
    num_processo = request.form['num_processo']
    data = formatar_data(request.form['data_conclusao'])

    # Validação de duplicidade
    if verificar_numero_eletronico(num_eletronico):
        flash("O Nº Eletrônico informado já está cadastrado.", "danger")
        return redirect(url_for('index'))

    criar_inquerito_manual(num_controle, num_eletronico, ano, num_processo, data)
    return redirect(url_for('index'))


@app.route('/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar(id):
    item = buscar_inquerito(id)
    if not item:
        flash("Não encontrado.", "danger")
        return redirect(url_for('index'))

    if request.method == 'POST':
        num_controle = request.form['num_controle']
        num_eletronico = request.form['num_eletronico']
        ano = int(request.form['ano'])
        num_processo = request.form['num_processo']
        data = formatar_data(request.form['data_conclusao'])

        # Validação de duplicidade somente quando o número for alterado
        if num_eletronico != item[2] and verificar_numero_eletronico(num_eletronico):
            flash("Este Nº Eletrônico já está registrado em outro inquérito.", "danger")
            return redirect(url_for('editar', id=id))

        atualizar_inquerito(id, num_controle, num_eletronico, ano, num_processo, data)
        return redirect(url_for('index'))

    data_iso = item[5].isoformat() if item[5] else ""

    return render_template('editar.html', inquerito=item, data_conclusao_iso=data_iso)


@app.route('/deletar/<int:id>')
@login_required
def deletar(id):
    deletar_inquerito(id)
    return redirect(url_for('index'))


@app.route('/importar_massa', methods=['GET', 'POST'])
@login_required
def importar_massa():
    if request.method == 'POST':
        dados = request.form.get('dados_inqueritos', '')
        if dados.strip():
            inserir_em_massa(dados)
        else:
            flash("Nenhum dado fornecido.", "warning")

        return redirect(url_for('index'))

    return render_template('importar.html')


# ===============================================
# 6. EXECUÇÃO LOCAL
# ===============================================

if __name__ == '__main__':
    criar_tabela_se_nao_existe()
    app.run(debug=True)
