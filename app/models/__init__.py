"""
Models do sistema
"""
from app.models.user import User
from app.models.inquerito import Inquerito, InqueritoConcluido
from app.models.boletim import Boletim, BoletimConcluir, BoletimFinalizado

__all__ = [
    'User',
    'Inquerito',
    'InqueritoConcluido',
    'Boletim',
    'BoletimConcluir',
    'BoletimFinalizado'
]
