# app.py
from flask import Flask, render_template, request, flash, redirect, url_for, abort
from models import db, Imovel, Lead, Usuario # Importe Lead e Usuario

app = Flask(__name__)

# --- Configurações ---
# Chave secreta para o Flask poder mostrar mensagens "flash" de forma segura.
app.config['SECRET_KEY'] = 'uma-chave-secreta-bem-aleatoria-para-seguranca'

# Configuração do Banco de Dados (mantenha a sua)
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


# --- Rotas da Aplicação ---

@app.route('/')
def index():
    imoveis = Imovel.query.filter(Imovel.data_exclusao.is_(None)).order_by(Imovel.destaque_ordem.desc()).all()
    return render_template('index.html', imoveis=imoveis)


# Rota atualizada para aceitar GET (mostrar página) e POST (receber dados do formulário)
@app.route('/imovel/<int:imovel_id>', methods=['GET', 'POST'])
def imovel_detalhes(imovel_id):
    imovel = db.get_or_404(Imovel, imovel_id)
    if imovel.data_exclusao is not None:
        abort(404)

    # Se a requisição for do tipo POST (formulário enviado)
    if request.method == 'POST':
        # 1. Pega os dados do formulário
        nome = request.form.get('nome')
        email = request.form.get('email')
        telefone = request.form.get('telefone')
        mensagem = request.form.get('mensagem')

        # 2. Cria um novo "Lead" com esses dados
        novo_lead = Lead(
            nome=nome,
            email=email,
            telefone=telefone,
            mensagem=mensagem,
            id_imovel=imovel.id_imovel,
            id_usuario_responsavel=imovel.id_usuario # Associa o lead ao corretor dono do imóvel
        )
        
        # 3. Adiciona o novo lead ao banco de dados
        db.session.add(novo_lead)
        db.session.commit()

        # 4. Cria uma mensagem de sucesso para o usuário
        flash('Contato enviado com sucesso! Em breve um corretor retornará.', 'success')
        
        # 5. Redireciona de volta para a mesma página (evita reenvio do formulário)
        return redirect(url_for('imovel_detalhes', imovel_id=imovel_id))

    # Se a requisição for GET, apenas mostra a página normalmente
    outros_imoveis = Imovel.query.filter(
        Imovel.id_imovel != imovel_id,
        Imovel.data_exclusao.is_(None)
    ).limit(6).all()
    
    return render_template('imovel_detalhes.html', imovel=imovel, outros_imoveis=outros_imoveis)


if __name__ == '__main__':
    app.run(debug=True)
