"""
Script de Migração - Adicionar colunas data_cadastro e prazo_verificado
Executa automaticamente as alterações no banco de dados MySQL
"""

import os
import sys
from datetime import datetime
import pymysql
from dotenv import load_dotenv
from urllib.parse import quote_plus

# ===============================================
# CONFIGURAÇÃO
# ===============================================

# Carrega variáveis de ambiente
basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))

# Configurações do banco
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_HOST = os.getenv('DB_HOST')
DB_NAME = os.getenv('DB_NAME')

# ===============================================
# FUNÇÕES AUXILIARES
# ===============================================

def conectar_banco():
    """Estabelece conexão com o banco de dados MySQL"""
    try:
        conexao = pymysql.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )
        print("✅ Conexão com o banco de dados estabelecida!")
        return conexao
    except Exception as e:
        print(f"❌ Erro ao conectar ao banco: {e}")
        sys.exit(1)

def verificar_coluna_existe(cursor, tabela, coluna):
    """Verifica se uma coluna já existe na tabela"""
    sql = f"""
        SELECT COUNT(*) as existe 
        FROM information_schema.COLUMNS 
        WHERE TABLE_SCHEMA = '{DB_NAME}' 
        AND TABLE_NAME = '{tabela}' 
        AND COLUMN_NAME = '{coluna}'
    """
    cursor.execute(sql)
    resultado = cursor.fetchone()
    return resultado['existe'] > 0

def fazer_backup_tabela(cursor, conexao, tabela):
    """Cria uma tabela de backup antes da migração"""
    try:
        nome_backup = f"{tabela}_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        sql = f"CREATE TABLE {nome_backup} AS SELECT * FROM {tabela}"
        cursor.execute(sql)
        conexao.commit()
        print(f"✅ Backup criado: {nome_backup}")
        return nome_backup
    except Exception as e:
        print(f"⚠️  Aviso: Não foi possível criar backup: {e}")
        return None

def executar_migracao(cursor, conexao):
    """Executa a migração adicionando as novas colunas"""
    
    tabela = 'inqueritos'
    migracoes_executadas = []
    
    print("\n" + "="*60)
    print("INICIANDO MIGRAÇÃO DO BANCO DE DADOS")
    print("="*60 + "\n")
    
    # 1. Verificar e adicionar coluna data_cadastro
    print("1️⃣  Verificando coluna 'data_cadastro'...")
    if verificar_coluna_existe(cursor, tabela, 'data_cadastro'):
        print("   ⏭️  Coluna 'data_cadastro' já existe. Pulando...")
    else:
        try:
            sql = f"""
                ALTER TABLE {tabela} 
                ADD COLUMN data_cadastro DATETIME DEFAULT CURRENT_TIMESTAMP
            """
            cursor.execute(sql)
            conexao.commit()
            print("   ✅ Coluna 'data_cadastro' adicionada com sucesso!")
            migracoes_executadas.append("data_cadastro")
        except Exception as e:
            print(f"   ❌ Erro ao adicionar 'data_cadastro': {e}")
            conexao.rollback()
            return False
    
    # 2. Verificar e adicionar coluna prazo_verificado
    print("\n2️⃣  Verificando coluna 'prazo_verificado'...")
    if verificar_coluna_existe(cursor, tabela, 'prazo_verificado'):
        print("   ⏭️  Coluna 'prazo_verificado' já existe. Pulando...")
    else:
        try:
            sql = f"""
                ALTER TABLE {tabela} 
                ADD COLUMN prazo_verificado BOOLEAN DEFAULT FALSE
            """
            cursor.execute(sql)
            conexao.commit()
            print("   ✅ Coluna 'prazo_verificado' adicionada com sucesso!")
            migracoes_executadas.append("prazo_verificado")
        except Exception as e:
            print(f"   ❌ Erro ao adicionar 'prazo_verificado': {e}")
            conexao.rollback()
            return False
    
    # 3. Atualizar registros existentes sem data_cadastro
    print("\n3️⃣  Atualizando registros existentes...")
    try:
        sql = f"""
            UPDATE {tabela} 
            SET data_cadastro = CURRENT_TIMESTAMP 
            WHERE data_cadastro IS NULL
        """
        cursor.execute(sql)
        registros_atualizados = cursor.rowcount
        conexao.commit()
        print(f"   ✅ {registros_atualizados} registro(s) atualizado(s) com data_cadastro!")
    except Exception as e:
        print(f"   ⚠️  Aviso ao atualizar registros: {e}")
    
    # 4. Verificar estrutura final
    print("\n4️⃣  Verificando estrutura final da tabela...")
    try:
        cursor.execute(f"DESCRIBE {tabela}")
        colunas = cursor.fetchall()
        
        print(f"\n   📋 Estrutura da tabela '{tabela}':")
        print("   " + "-"*80)
        for col in colunas:
            if col['Field'] in ['data_cadastro', 'prazo_verificado']:
                print(f"   ✅ {col['Field']:25s} | {col['Type']:20s} | {col['Null']:5s} | {col['Default']}")
        print("   " + "-"*80)
    except Exception as e:
        print(f"   ⚠️  Não foi possível verificar estrutura: {e}")
    
    return True, migracoes_executadas

