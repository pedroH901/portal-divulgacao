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

@app.route('/imovel/<int:imovel_id>')
def imovel_detalhes(imovel_id):
    # Busca o imóvel principal pelo ID. Retorna erro 404 se não encontrar.
    imovel = Imovel.query.filter_by(id_imovel=imovel_id, data_exclusao=None).first_or_404()
    
    # Busca outros imóveis para o carrossel (excluindo o imóvel atual)
    outros_imoveis = Imovel.query.filter(Imovel.id_imovel != imovel_id, Imovel.data_exclusao.is_(None)).limit(6).all()

    # Envia AMBOS (o imóvel principal e a lista de outros) para o template.
    return render_template('imovel_detalhes.html', imovel=imovel, outros_imoveis=outros_imoveis)


if __name__ == '__main__':
    app.run(debug=True)