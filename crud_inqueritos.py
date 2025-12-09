import pymysql
from flask import Flask, render_template, request, redirect, url_for, flash
from datetime import datetime
import traceback 
import re
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from io import StringIO
import csv 



# ===============================================
# 1. CONEXÃO COM MYSQL REMOTO
# ===============================================

def conectar():
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
        print(f"ERRO: {e}")
        return None

# ===============================================
# 2. FLASK + LOGIN
# ===============================================

app = Flask(__name__)
app.secret_key = 'chave_muito_secreta_para_flash'

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class User(UserMixin):
    # Usuário de exemplo: usar um DB real para usuários seria ideal
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
    if conn is None:
        return
    try:
        cursor = conn.cursor()

        # Tabela principal 'inqueritos'
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
                concluir_mes TINYINT(1) DEFAULT 0
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)
        
        # Tabela 'inqueritos_concluidos' (Mantida, mas deveria ser refatorada)
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
                data_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)

        conn.commit()

    except Exception as e:
        print("ERRO AO CRIAR TABELAS:", e)
    finally:
        if conn: conn.close()

# ===============================================
# 4. FUNÇÕES AUXILIARES
# ===============================================

def formatar_data(data_str):
    if not data_str:
        return None
    data_str = data_str.strip()
    try:
        # Tenta DD/MM/AAAA (para formulário de inclusão)
        return datetime.strptime(data_str, '%d/%m/%Y').date()
    except ValueError:
        try:
            # Tenta YYYY-MM-DD (para input type="date" do HTML5)
            return datetime.strptime(data_str, '%Y-%m-%d').date()
        except ValueError:
            return None

def verificar_numero_eletronico(num):
    conn = conectar()
    if conn is None:
        return True
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM inqueritos WHERE num_eletronico = %s", (num,))
        return cursor.fetchone() is not None
    finally:
        if conn: conn.close()

# ===============================================
# 5. CRUD
# ===============================================

def criar_inquerito_manual(num_controle, num_eletronico, ano, num_processo, data_conclusao):
    # Já verificado na rota antes de chamar
    conn = conectar()
    if conn is None:
        return
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO inqueritos
            (num_controle, num_eletronico, ano, num_processo, data_conclusao)
            VALUES (%s, %s, %s, %s, %s)
        """, (num_controle, num_eletronico, ano, num_processo, data_conclusao))
        conn.commit()
        flash("Inquérito cadastrado!", "success")
    except Exception as e:
        flash(f"Erro: {e}", "danger")
        if conn: conn.rollback() # ✅ Rollback adicionado
    finally:
        if conn: conn.close()

def listar_inqueritos(ordenar_por='ano', direcao='DESC'):
    conn = conectar()
    if conn is None:
        return []

    # Proteção contra Injeção de SQL em ORDER BY
    colunas_permitidas = ['id', 'num_controle', 'num_eletronico', 'ano', 'data_conclusao']
    direcoes_permitidas = ['ASC', 'DESC']
    
    if ordenar_por not in colunas_permitidas:
        ordenar_por = 'ano'
        
    direcao = direcao.upper()
    if direcao not in direcoes_permitidas:
        direcao = 'DESC'

    try:
        cursor = conn.cursor()
        # SQL seguro (variáveis de ordenação são pré-validadas)
        sql = f"SELECT * FROM inqueritos ORDER BY {ordenar_por} {direcao}"
        cursor.execute(sql)
        return cursor.fetchall()
    finally:
        if conn: conn.close()

def buscar_inquerito(id):
    conn = conectar()
    if conn is None:
        return
    try:
        cursor = conn.cursor()
        # Uso de placeholder (%s) para proteção
        cursor.execute("SELECT * FROM inqueritos WHERE id=%s", (id,))
        return cursor.fetchone()
    finally:
        if conn: conn.close()

def atualizar_inquerito(id, num_controle, num_eletronico, ano, num_processo, data_conclusao):
    conn = conectar()
    if conn is None:
        return
    try:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE inqueritos
            SET num_controle=%s, num_eletronico=%s, ano=%s,
                num_processo=%s, data_conclusao=%s
            WHERE id=%s
        """, (num_controle, num_eletronico, ano, num_processo, data_conclusao, id))
        conn.commit()
        flash("Atualizado!", "success")
    except Exception as e:
        flash(f"Erro: {e}", "danger")
        if conn: conn.rollback() # ✅ Rollback adicionado
    finally:
        if conn: conn.close()

