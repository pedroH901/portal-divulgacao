# app.py
from flask import Flask, render_template, abort
from models import db, Imovel

app = Flask(__name__)

# --- CONFIGURAÇÃO DA CONEXÃO (MANTENHA A SUA) ---
SERVER_NAME = 'localhost'
DATABASE_NAME = 'SeuNovoImovel'

connection_string = (
    f"DRIVER={{ODBC Driver 18 for SQL Server}};"
    f"SERVER={SERVER_NAME};"
    f"DATABASE={DATABASE_NAME};"
    f"Trusted_Connection=yes;"
    f"TrustServerCertificate=yes;"
)

app.config['SQLALCHEMY_DATABASE_URI'] = f"mssql+pyodbc:///?odbc_connect={connection_string.replace(';', '%3B')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

@app.route('/')
def index():
    imoveis_destaque = Imovel.query.filter(Imovel.data_exclusao.is_(None)).order_by(Imovel.destaque_ordem.desc()).all()
    return render_template('index.html', imoveis=imoveis_destaque)

# --- NOVA ROTA PARA OS DETALHES DO IMÓVEL ---
@app.route('/imovel/<int:imovel_id>')
def imovel_detalhes(imovel_id):
    # Busca o imóvel pelo ID fornecido na URL.
    # O .first_or_404() é ótimo: ele busca o primeiro resultado ou retorna um erro "Página não encontrada" automaticamente.
    imovel = Imovel.query.filter_by(id_imovel=imovel_id, data_exclusao=None).first_or_404()
    
    # Envia o objeto 'imovel' para um novo template que vamos criar.
    return render_template('imovel_detalhes.html', imovel=imovel)


if __name__ == '__main__':
    app.run(debug=True)