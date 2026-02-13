"""
Models de Inquérito - COMPLETO com todos os campos restaurados
"""
from datetime import datetime
from app import db

class Inquerito(db.Model):
    __tablename__ = 'inqueritos'
    
    id = db.Column(db.Integer, primary_key=True)
    num_controle = db.Column(db.String(255))
    num_eletronico = db.Column(db.String(255), unique=True, nullable=False)
    ano = db.Column(db.Integer, nullable=False)
    num_processo = db.Column(db.String(255))
    data_conclusao = db.Column(db.Date)
    
    # CAMPOS RESTAURADOS
    delegacia = db.Column(db.String(255))
    data_ultima_atualizacao = db.Column(db.Date)
    status = db.Column(db.String(255))
    equipe = db.Column(db.String(255))
    
    concluir_mes = db.Column(db.Boolean, default=False)
    is_cota = db.Column(db.Boolean, default=False)
    data_cadastro = db.Column(db.DateTime, default=datetime.utcnow)
    prazo_verificado = db.Column(db.Boolean, default=False)
    
    def dias_para_vencimento(self):
        """Calcula quantos dias faltam para a data de conclusão"""
        if not self.data_conclusao:
            return None
        hoje = datetime.now().date()
        delta = self.data_conclusao - hoje
        return delta.days
    
    def esta_proximo_vencimento(self):
        """Verifica se está a 5 dias ou menos do vencimento e não foi verificado"""
        if self.prazo_verificado:
            return False
        dias = self.dias_para_vencimento()
        if dias is None:
            return False
        return 0 <= dias <= 5
    
    def __repr__(self):
        return f'<Inquerito {self.num_eletronico}>'


class InqueritoConcluido(db.Model):
    __tablename__ = 'inqueritos_concluidos'
    
    id = db.Column(db.Integer, primary_key=True)
    num_controle = db.Column(db.String(255))
    num_eletronico = db.Column(db.String(255), nullable=False)
    ano = db.Column(db.Integer, nullable=False)
    num_processo = db.Column(db.String(255))
    data_conclusao = db.Column(db.Date)
    mes = db.Column(db.Integer, nullable=False)
    ano_ref = db.Column(db.Integer, nullable=False)
    ano_conclusao = db.Column(db.Integer, nullable=False)
    data_relato = db.Column(db.Date)
    data_registro = db.Column(db.DateTime, default=datetime.utcnow)
    is_cota = db.Column(db.Boolean, default=False)
    
    def __repr__(self):
        return f'<InqueritoConcluido {self.num_eletronico}>'