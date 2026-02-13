# 🔄 GUIA RÁPIDO DE MIGRAÇÃO

## ✅ Checklist Pré-Migração

- [ ] Backup do banco de dados MySQL atual
- [ ] Backup do arquivo `.env` atual
- [ ] Backup de todos os arquivos `.py` atuais
- [ ] Sistema antigo está funcionando

## 📋 Passo a Passo - Migração

### **OPÇÃO 1: Migração Direta (Recomendado)**

#### 1. **Backup**
```bash
# Backup do banco
mysqldump -u root -p sistema_juridico > backup_antes_migracao.sql

# Backup dos arquivos
cp -r /caminho/sistema-atual /caminho/sistema-atual-backup
```

#### 2. **Substituir arquivos**
- Copie toda a pasta `sistema-integrado` para o servidor
- Mantenha seu arquivo `.env` antigo (funciona perfeitamente!)

#### 3. **Instalar dependências**
```bash
cd sistema-integrado
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou: venv\Scripts\activate  # Windows

pip install -r requirements.txt
```

#### 4. **Executar**
```bash
python app.py
```

**Pronto!** O sistema vai:
- ✅ Usar suas tabelas existentes (usuarios, inqueritos, inqueritos_concluidos)
- ✅ Criar automaticamente 3 novas tabelas para Boletins
- ✅ Manter todos os dados de inquéritos

---

### **OPÇÃO 2: Teste Paralelo (Mais Seguro)**

#### 1. **Criar banco de teste**
```sql
CREATE DATABASE sistema_juridico_teste CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

#### 2. **Copiar dados do banco antigo**
```bash
mysqldump -u root -p sistema_juridico | mysql -u root -p sistema_juridico_teste
```

#### 3. **Configurar .env de teste**
```env
DB_NAME=sistema_juridico_teste
```

#### 4. **Testar**
```bash
python app.py
```

#### 5. **Quando estiver satisfeito:**
- Mude `.env` para apontar para o banco de produção
- Ou migre os dados de teste para produção

---

## 🗄️ Estrutura do Banco Após Migração

### **Tabelas Mantidas (inalteradas):**
- ✅ `usuarios`
- ✅ `inqueritos`
- ✅ `inqueritos_concluidos`

### **Tabelas Novas (criadas automaticamente):**
- 🆕 `boletins`
- 🆕 `boletins_concluir`
- 🆕 `boletins_finalizados`

**TOTAL: 6 tabelas**

---

## 🔧 Troubleshooting

### **"ModuleNotFoundError: No module named 'app'"**
- Certifique-se que está na pasta `sistema-integrado`
- Verifique se o ambiente virtual está ativado

### **"Can't connect to MySQL server"**
- Verifique credenciais no `.env`
- Teste: `mysql -u root -p`

### **"Table 'usuarios' doesn't exist"**
- Execute o sistema uma vez para criar as tabelas
- Ou restaure o backup do banco

### **Templates não aparecem**
- Verifique estrutura de pastas: `app/templates/`
- Limpe cache do navegador (Ctrl+F5)

---

## 📞 Suporte Rápido

**Login padrão:**
- Usuário: `gabriel.cintra`
- Senha: `Web010203`

**Testar instalação:**
1. Acesse `http://localhost:5000`
2. Faça login
3. Veja se inquéritos antigos aparecem
4. Teste criar um boletim novo

---

## ✨ Novidades que Você Vai Ver

1. **Navbar unificada** com menu suspenso
2. **Módulo de Boletins** completamente novo
3. **Design responsivo** (funciona no celular!)
4. **Código organizado** em pastas (models, routes, templates)

---

**🎉 Migração concluída! Aproveite o novo sistema!**
