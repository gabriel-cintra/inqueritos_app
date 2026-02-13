# 🏛️ Sistema Jurídico MP - Versão Integrada

Sistema completo para gerenciamento de Inquéritos Policiais e Boletins de Ocorrência do Ministério Público.

## 🎯 O que mudou do sistema anterior

### ✅ **Mantido 100%:**
- Toda a lógica de Inquéritos
- Sistema de login/autenticação
- Importação em massa (CSV)
- Comparador de vencidos (Excel)
- Sistema de conclusão mensal
- Relatórios
- Banco de dados MySQL

### 🆕 **Novidades:**
- **Módulo completo de Boletins de Ocorrência**
- Arquitetura modular (Blueprints)
- Navbar unificada
- Design responsivo
- Código organizado e escalável

## 📦 Estrutura do Projeto

```
sistema-integrado/
├── app.py                      # Arquivo principal
├── config.py                   # Configurações
├── requirements.txt            # Dependências
├── Procfile                    # Deploy
├── .env                        # Variáveis de ambiente
├── app/
│   ├── __init__.py             # Factory da aplicação
│   ├── models/                 # Modelos do banco
│   │   ├── user.py
│   │   ├── inquerito.py
│   │   └── boletim.py
│   ├── routes/                 # Rotas (Blueprints)
│   │   ├── auth.py
│   │   ├── inqueritos.py
│   │   └── boletins.py
│   ├── templates/              # Templates HTML
│   │   ├── base.html
│   │   ├── auth/
│   │   ├── inqueritos/
│   │   └── boletins/
│   ├── static/                 # CSS/JS
│   │   ├── css/custom.css
│   │   └── js/main.js
│   └── utils/                  # Funções auxiliares
│       └── helpers.py
```

## 🚀 Instalação

### 1. **Preparar ambiente**

```bash
# Criar ambiente virtual
python -m venv venv

# Ativar (Linux/Mac)
source venv/bin/activate

# Ativar (Windows)
venv\Scripts\activate

# Instalar dependências
pip install -r requirements.txt
```

### 2. **Configurar banco de dados**

Crie o arquivo `.env` na raiz do projeto:

```env
SECRET_KEY=sua-chave-secreta-aqui
DB_USER=seu_usuario_mysql
DB_PASSWORD=sua_senha_mysql
DB_HOST=localhost
DB_NAME=sistema_juridico
```

### 3. **Criar banco de dados**

```sql
CREATE DATABASE sistema_juridico CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

**IMPORTANTE:** Se você já tem o banco do sistema anterior, **NÃO PRECISA RECRIAR**! O sistema vai:
- Manter suas 3 tabelas existentes (usuarios, inqueritos, inqueritos_concluidos)
- Criar automaticamente 3 novas tabelas (boletins, boletins_concluir, boletins_finalizados)

### 4. **Executar aplicação**

```bash
# Modo desenvolvimento
python app.py

# Ou com gunicorn (produção)
gunicorn app:app
```

Acesse: `http://localhost:5000`

**Login padrão:**
- Usuário: `gabriel.cintra`
- Senha: `Web010203`

## 📊 Tabelas do Banco de Dados

### **Existentes (mantidas):**
1. `usuarios` - Login/autenticação
2. `inqueritos` - Inquéritos ativos
3. `inqueritos_concluidos` - Inquéritos arquivados

### **Novas (criadas automaticamente):**
4. `boletins` - Boletins ativos
5. `boletins_concluir` - Boletins aguardando validação
6. `boletins_finalizados` - Boletins arquivados

## 🔄 Migração do Sistema Anterior

### **Opção 1: Substituir tudo (Recomendado)**
1. Fazer backup do banco de dados atual
2. Fazer backup do arquivo `.env`
3. Substituir todos os arquivos Python e HTML
4. Manter o `.env` (mesmo arquivo)
5. Executar o sistema

### **Opção 2: Manter sistemas paralelos**
- Mantenha o antigo funcionando
- Crie novo banco de dados para testar
- Migre quando estiver satisfeito

## 🎨 Módulos do Sistema

### **1. Inquéritos**
- `/inqueritos/` - Lista principal
- `/inqueritos/adicionar` - Novo inquérito
- `/inqueritos/editar/<id>` - Editar
- `/inqueritos/concluir_mes` - Marcados para concluir
- `/inqueritos/relatorios` - Arquivados
- `/inqueritos/importar_massa` - Importação CSV
- `/inqueritos/comparar_vencidos` - Comparador Excel

### **2. Boletins (NOVO)**
- `/boletins/` - Lista principal
- `/boletins/adicionar` - Novo boletim
- `/boletins/editar/<id>` - Editar
- `/boletins/concluir` - Aguardando validação
- `/boletins/finalizados` - Arquivados

### **3. Autenticação**
- `/auth/login` - Login
- `/auth/logout` - Logout

## 🛠️ Tecnologias

- **Backend:** Flask 3.0
- **ORM:** SQLAlchemy
- **Banco:** MySQL
- **Auth:** Flask-Login
- **Frontend:** Bootstrap 5.3.8 + Bootstrap Icons
- **Deploy:** Gunicorn

## 📱 Funcionalidades

### **Inquéritos:**
✅ CRUD completo
✅ Sistema de alertas de prazo (≤5 dias)
✅ Marcação de COTA (retorno da Justiça)
✅ Importação em massa (CSV/TSV)
✅ Comparador de vencidos (Excel)
✅ Sistema de conclusão em 2 etapas
✅ Relatórios por mês/ano
✅ Busca e paginação

### **Boletins (NOVO):**
✅ CRUD completo
✅ Sistema de 3 etapas (Ativo → Concluir → Finalizado)
✅ Campo de despacho (texto livre)
✅ Status customizável
✅ Filtros por mês/ano/natureza
✅ Relatórios e estatísticas
✅ Busca e paginação

## 🔐 Segurança

- Senhas hash (SHA-256)
- Login obrigatório em todas as rotas
- CSRF protection (via Flask-WTF - adicionar se necessário)
- Variáveis sensíveis em .env
- SQL Injection protegido (SQLAlchemy ORM)

## 📈 Escalabilidade

O sistema está preparado para:
- ✅ Adicionar novos módulos (apenas criar novo blueprint)
- ✅ Múltiplos usuários com permissões (adicionar roles)
- ✅ Auditoria de ações (adicionar tabela de logs)
- ✅ Upload de anexos (configuração já pronta)
- ✅ Exportação PDF/Excel (pandas já instalado)

## 🐛 Troubleshooting

### **Erro de conexão ao banco:**
- Verificar credenciais no `.env`
- Verificar se MySQL está rodando
- Testar conexão: `mysql -u usuario -p`

### **Erro ao importar módulos:**
- Verificar instalação: `pip install -r requirements.txt`
- Verificar ambiente virtual está ativado

### **Página em branco:**
- Verificar logs do terminal
- Modo debug: editar `app.py` → `debug=True`

## 📞 Suporte

Sistema desenvolvido para Ministério Público.
Versão: 2.0 - Integrada e Modular

---

**🎉 Pronto para uso! Basta seguir os passos de instalação acima.**
