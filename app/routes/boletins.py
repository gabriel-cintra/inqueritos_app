"""
Blueprint de Boletins de Ocorrência - COMPLETO COM UNDO
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required
from datetime import datetime
from app import db
from app.models.boletim import Boletim, BoletimConcluir, BoletimFinalizado
from app.utils.helpers import formatar_data, formatar_data_iso

bp = Blueprint('boletins', __name__, url_prefix='/boletins')


@bp.route('/')
@login_required
def index():
    """Lista principal de boletins ativos"""
    busca = request.args.get('q', '')
    page = request.args.get('page', 1, type=int)
    per_page = 10

    query = Boletim.query

    if busca:
        t = f"%{busca}%"
        query = query.filter(
            (Boletim.num_bo.like(t)) | 
            (Boletim.natureza.like(t))
        )

    query = query.order_by(Boletim.data_cadastro.desc())
    paginacao = query.paginate(page=page, per_page=per_page, error_out=False)
    
    # Contar boletins aguardando finalização
    count_concluir = BoletimConcluir.query.count()
    
    return render_template('boletins/index.html',
                           boletins=paginacao.items,
                           pagination=paginacao,
                           busca_atual=busca,
                           total=paginacao.total,
                           pagina_atual=page,
                           total_paginas=paginacao.pages,
                           count_concluir=count_concluir)


@bp.route('/adicionar', methods=['POST'])
@login_required
def adicionar():
    """Adicionar novo boletim"""
    try:
        novo = Boletim(
            num_bo=request.form['num_bo'],
            ano=int(request.form['ano']),
            natureza=request.form['natureza'],
            data_atualizacao=formatar_data(request.form.get('data_atualizacao')),
            status_atual=request.form.get('status_atual'),
            data_conclusao=formatar_data(request.form.get('data_conclusao')),
            despacho=request.form.get('despacho'),
            data_cadastro=datetime.utcnow(),
            concluir=False
        )
        db.session.add(novo)
        db.session.commit()
        flash(f"Boletim {novo.num_bo} cadastrado com sucesso!", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Erro ao cadastrar: {e}", "danger")
    return redirect(url_for('boletins.index'))


@bp.route('/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar(id):
    """Editar boletim"""
    item = Boletim.query.get_or_404(id)
    
    if request.method == 'POST':
        try:
            item.num_bo = request.form['num_bo']
            item.ano = int(request.form['ano'])
            item.natureza = request.form['natureza']
            item.data_atualizacao = formatar_data(request.form.get('data_atualizacao'))
            item.status_atual = request.form.get('status_atual')
            item.data_conclusao = formatar_data(request.form.get('data_conclusao'))
            item.despacho = request.form.get('despacho')
            db.session.commit()
            flash("Boletim atualizado com sucesso!", "success")
            return redirect(url_for('boletins.index'))
        except Exception as e:
            db.session.rollback()
            flash(f"Erro ao atualizar: {e}", "danger")
    
    data_conclusao_iso = formatar_data_iso(item.data_conclusao)
    data_atualizacao_iso = formatar_data_iso(item.data_atualizacao)
    
    return render_template('boletins/editar.html', 
                           boletim=item, 
                           data_conclusao_iso=data_conclusao_iso,
                           data_atualizacao_iso=data_atualizacao_iso)


@bp.route('/deletar/<int:id>')
@login_required
def deletar(id):
    """Deletar boletim"""
    item = Boletim.query.get_or_404(id)
    try:
        db.session.delete(item)
        db.session.commit()
        flash("Boletim removido com sucesso.", "success")
    except:
        db.session.rollback()
        flash("Erro ao remover.", "danger")
    return redirect(url_for('boletins.index'))


@bp.route('/marcar_concluir/<int:id>')
@login_required
def marcar_concluir(id):
    """Marcar boletim como concluído (move para aguardando validação)"""
    item = Boletim.query.get_or_404(id)
    
    # Mover para tabela de "aguardando finalização"
    concluir = BoletimConcluir(
        num_bo=item.num_bo,
        ano=item.ano,
        natureza=item.natureza,
        data_conclusao=item.data_conclusao,
        despacho=item.despacho,
        data_marcacao=datetime.utcnow()
    )
    
    try:
        db.session.add(concluir)
        db.session.delete(item)
        db.session.commit()
        flash(f"Boletim {item.num_bo} marcado para finalização.", "success")
    except:
        db.session.rollback()
        flash("Erro ao marcar.", "danger")
    
    return redirect(url_for('boletins.index'))


# ========== FUNÇÃO UNDO 1: Retornar de "Concluir" para "Ativo" ==========
@bp.route('/desfazer_concluir/<int:id>')
@login_required
def desfazer_concluir(id):
    """Desfazer marcação de conclusão (retorna de aguardando para ativo)"""
    item = BoletimConcluir.query.get_or_404(id)
    
    # Restaurar para a tabela de ativos
    restaurado = Boletim(
        num_bo=item.num_bo,
        ano=item.ano,
        natureza=item.natureza,
        data_conclusao=item.data_conclusao,
        despacho=item.despacho,
        status_atual="Restaurado",
        data_cadastro=datetime.utcnow(),
        concluir=False
    )
    
    try:
        db.session.add(restaurado)
        db.session.delete(item)
        db.session.commit()
        flash(f"Boletim {item.num_bo} retornado para a lista de ativos.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Erro ao desfazer: {e}", "danger")
    
    return redirect(url_for('boletins.concluir'))


@bp.route('/concluir')
@login_required
def concluir():
    """Lista de boletins aguardando finalização (validação da chefia)"""
    dados = BoletimConcluir.query.order_by(BoletimConcluir.data_marcacao.desc()).all()
    
    # Contar totais
    count_ativos = Boletim.query.count()
    
    return render_template('boletins/concluir.html', 
                           boletins=dados,
                           count_ativos=count_ativos)


@bp.route('/finalizar/<int:id>', methods=['POST'])
@login_required
def finalizar(id):
    """Finalizar boletim (após validação da chefia - move para arquivo)"""
    item = BoletimConcluir.query.get_or_404(id)
    
    hoje = datetime.now().date()
    
    finalizado = BoletimFinalizado(
        num_bo=item.num_bo,
        ano=item.ano,
        natureza=item.natureza,
        data_conclusao=item.data_conclusao,
        data_finalizacao=hoje,
        mes_ref=hoje.month,
        ano_ref=hoje.year,
        despacho=item.despacho,
        data_registro=datetime.utcnow()
    )
    
    try:
        db.session.add(finalizado)
        db.session.delete(item)
        db.session.commit()
        flash(f"Boletim {item.num_bo} finalizado e arquivado.", "success")
    except:
        db.session.rollback()
        flash("Erro ao finalizar.", "danger")
    
    return redirect(url_for('boletins.concluir'))


# ========== FUNÇÃO UNDO 2: Retornar de "Finalizado" para "Concluir" ==========
@bp.route('/restaurar_finalizado/<int:id>')
@login_required
def restaurar_finalizado(id):
    """Restaurar boletim finalizado de volta para aguardando finalização"""
    finalizado = BoletimFinalizado.query.get_or_404(id)
    
    restaurado = BoletimConcluir(
        num_bo=finalizado.num_bo,
        ano=finalizado.ano,
        natureza=finalizado.natureza,
        data_conclusao=finalizado.data_conclusao,
        despacho=finalizado.despacho,
        data_marcacao=datetime.utcnow()
    )
    
    try:
        db.session.add(restaurado)
        db.session.delete(finalizado)
        db.session.commit()
        flash(f"Boletim {finalizado.num_bo} restaurado para aguardando finalização.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Erro ao restaurar: {e}", "danger")
    
    return redirect(url_for('boletins.finalizados'))


@bp.route('/finalizados')
@login_required
def finalizados():
    """Arquivo de boletins finalizados"""
    hoje = datetime.now()
    mes = request.args.get('mes', hoje.month, type=int)
    ano = request.args.get('ano', hoje.year, type=int)
    page = request.args.get('page', 1, type=int)
    per_page = 15
    
    query = BoletimFinalizado.query.filter_by(mes_ref=mes, ano_ref=ano)
    query = query.order_by(BoletimFinalizado.data_finalizacao.desc())
    
    paginacao = query.paginate(page=page, per_page=per_page, error_out=False)
    
    # Contar totais
    count_ativos = Boletim.query.count()
    count_concluir = BoletimConcluir.query.count()
    
    return render_template('boletins/finalizados.html',
                           boletins=paginacao.items,
                           pagination=paginacao,
                           mes_atual=mes,
                           ano_atual=ano,
                           count_ativos=count_ativos,
                           count_concluir=count_concluir,
                           total=paginacao.total,
                           anos_disponiveis=list(range(hoje.year-2, hoje.year+1)),
                           meses_do_ano=[(1,'Janeiro'),(2,'Fevereiro'),(3,'Março'),(4,'Abril'),
                                        (5,'Maio'),(6,'Junho'),(7,'Julho'),(8,'Agosto'),
                                        (9,'Setembro'),(10,'Outubro'),(11,'Novembro'),(12,'Dezembro')])


# Rota antiga mantida para compatibilidade
@bp.route('/restaurar/<int:id>')
@login_required
def restaurar(id):
    """Alias para restaurar_finalizado (mantido para compatibilidade)"""
    return restaurar_finalizado(id)