# app.py
from urllib.parse import quote_plus
from flask import Flask, render_template, request, flash, redirect, url_for, abort
from models import db, Imovel, Lead, Usuario # Importe todos os modelos necessários

app = Flask(__name__)

# --- Configurações da Aplicação ---
# Chave secreta para o Flask poder mostrar mensagens "flash" de forma segura.
app.config['SECRET_KEY'] = 'uma-chave-secreta-bem-aleatoria-para-seguranca'

# Configuração do Banco de Dados (verifique se os nomes estão corretos)
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
    """ Rota da página inicial. """
    imoveis = Imovel.query.filter(Imovel.data_exclusao.is_(None)).order_by(Imovel.destaque_ordem.desc()).all()
    return render_template('index.html', imoveis=imoveis)


@app.route('/imovel/<int:imovel_id>', methods=['GET', 'POST'])
def imovel_detalhes(imovel_id):
    """ Rota da página de detalhes, que mostra o imóvel e processa o formulário de contato. """
    imovel = db.get_or_404(Imovel, imovel_id)
    if imovel.data_exclusao is not None:
        abort(404)

    # Se a requisição for do tipo POST (formulário de lead enviado)
    if request.method == 'POST':
        nome = request.form.get('nome')
        email = request.form.get('email')
        telefone = request.form.get('telefone')
        mensagem = request.form.get('mensagem')

        novo_lead = Lead(
            nome=nome,
            email=email,
            telefone=telefone,
            mensagem=mensagem,
            id_imovel=imovel.id_imovel,
            id_usuario_responsavel=imovel.id_usuario # Associa o lead ao corretor dono do imóvel
        )
        
        db.session.add(novo_lead)
        db.session.commit()

        flash('Contato enviado com sucesso! Em breve um corretor retornará.', 'success')
        return redirect(url_for('imovel_detalhes', imovel_id=imovel_id))

    # --- Lógica do WhatsApp (executada apenas quando a página é carregada - GET) ---
    link_whatsapp = None
    try:
        # Verifica se o imóvel tem um anunciante e se o anunciante tem telefone
        if imovel.anunciante and imovel.anunciante.telefone:
            telefone_limpo = "".join(filter(str.isdigit, imovel.anunciante.telefone))
            if telefone_limpo: # Garante que o telefone não ficou vazio após a limpeza
                mensagem_wpp = f"Olá, tenho interesse no imóvel '{imovel.titulo}', que vi no portal."
                mensagem_encoded = quote_plus(mensagem_wpp)
                link_whatsapp = f"https://wa.me/55{telefone_limpo}?text={mensagem_encoded}"
    except Exception as e:
        # Se der qualquer erro (ex: anunciante não encontrado), não quebra o site, apenas avisa no terminal.
        print(f"AVISO: Não foi possível gerar link do WhatsApp para o imóvel {imovel_id}. Erro: {e}")
        link_whatsapp = None
    
    # Busca outros imóveis para o carrossel
    outros_imoveis = Imovel.query.filter(
        Imovel.id_imovel != imovel_id,
        Imovel.data_exclusao.is_(None)
    ).limit(6).all()
    
    # Envia todas as informações para o template
    return render_template(
        'imovel_detalhes.html', 
        imovel=imovel, 
        outros_imoveis=outros_imoveis,
        link_whatsapp=link_whatsapp
    )


if __name__ == '__main__':
    app.run(debug=True)
