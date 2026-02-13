"""
Funções auxiliares do sistema
"""
from datetime import datetime

def formatar_data(data_str):
    """
    Converte string de data em objeto date
    Aceita formatos: dd/mm/yyyy ou yyyy-mm-dd
    """
    if not data_str:
        return None
    
    data_str = data_str.strip()
    
    for fmt in ('%d/%m/%Y', '%Y-%m-%d'):
        try:
            return datetime.strptime(data_str, fmt).date()
        except ValueError:
            pass
    
    return None


def formatar_data_iso(data_obj):
    """
    Converte objeto date para string ISO (yyyy-mm-dd)
    Para uso em inputs HTML type="date"
    """
    if not data_obj:
        return ''
    return data_obj.strftime('%Y-%m-%d')


def formatar_data_br(data_obj):
    """
    Converte objeto date para string BR (dd/mm/yyyy)
    Para exibição ao usuário
    """
    if not data_obj:
        return ''
    return data_obj.strftime('%d/%m/%Y')
