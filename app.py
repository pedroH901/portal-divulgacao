# app.py
from flask import Flask, render_template
from models import db, Imovel

# Cria a instância da aplicação Flask
app = Flask(__name__)

# --- Configuração do Banco de Dados ---
# (Verifique se estes nomes correspondem ao seu ambiente)
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

# Inicializa o banco de dados com a aplicação
db.init_app(app)


# --- Rotas da Aplicação ---

@app.route('/')
def index():
    """
    Rota da página inicial.
    Busca os imóveis ativos no banco e os envia para o template.
    """
    imoveis = Imovel.query.filter(Imovel.data_exclusao.is_(None)).order_by(Imovel.destaque_ordem.desc()).all()
    return render_template('index.html', imoveis=imoveis)


@app.route('/imovel/<int:imovel_id>')
def imovel_detalhes(imovel_id):
    """
    Rota da página de detalhes de um imóvel específico.
    """
    # Busca o imóvel pelo ID ou retorna um erro 404 (Página não encontrada)
    imovel = db.get_or_404(Imovel, imovel_id)

    # Verifica se o imóvel não foi excluído logicamente
    if imovel.data_exclusao is not None:
        # Se foi excluído, também retorna 404
        return abort(404)

    # Busca outros imóveis para o carrossel, excluindo o atual
    outros_imoveis = Imovel.query.filter(
        Imovel.id_imovel != imovel_id,
        Imovel.data_exclusao.is_(None)
    ).limit(6).all()

    return render_template('imovel_detalhes.html', imovel=imovel, outros_imoveis=outros_imoveis)


# Ponto de entrada para rodar a aplicação
if __name__ == '__main__':
    app.run(debug=True)