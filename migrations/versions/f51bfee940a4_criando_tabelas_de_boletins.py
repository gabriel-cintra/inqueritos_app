"""Criando tabelas de boletins

Revision ID: (será gerado automaticamente)
Revises: 
Create Date: 2026-02-13

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'SUBSTITUA_PELO_ID_GERADO'  # Não altere esta linha
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ===== CRIAÇÃO DAS TABELAS DE BOLETINS =====
    
    # Tabela boletins (ativos)
    op.create_table('boletins',
        sa.Column('id', sa.Integer(), nullable=False, autoincrement=True),
        sa.Column('num_bo', sa.String(length=100), nullable=False),
        sa.Column('ano', sa.Integer(), nullable=False),
        sa.Column('natureza', sa.String(length=255), nullable=False),
        sa.Column('data_cadastro', sa.DateTime(), nullable=True),
        sa.Column('data_atualizacao', sa.Date(), nullable=True),
        sa.Column('status_atual', sa.String(length=255), nullable=True),
        sa.Column('data_conclusao', sa.Date(), nullable=True),
        sa.Column('despacho', sa.Text(), nullable=True),
        sa.Column('concluir', sa.Boolean(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('num_bo')
    )
    
    # Tabela boletins_concluir (aguardando validação)
    op.create_table('boletins_concluir',
        sa.Column('id', sa.Integer(), nullable=False, autoincrement=True),
        sa.Column('num_bo', sa.String(length=100), nullable=False),
        sa.Column('ano', sa.Integer(), nullable=False),
        sa.Column('natureza', sa.String(length=255), nullable=False),
        sa.Column('data_conclusao', sa.Date(), nullable=True),
        sa.Column('despacho', sa.Text(), nullable=True),
        sa.Column('data_marcacao', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Tabela boletins_finalizados (arquivo)
    op.create_table('boletins_finalizados',
        sa.Column('id', sa.Integer(), nullable=False, autoincrement=True),
        sa.Column('num_bo', sa.String(length=100), nullable=False),
        sa.Column('ano', sa.Integer(), nullable=False),
        sa.Column('natureza', sa.String(length=255), nullable=False),
        sa.Column('data_conclusao', sa.Date(), nullable=True),
        sa.Column('data_finalizacao', sa.Date(), nullable=True),
        sa.Column('mes_ref', sa.Integer(), nullable=False),
        sa.Column('ano_ref', sa.Integer(), nullable=False),
        sa.Column('despacho', sa.Text(), nullable=True),
        sa.Column('data_registro', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Índice para consultas por mês/ano
    op.create_index('idx_mes_ano', 'boletins_finalizados', ['mes_ref', 'ano_ref'], unique=False)


def downgrade():
    # ===== REMOÇÃO DAS TABELAS DE BOLETINS =====
    op.drop_index('idx_mes_ano', table_name='boletins_finalizados')
    op.drop_table('boletins_finalizados')
    op.drop_table('boletins_concluir')
    op.drop_table('boletins')