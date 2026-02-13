"""
Models de Boletim de Ocorrência (NOVO MÓDULO)
"""
from datetime import datetime
from app import db

class Boletim(db.Model):
    __tablename__ = 'boletins'
    
    id = db.Column(db.Integer, primary_key=True)
    num_bo = db.Column(db.String(100), unique=True, nullable=False)
    ano = db.Column(db.Integer, nullable=False)
    natureza = db.Column(db.String(255), nullable=False)
    data_cadastro = db.Column(db.DateTime, default=datetime.utcnow)
    data_atualizacao = db.Column(db.Date)
    status_atual = db.Column(db.String(255))
    data_conclusao = db.Column(db.Date)
    despacho = db.Column(db.Text)
    concluir = db.Column(db.Boolean, default=False)  # Marcar para finalização
    
    def __repr__(self):
        return f'<Boletim {self.num_bo}/{self.ano}>'


class BoletimConcluir(db.Model):
    """Boletins marcados para concluir, aguardando validação da chefia"""
    __tablename__ = 'boletins_concluir'
    
    id = db.Column(db.Integer, primary_key=True)
    num_bo = db.Column(db.String(100), nullable=False)
    ano = db.Column(db.Integer, nullable=False)
    natureza = db.Column(db.String(255), nullable=False)
    data_conclusao = db.Column(db.Date)
    despacho = db.Column(db.Text)
    data_marcacao = db.Column(db.DateTime, default=datetime.utcnow)  # Quando foi marcado
    
    def __repr__(self):
        return f'<BoletimConcluir {self.num_bo}/{self.ano}>'


class BoletimFinalizado(db.Model):
    """Boletins finalizados (arquivo permanente)"""
    __tablename__ = 'boletins_finalizados'
    
    id = db.Column(db.Integer, primary_key=True)
    num_bo = db.Column(db.String(100), nullable=False)
    ano = db.Column(db.Integer, nullable=False)
    natureza = db.Column(db.String(255), nullable=False)
    data_conclusao = db.Column(db.Date)
    data_finalizacao = db.Column(db.Date)  # Quando a chefia validou
    mes_ref = db.Column(db.Integer, nullable=False)
    ano_ref = db.Column(db.Integer, nullable=False)
    despacho = db.Column(db.Text)
    data_registro = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<BoletimFinalizado {self.num_bo}/{self.ano}>'
