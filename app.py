"""
Sistema Jurídico MP - Arquivo Principal
Gerenciamento de Inquéritos e Boletins de Ocorrência
"""
from app import create_app

app = create_app('production')  # Use 'development' para debug

if __name__ == '__main__':
    app.run(debug=False)