def main():
    """Função principal de execução"""
    
    print("\n" + "🔧 "*20)
    print("SCRIPT DE MIGRAÇÃO - Sistema de Inquéritos")
    print("Versão: 2.0 | Data:", datetime.now().strftime('%d/%m/%Y %H:%M:%S'))
    print("🔧 "*20 + "\n")
    
    # Verificar variáveis de ambiente
    if not all([DB_USER, DB_PASSWORD, DB_HOST, DB_NAME]):
        print("❌ ERRO: Variáveis de ambiente não configuradas!")
        print("   Certifique-se que o arquivo .env existe com:")
        print("   - DB_USER")
        print("   - DB_PASSWORD")
        print("   - DB_HOST")
        print("   - DB_NAME")
        sys.exit(1)
    
    print(f"📌 Banco de dados: {DB_NAME}")
    print(f"📌 Host: {DB_HOST}")
    print(f"📌 Usuário: {DB_USER}\n")
    
    # Confirmação do usuário
    resposta = input("⚠️  Deseja continuar com a migração? (s/n): ").lower().strip()
    if resposta != 's':
        print("\n❌ Migração cancelada pelo usuário.")
        sys.exit(0)
    
    # Conectar ao banco
    conexao = conectar_banco()
    cursor = conexao.cursor()
    
    # Fazer backup (opcional mas recomendado)
    print("\n📦 Criando backup de segurança...")
    backup_nome = fazer_backup_tabela(cursor, conexao, 'inqueritos')
    
    # Executar migração
    try:
        sucesso, migracoes = executar_migracao(cursor, conexao)
        
        if sucesso:
            print("\n" + "="*60)
            print("🎉 MIGRAÇÃO CONCLUÍDA COM SUCESSO!")
            print("="*60)
            
            if migracoes:
                print(f"\n✅ Colunas adicionadas: {', '.join(migracoes)}")
            else:
                print("\n✅ Todas as colunas já existiam - Nenhuma alteração necessária")
            
            if backup_nome:
                print(f"📦 Backup disponível em: {backup_nome}")
            
            print("\n💡 Próximos passos:")
            print("   1. Substitua o arquivo crud_inqueritos.py no servidor")
            print("   2. Substitua o arquivo index.html na pasta templates/")
            print("   3. Reinicie a aplicação")
            print()
            
        else:
            print("\n❌ MIGRAÇÃO FALHOU!")
            print("   Verifique os erros acima e tente novamente.")
            
    except Exception as e:
        print(f"\n❌ ERRO CRÍTICO: {e}")
        conexao.rollback()
    finally:
        cursor.close()
        conexao.close()
        print("\n🔌 Conexão com o banco encerrada.")

# ===============================================
# EXECUÇÃO
# ===============================================

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Migração interrompida pelo usuário.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERRO INESPERADO: {e}")
        sys.exit(1)