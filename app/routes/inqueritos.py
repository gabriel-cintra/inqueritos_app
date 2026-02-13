"""
Blueprint de Inquéritos - COMPLETO com todas as funcionalidades
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required
from datetime import datetime, timedelta
from app import db
from app.models.inquerito import Inquerito, InqueritoConcluido
from app.utils.helpers import formatar_data, formatar_data_iso
import csv
from io import StringIO
import pandas as pd

bp = Blueprint('inqueritos', __name__, url_prefix='/inqueritos')


@bp.route('/')
@login_required
def index():
    """Lista principal de inquéritos"""
    ordem_col = request.args.get('ordem', 'data_cadastro')
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
    
    return render_template('inqueritos/index.html',
                           inqueritos=paginacao.items,
                           pagination=paginacao,
                           ordem_atual=ordem_col,
                           dir_atual=direcao,
                           busca_atual=busca,
                           total=paginacao.total,
                           pagina_atual=page,
                           total_paginas=paginacao.pages)


@bp.route('/adicionar', methods=['POST'])
@login_required
def adicionar():
    """Adicionar novo inquérito"""
    try:
        # CAMPOS RESTAURADOS
        novo = Inquerito(
            num_controle=request.form['num_controle'],
            num_eletronico=request.form['num_eletronico'],
            ano=int(request.form['ano']),
            num_processo=request.form.get('num_processo', ''),
            data_conclusao=formatar_data(request.form.get('data_conclusao')),
            delegacia=request.form.get('delegacia'),
            data_ultima_atualizacao=formatar_data(request.form.get('data_ultima_atualizacao')),
            status=request.form.get('status', 'Em Cartório'),
            equipe=request.form.get('equipe'),
            is_cota=bool(request.form.get('is_cota')),
            data_cadastro=datetime.utcnow(),
            prazo_verificado=False
        )
        
        # Verificar duplicidade
        if Inquerito.query.filter_by(num_eletronico=novo.num_eletronico).first():
            flash("Nº Eletrônico já existe!", "danger")
            return redirect(url_for('inqueritos.index'))

        db.session.add(novo)
        db.session.commit()
        flash("Inquérito cadastrado com sucesso!", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Erro ao adicionar: {e}", "danger")
    
    return redirect(url_for('inqueritos.index'))


@bp.route('/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar(id):
    """Editar inquérito"""
    item = Inquerito.query.get_or_404(id)
    
    if request.method == 'POST':
        try:
            item.num_controle = request.form['num_controle']
            item.num_eletronico = request.form['num_eletronico']
            item.ano = int(request.form['ano'])
            item.num_processo = request.form.get('num_processo', '')
            item.data_conclusao = formatar_data(request.form.get('data_conclusao'))
            
            # CAMPOS RESTAURADOS
            item.delegacia = request.form.get('delegacia')
            item.data_ultima_atualizacao = formatar_data(request.form.get('data_ultima_atualizacao'))
            item.status = request.form.get('status', 'Em Cartório')
            item.equipe = request.form.get('equipe')
            item.is_cota = bool(request.form.get('is_cota'))
            
            db.session.commit()
            flash("Inquérito atualizado com sucesso!", "success")
            return redirect(url_for('inqueritos.index'))
        except Exception as e:
            db.session.rollback()
            flash(f"Erro ao atualizar: {e}", "danger")
    
    data_conclusao_iso = formatar_data_iso(item.data_conclusao)
    data_ultima_atualizacao_iso = formatar_data_iso(item.data_ultima_atualizacao)
    
    return render_template('inqueritos/editar.html', 
                           inquerito=item, 
                           data_conclusao_iso=data_conclusao_iso,
                           data_ultima_atualizacao_iso=data_ultima_atualizacao_iso)


@bp.route('/deletar/<int:id>')
@login_required
def deletar(id):
    """Deletar inquérito"""
    item = Inquerito.query.get_or_404(id)
    try:
        db.session.delete(item)
        db.session.commit()
        flash("Inquérito removido com sucesso.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Erro ao remover: {e}", "danger")
    return redirect(url_for('inqueritos.index'))


@bp.route('/marcar_concluir/<int:id>')
@login_required
def marcar_concluir(id):
    """Marcar/desmarcar para concluir no mês"""
    item = Inquerito.query.get_or_404(id)
    item.concluir_mes = bool(int(request.args.get('v', 0)))
    db.session.commit()
    return redirect(url_for('inqueritos.index'))


@bp.route('/verificar_prazo/<int:id>')
@login_required
def verificar_prazo(id):
    """Marcar prazo como verificado"""
    item = Inquerito.query.get_or_404(id)
    item.prazo_verificado = True
    db.session.commit()
    flash("Prazo verificado! Alerta removido.", "success")
    return redirect(url_for('inqueritos.index'))


@bp.route('/concluir_mes')
@login_required
def concluir_mes():
    """Lista de inquéritos marcados para concluir"""
    hoje = datetime.now()
    dados = Inquerito.query.filter_by(concluir_mes=True).order_by(Inquerito.data_conclusao.asc()).all()
    return render_template('inqueritos/concluir_mes.html', 
                           inqueritos=dados, 
                           mes=hoje.month, 
                           ano=hoje.year)


@bp.route('/relatar/<int:id>', methods=['POST'])
@login_required
def relatar(id):
    """Relatar inquérito (move para concluídos)"""
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
        flash("Inquérito relatado e arquivado com sucesso.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Erro ao relatar: {e}", "danger")
    
    return redirect(url_for('inqueritos.concluir_mes'))


@bp.route('/relatorios')
@login_required
def relatorios():
    """Relatórios de inquéritos concluídos"""
    hoje = datetime.now()
    mes = request.args.get('mes', hoje.month, type=int)
    ano = request.args.get('ano', hoje.year, type=int)
    
    dados = InqueritoConcluido.query.filter_by(mes=mes, ano_ref=ano).order_by(InqueritoConcluido.data_relato.desc()).all()
    
    return render_template('inqueritos/relatorios.html', 
                           inqueritos=dados, 
                           mes_atual=mes, 
                           ano_atual=ano,
                           anos_disponiveis=list(range(hoje.year-2, hoje.year+1)),
                           meses_do_ano=[(1,'Janeiro'),(2,'Fevereiro'),(3,'Março'),(4,'Abril'),
                                        (5,'Maio'),(6,'Junho'),(7,'Julho'),(8,'Agosto'),
                                        (9,'Setembro'),(10,'Outubro'),(11,'Novembro'),(12,'Dezembro')])


@bp.route('/desfazer_relato/<int:id>')
@login_required
def desfazer_relato(id):
    """Desfazer relato (restaurar para lista principal)"""
    concluido = InqueritoConcluido.query.get_or_404(id)
    
    restaurado = Inquerito(
        num_controle=concluido.num_controle,
        num_eletronico=concluido.num_eletronico,
        ano=concluido.ano,
        num_processo=concluido.num_processo,
        data_conclusao=concluido.data_conclusao,
        is_cota=concluido.is_cota,
        concluir_mes=False,
        data_cadastro=datetime.utcnow(),
        prazo_verificado=False
    )
    
    try:
        db.session.add(restaurado)
        db.session.delete(concluido)
        db.session.commit()
        flash("Inquérito restaurado para a lista principal.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Erro ao restaurar: {e}", "danger")
    
    return redirect(url_for('inqueritos.relatorios'))


@bp.route('/importar_massa', methods=['GET', 'POST'])
@login_required
def importar_massa():
    """Importação em massa via CSV/TSV"""
    if request.method == 'POST':
        dados = request.form.get('dados_inqueritos', '')
        reader = csv.reader(StringIO(dados), delimiter='\t')
        
        try:
            next(reader)  # Pular cabeçalho
        except:
            pass
        
        count = 0
        erros = 0
        
        for row in reader:
            if len(row) < 7:
                continue
            
            try:
                num_eletronico = row[0].strip()
                if Inquerito.query.filter_by(num_eletronico=num_eletronico).first():
                    continue
                
                novo = Inquerito(
                    num_eletronico=num_eletronico,
                    ano=int(row[1].strip()),
                    delegacia=row[2].strip() if len(row) > 2 else None,
                    data_ultima_atualizacao=formatar_data(row[3]) if len(row) > 3 else None,
                    data_conclusao=formatar_data(row[4]) if len(row) > 4 else None,
                    status=row[5].strip() if len(row) > 5 else 'Em Cartório',
                    equipe=row[6].strip() if len(row) > 6 else None,
                    is_cota=False,
                    data_cadastro=datetime.utcnow(),
                    prazo_verificado=False
                )
                db.session.add(novo)
                count += 1
            except Exception as e:
                erros += 1
                print(f"Erro na linha: {row} - {e}")
        
        try:
            db.session.commit()
            flash(f"Importação concluída! {count} registros importados. {erros} erros.", "success")
        except Exception as e:
            db.session.rollback()
            flash(f"Erro crítico na importação: {e}", "danger")
        
        return redirect(url_for('inqueritos.index'))
    
    return render_template('inqueritos/importar.html')


@bp.route('/comparar_vencidos', methods=['GET', 'POST'])
@login_required
def comparar_vencidos():
    """Comparador de vencidos via Excel com ordenação inteligente"""
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
            df = pd.read_excel(file)
            df.dropna(how='all', inplace=True)
            
            # Identificar coluna de números de inquérito
            coluna_chave = None
            for col in df.columns:
                if 'inquérito' in str(col).lower() or 'inquerito' in str(col).lower():
                    coluna_chave = col
                    break
            
            if not coluna_chave:
                coluna_chave = df.columns[0]
            
            lista_excel = df[coluna_chave].dropna().astype(str).str.strip().tolist()
            
            # Buscar no banco
            resultados = Inquerito.query.filter(Inquerito.num_eletronico.in_(lista_excel)).all()
            
            # Ordenação inteligente (ano + número de controle como inteiro)
            def chave_ordenacao(inq):
                try:
                    nc = int(inq.num_controle) if inq.num_controle else 9999999
                except (ValueError, TypeError):
                    nc = 9999999
                return (inq.ano, nc)
            
            resultados.sort(key=chave_ordenacao)
            
            # Identificar não encontrados
            encontrados_set = {iq.num_eletronico for iq in resultados}
            for num in lista_excel:
                if num not in encontrados_set:
                    nao_encontrados.append(num)
            
            if not resultados:
                flash("Nenhum inquérito do arquivo foi encontrado na base de dados.", "warning")
            else:
                flash(f"Processamento concluído! {len(resultados)} registros localizados e ordenados.", "success")
        
        except Exception as e:
            flash(f"Erro ao processar o arquivo: {str(e)}", "danger")
    
    return render_template('inqueritos/comparar_vencidos.html', 
                           resultados=resultados, 
                           nao_encontrados=nao_encontrados)