def deletar_inquerito(id):
    conn = conectar()
    if conn is None:
        return
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM inqueritos WHERE id=%s", (id,))
        conn.commit()
        flash("Excluído!", "success")
    except Exception as e:
        flash(f"Erro: {e}", "danger")
        if conn: conn.rollback() # ✅ Rollback adicionado
    finally:
        if conn: conn.close()

# ===============================================
# 6. NOVO — CHECKBOX CONCLUIR MÊS
# ===============================================

def marcar_concluir(id, novo_valor):
    conn = conectar()
    if conn is None:
        return
    try:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE inqueritos
            SET concluir_mes=%s
            WHERE id=%s
        """, (novo_valor, id))
        conn.commit()
    except Exception as e:
        print(f"Erro ao marcar concluir: {e}")
        if conn: conn.rollback() # ✅ Rollback adicionado
    finally:
        if conn: conn.close()

def listar_para_concluir_mes():
    conn = conectar()
    if conn is None:
        return []
    try:
        cursor = conn.cursor()
        # A consulta agora filtra APENAS pela marcação do usuário (concluir_mes = 1)
        cursor.execute("""
            SELECT *
            FROM inqueritos
            WHERE concluir_mes = 1
            ORDER BY data_conclusao ASC
        """)
        return cursor.fetchall()
    finally:
        if conn: conn.close()


# crud_inqueritos.py (Busque e modifique a função mover_para_concluidos)

def mover_para_concluidos(id):
    conn = conectar()
    # ... (código de conexão e busca do item) ...

    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM inqueritos WHERE id=%s", (id,))
        item = cursor.fetchone()

        # ... (check if item exists) ...

        num_controle = item[1]
        num_eletronico = item[2]
        ano = item[3]
        num_processo = item[4]
        data_conclusao = item[5] 

        # --- ✅ CORREÇÃO APLICADA AQUI ---
        data_referencia = data_conclusao
        if data_referencia is None:
            # Se não houver data de conclusão, usa a data atual (data do relato)
            data_referencia = datetime.now().date()
            
        mes = data_referencia.month
        ano_ref = data_referencia.year
        # -----------------------------------
        
        # ... (segue o print de debug) ...
        
        # O restante do INSERT já está correto:
        params = (num_controle, num_eletronico, ano, num_processo, data_conclusao, mes, ano_ref, ano_ref)
        
        cursor.execute("""
            INSERT INTO inqueritos_concluidos
            (num_controle, num_eletronico, ano, num_processo, data_conclusao,
             mes, ano_ref, ano_conclusao, data_relato)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,CURDATE())
        """, params)

        cursor.execute("DELETE FROM inqueritos WHERE id=%s", (id,))
        conn.commit()
        return True

    except Exception as e:
        # ... (código de rollback) ...
        pass
    finally:
        # ... (código de close) ...
        pass


# crud_inqueritos.py (Busque e modifique a função desfazer_relato)

def desfazer_relato(id):
    conn = conectar()
    if conn is None:
        print("desfazer_relato: conexão retornou None")
        return False

    try:
        cursor = conn.cursor()
        
        # 1. Busca os dados do inquérito concluído PELOS NOMES DOS CAMPOS
        # Esta consulta traz EXATAMENTE 5 campos, garantindo o mapeamento (item[0] a item[4])
        cursor.execute("""
            SELECT 
                num_controle, num_eletronico, ano, num_processo, data_conclusao
            FROM inqueritos_concluidos 
            WHERE id=%s
        """, (id,))
        item = cursor.fetchone() 

        if not item:
            print(f"desfazer_relato: registro id={id} não encontrado em concluídos")
            return False

        # Mapeamento dos campos essenciais
        num_controle = item[0]
        num_eletronico = item[1]
        ano = item[2] 
        num_processo = item[3]
        data_conclusao = item[4]
        
        # 2. Insere de volta na tabela principal 'inqueritos'
        # Inserimos APENAS os 5 campos que extraímos + o campo obrigatório 'concluir_mes'.
        # Os campos delegacia, status, etc., serão preenchidos com NULL por omissão.
        cursor.execute("""
            INSERT INTO inqueritos (
                num_controle, num_eletronico, ano, num_processo, data_conclusao, 
                concluir_mes
            )
            VALUES (%s, %s, %s, %s, %s, %s) 
        """, (
            num_controle, 
            num_eletronico, 
            ano,  # O valor de ano é passado aqui
            num_processo, 
            data_conclusao, 
            0 # concluir_mes
        ))

        # 3. Deleta da tabela 'inqueritos_concluidos'
        cursor.execute("DELETE FROM inqueritos_concluidos WHERE id=%s", (id,))
        
        conn.commit()
        print(f"desfazer_relato: sucesso id={id}")
        return True

    except Exception as e:
        print("Erro desfazer relato (traceback):")
        traceback.print_exc()
        try:
            if conn: conn.rollback()
        except Exception:
            pass
        return False
    finally:
        try:
            if conn: conn.close()
        except Exception:
            pass


def inserir_em_massa(dados):
    conn = conectar()
    if conn is None:
        flash("Erro de conexão com o banco de dados.", "danger")
        return 0

    reader = csv.reader(StringIO(dados), delimiter='\t')
    next(reader)  # Pula o cabeçalho
    linhas_inseridas = 0
    erros = []

    try:
        cursor = conn.cursor()
        for i, row in enumerate(reader):
            if len(row) < 7:
                erros.append(f"Linha {i+2}: Dados incompletos.")
                continue

            try:
                # 0: Nº Inquérito (num_eletronico)
                # 1: Ano
                # 2: Delegacia
                # 3: Data Última Atualização
                # 4: Data Conclusão
                # 5: Status
                # 6: Equipe
                
                num_eletronico = row[0].strip()
                ano = int(row[1].strip())
                delegacia = row[2].strip() or None
                data_ultima_atualizacao = formatar_data(row[3])
                data_conclusao = formatar_data(row[4])
                status = row[5].strip() or 'Em Cartório'
                equipe = row[6].strip() or None
                
                # Campos não fornecidos na importação, usar None
                num_controle = None 
                num_processo = None
                
                if verificar_numero_eletronico(num_eletronico):
                    erros.append(f"Linha {i+2}: Nº Eletrônico '{num_eletronico}' já existe. Ignorado.")
                    continue

                cursor.execute("""
                    INSERT INTO inqueritos (
                        num_eletronico, ano, delegacia, data_ultima_atualizacao, 
                        data_conclusao, status, equipe, num_controle, num_processo
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (num_eletronico, ano, delegacia, data_ultima_atualizacao, 
                      data_conclusao, status, equipe, num_controle, num_processo))
                
                linhas_inseridas += 1

            except ValueError:
                erros.append(f"Linha {i+2}: Erro de formato (Ano ou Data inválida).")
            except Exception as e:
                erros.append(f"Linha {i+2}: Erro de DB: {e}")

        conn.commit()
        
        if linhas_inseridas > 0:
            flash(f"Importação concluída: {linhas_inseridas} inquéritos inseridos.", "success")
        
        if erros:
            flash(f"Atenção: {len(erros)} erros ocorreram durante a importação.", "warning")
            for erro in erros:
                print(f"Erro de Importação: {erro}")
        
        return linhas_inseridas
    except Exception as e:
        flash(f"Erro fatal na importação: {e}", "danger")
        if conn: conn.rollback()
        return 0
    finally:
        if conn: conn.close()

# ===============================================
# 7. NOVAS FUNÇÕES PARA RELATÓRIOS
# ===============================================

def listar_inqueritos_concluidos(mes, ano):
    conn = conectar()
    if conn is None:
        return []
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                id,                
                num_eletronico, 
                num_processo, 
                data_conclusao, 
                data_relato, 
                num_controle,
                data_registro
            FROM inqueritos_concluidos
            WHERE mes = %s AND ano_ref = %s
            ORDER BY data_relato DESC
        """, (mes, ano))
        return cursor.fetchall()
    finally:
        if conn: conn.close()


# ===============================================
# 7. ROTAS
# ===============================================

# ... (ROTAS DE LOGIN/LOGOUT SEM ALTERAÇÃO) ...
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = USERS.get(1)

        if user.username == username and user.password == password:
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

@app.route('/marcar_concluir/<int:id>')
@login_required
def rota_marcar_concluir(id):
    novo_valor = int(request.args.get('v', 1))
    marcar_concluir(id, novo_valor)
    return redirect(url_for('index'))

@app.route('/concluir_mes')
@login_required
def concluir_mes():
    hoje = datetime.now()
    mes = hoje.month
    ano = hoje.year    
    
    dados = listar_para_concluir_mes() 
    
    return render_template('concluir_mes.html', inqueritos=dados, mes=mes, ano=ano)


@app.route('/relatar/<int:id>', methods=['GET', 'POST'])
@login_required
def relatar(id):
    # chama mover
    success = mover_para_concluidos(id)
    if success:
        flash("Inquérito relatado e removido da lista principal.", "success")
    else:
        flash("Erro ao relatar. Verifique o log do servidor (console) para o traceback.", "danger")
    return redirect(url_for('concluir_mes'))



@app.route('/adicionar', methods=['POST'])
@login_required
def adicionar():
    num_controle = request.form['num_controle']
    num_eletronico = request.form['num_eletronico']
    
    try:
        ano = int(request.form['ano'])
    except ValueError:
        flash("Ano deve ser um número válido.", "danger")
        return redirect(url_for('index'))
        
    num_processo = request.form['num_processo']
    data = formatar_data(request.form['data_conclusao'])

    if verificar_numero_eletronico(num_eletronico):
        flash("Este Nº Eletrônico já está cadastrado.", "danger")
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
        
        try:
            ano = int(request.form['ano'])
        except ValueError:
            flash("Ano deve ser um número válido.", "danger")
            return redirect(url_for('editar', id=id))
            
        num_processo = request.form['num_processo']
        # ✅ Agora formatar_data aceita YYYY-MM-DD do input type="date"
        data = formatar_data(request.form['data_conclusao']) 

        if num_eletronico != item[2] and verificar_numero_eletronico(num_eletronico):
            flash("Este Nº Eletrônico já está cadastrado.", "danger")
            return redirect(url_for('editar', id=id))

        atualizar_inquerito(id, num_controle, num_eletronico, ano, num_processo, data)
        return redirect(url_for('index'))

    # Para usar o input type="date", o formato deve ser YYYY-MM-DD (ISO)
    data_conclusao_iso = item[5].isoformat() if item[5] else ""
    return render_template('editar.html', inquerito=item, data_conclusao_iso=data_conclusao_iso)

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
            # A função inserir_em_massa agora lida com feedback via flash
            inserir_em_massa(dados) 
        else:
            flash("Sem dados para importar.", "warning")
        return redirect(url_for('index'))
    return render_template('importar.html')



@app.route('/relatorios', methods=['GET'])
@login_required
def relatorios():
    hoje = datetime.now()
    
    # Pega os parâmetros do URL, ou usa o mês e ano atuais como padrão
    try:
        mes = int(request.args.get('mes', hoje.month))
        ano = int(request.args.get('ano', hoje.year))
    except ValueError:
        # Em caso de erro de conversão, volta para o mês/ano atual
        mes = hoje.month
        ano = hoje.year

    dados = listar_inqueritos_concluidos(mes, ano)
    
    # Cria uma lista de anos para o seletor (2 anos passados até o ano atual)
    anos_disponiveis = list(range(hoje.year - 2, hoje.year + 1))
    
    return render_template('relatorios.html', 
                           inqueritos=dados, 
                           mes_atual=mes, 
                           ano_atual=ano,
                           anos_disponiveis=anos_disponiveis,
                           meses_do_ano=[
                               (1, 'Janeiro'), (2, 'Fevereiro'), (3, 'Março'), (4, 'Abril'),
                               (5, 'Maio'), (6, 'Junho'), (7, 'Julho'), (8, 'Agosto'),
                               (9, 'Setembro'), (10, 'Outubro'), (11, 'Novembro'), (12, 'Dezembro')
                           ])

@app.route('/desfazer_relato/<int:id>')
@login_required
def rota_desfazer_relato(id):
    success = desfazer_relato(id)
    if success:
        flash("Inquérito restaurado para a lista principal e removido dos relatórios.", "success")
    else:
        flash("Erro ao desfazer relato. Verifique o log do servidor.", "danger")
        
    # Redireciona de volta para a tela de relatórios
    return redirect(url_for('relatorios'))



# ===============================================
# 8. EXECUÇÃO LOCAL
# ===============================================

def contar_total_registros():
    conn = conectar()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM inqueritos")
        return cursor.fetchone()[0]
    finally:
        if conn: conn.close()

if __name__ == '__main__':
    criar_tabela_se_nao_existe()
    app.run(debug=True)