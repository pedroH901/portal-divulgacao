# app.py
from urllib.parse import quote_plus
from flask import Flask, render_template, request, flash, redirect, url_for, abort
import os
from werkzeug.utils import secure_filename
from models import ImagemImovel, db, Imovel, Lead, Usuario 
from flask_login import LoginManager, login_user, current_user, logout_user, login_required
from flask_bcrypt import Bcrypt
from sqlalchemy import func
from datetime import datetime

app = Flask(__name__)

# --- Configurações da Aplicação ---
app.config["SECRET_KEY"] = "uma-chave-secreta-bem-aleatoria-para-seguranca"
SERVER_NAME = "localhost"
DATABASE_NAME = "SeuNovoImovel"
app.config["UPLOAD_FOLDER"] = "static/uploads/imoveis"
app.config["UPLOAD_FOLDER_PERFIS"] = "static/uploads/perfis"  # NOVA PASTA
app.config["ALLOWED_EXTENSIONS"] = {"png", "jpg", "jpeg", "gif", "webp"}

connection_string = (
    f"DRIVER={{ODBC Driver 18 for SQL Server}};"
    f"SERVER={SERVER_NAME};"
    f"DATABASE={DATABASE_NAME};"
    f"Trusted_Connection=yes;"
    f"TrustServerCertificate=yes;"
)
app.config["SQLALCHEMY_DATABASE_URI"] = (
    f"mssql+pyodbc:///?odbc_connect={connection_string.replace(';', '%3B')}"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Inicializa as extensões
db.init_app(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"
login_manager.login_message = "Por favor, faça o login para acessar esta página."
login_manager.login_message_category = "info"

@app.template_filter('humanize_price')
def humanize_price_filter(value):
    """
    Formata um número para o padrão de moeda brasileiro.
    Exemplo: 1200000.50 -> 1.200.000,50
    """
    try:
        value = float(value)
        # O 'v' é um placeholder temporário para trocar ponto e vírgula corretamente
        return f"{value:,.2f}".replace(",", "v").replace(".", ",").replace("v", ".")
    except (ValueError, TypeError):
        # Se o valor não for um número, retorna o valor original sem quebrar o site
        return value

def allowed_file(filename):
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in app.config["ALLOWED_EXTENSIONS"]
    )


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(Usuario, int(user_id))


# --- Rotas Públicas ---


@app.route('/')
def index():
    """
    Rota da página inicial.
    Executa a lógica de rotação numérica e exibe os imóveis de forma paginada.
    """
    # --- LÓGICA DE ROTAÇÃO NUMÉRICA ---
    try:
        # 1. Encontra o imóvel com a maior ordem (o "último da fila")
        ultimo_imovel = Imovel.query.filter(Imovel.data_exclusao.is_(None)).order_by(Imovel.destaque_ordem.desc()).first()
        
        # 2. Encontra o imóvel com a menor ordem (o "primeiro da fila")
        primeiro_imovel = Imovel.query.filter(Imovel.data_exclusao.is_(None)).order_by(Imovel.destaque_ordem.asc()).first()

        if ultimo_imovel and primeiro_imovel and ultimo_imovel != primeiro_imovel:
            # 3. Move o último para a primeira posição, dando a ele uma ordem menor que a do primeiro
            ultimo_imovel.destaque_ordem = primeiro_imovel.destaque_ordem - 1
            db.session.commit()
            
    except Exception as e:
        print(f"AVISO: Falha na lógica de rotação numérica. Erro: {e}")
        db.session.rollback()

    # --- LÓGICA DE EXIBIÇÃO COM PAGINAÇÃO ---
    page = request.args.get('page', 1, type=int)
    
    # A consulta agora ordena pela 'DestaqueOrdem', que nós manipulamos
    pagination = Imovel.query.filter(Imovel.data_exclusao.is_(None))\
                             .order_by(Imovel.destaque_ordem.asc())\
                             .paginate(page=page, per_page=6, error_out=False)
    
    imoveis = pagination.items
    return render_template('index.html', imoveis=imoveis, pagination=pagination)


@app.route("/imovel/<int:imovel_id>", methods=["GET", "POST"])
def imovel_detalhes(imovel_id):
    imovel = db.get_or_404(Imovel, imovel_id)
    if imovel.data_exclusao is not None:
        abort(404)

    if request.method == "POST":
        nome = request.form.get("nome")
        email = request.form.get("email")
        telefone = request.form.get("telefone")
        mensagem = request.form.get("mensagem")

        novo_lead = Lead(
            nome=nome,
            email=email,
            telefone=telefone,
            mensagem=mensagem,
            id_imovel=imovel.id_imovel,
            id_usuario_responsavel=imovel.id_usuario,
        )

        db.session.add(novo_lead)
        db.session.commit()

        flash("Contato enviado com sucesso! Em breve um corretor retornará.", "success")
        return redirect(url_for("imovel_detalhes", imovel_id=imovel_id))

    link_whatsapp = None
    try:
        if imovel.anunciante and imovel.anunciante.telefone:
            telefone_limpo = "".join(filter(str.isdigit, imovel.anunciante.telefone))
            if telefone_limpo:
                mensagem_wpp = f"Olá, tenho interesse no imóvel '{imovel.titulo}', que vi no portal."
                mensagem_encoded = quote_plus(mensagem_wpp)
                link_whatsapp = (
                    f"https://wa.me/55{telefone_limpo}?text={mensagem_encoded}"
                )
    except Exception as e:
        print(f"AVISO: Não foi possível gerar link do WhatsApp. Erro: {e}")
        link_whatsapp = None

    outros_imoveis = (
        Imovel.query.filter(
            Imovel.id_imovel != imovel.id_imovel,  # 1. Exclui o próprio imóvel
            Imovel.data_exclusao.is_(None),  # 2. Apenas imóveis ativos
            Imovel.cidade == imovel.cidade,  # 3. Apenas imóveis na mesma cidade
        )
        .order_by(Imovel.data_publicacao.desc())
        .limit(6)
        .all()
    )  # 4. ORDENA PELOS MAIS RECENTES

    return render_template(
        "imovel_detalhes.html",
        imovel=imovel,
        outros_imoveis=outros_imoveis,
        link_whatsapp=link_whatsapp,
    )


@app.route("/buscar")
def buscar():
    page = request.args.get("page", 1, type=int)
    search_params = request.args.to_dict()
    search_params.pop("page", None)
    base_query = Imovel.query.filter(Imovel.data_exclusao.is_(None))

    if search_params.get("finalidade"):
        base_query = base_query.filter(Imovel.finalidade == search_params["finalidade"])
    if search_params.get("tipo"):
        base_query = base_query.filter(
            Imovel.titulo.ilike(f'%{search_params["tipo"]}%')
        )
    if search_params.get("cidade"):
        base_query = base_query.filter(
            Imovel.cidade.ilike(f'%{search_params["cidade"]}%')
        )
    if search_params.get("bairro"):
        base_query = base_query.filter(
            Imovel.bairro.ilike(f'%{search_params["bairro"]}%')
        )
    if search_params.get("quartos"):
        try:
            num_quartos = int(search_params["quartos"])
            base_query = base_query.filter(Imovel.quartos >= num_quartos)
        except (ValueError, TypeError):
            pass

    pagination = base_query.order_by(Imovel.destaque_ordem.desc()).paginate(
        page=page, per_page=9, error_out=False
    )

    resultados = pagination.items
    total_resultados = pagination.total

    return render_template(
        "resultados.html",
        imoveis=resultados,
        total_resultados=total_resultados,
        pagination=pagination,
        search_params=search_params,
    )


# --- ROTAS DE AUTENTICAÇÃO E PAINEL ---


# ESTA É A ÚNICA E CORRETA FUNÇÃO 'login'
@app.route("/painel-controle", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))
    if request.method == "POST":
        email = request.form.get("email")
        senha = request.form.get("senha")
        user = Usuario.query.filter_by(email=email).first()
        if user and bcrypt.check_password_hash(user.senha_hash, senha):
            login_user(user, remember=True)
            next_page = request.args.get("next")
            return redirect(next_page) if next_page else redirect(url_for("dashboard"))
        else:
            flash("Login falhou. Verifique o e-mail e a senha.", "danger")

    return render_template("login.html", title="Login")


@app.route("/dashboard")
@login_required  # Garante que só usuários logados acessem
def dashboard():
    """
    Busca e exibe os imóveis pertencentes ao usuário logado.
    """
    # Usamos o relacionamento 'imoveis' que definimos no models.py
    # para pegar apenas os imóveis deste usuário.
    meus_imoveis = (
        Imovel.query.filter_by(anunciante=current_user).order_by(Imovel.titulo).all()
    )

    return render_template("dashboard.html", title="Painel", meus_imoveis=meus_imoveis)


@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("index"))


@app.route("/imovel/<int:imovel_id>/excluir", methods=["POST"])
@login_required
def excluir_imovel(imovel_id):
    imovel = db.get_or_404(Imovel, imovel_id)

    # NOVA VERIFICAÇÃO DE PERMISSÃO:
    # Permite a ação se o usuário for o dono do imóvel OU um admin.
    if imovel.anunciante != current_user and current_user.tipo_usuario != "admin":
        flash("Você não tem permissão para executar esta ação.", "danger")
        return redirect(url_for("dashboard"))

    # Se a permissão estiver OK, deleta o imóvel
    db.session.delete(imovel)
    db.session.commit()

    flash("Imóvel excluído com sucesso!", "success")
    return redirect(url_for("dashboard"))


@app.route("/imovel/<int:imovel_id>/editar", methods=["GET", "POST"])
@login_required
def editar_imovel(imovel_id):
    imovel = db.get_or_404(Imovel, imovel_id)

    # Verificação de permissão (dono do imóvel ou admin)
    if imovel.anunciante != current_user and current_user.tipo_usuario != "admin":
        abort(403)  # Erro de "Proibido"

    if request.method == "POST":
        # 1. Atualiza todos os campos com os dados do formulário
        imovel.titulo = request.form["titulo"]
        imovel.descricao = request.form["descricao"]
        imovel.preco = request.form["preco"]
        imovel.finalidade = request.form["finalidade"]
        imovel.bairro = request.form["bairro"]
        imovel.cidade = request.form["cidade"]
        imovel.area_construida = request.form.get("area_construida")
        imovel.quartos = request.form.get("quartos", type=int)
        imovel.banheiros = request.form.get("banheiros", type=int)
        imovel.vagas = request.form.get("vagas", type=int)
        imovel.vagas_cobertas = request.form.get("vagas_cobertas", type=int)
        imovel.piscina = 1 if "piscina" in request.form else 0
        imovel.area_gourmet = 1 if "area_gourmet" in request.form else 0

        # 2. Lógica para adicionar novas fotos (as antigas não são apagadas)
        files = request.files.getlist("imagens")
        for file in files:
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
                file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))

                nova_imagem = ImagemImovel(
                    url_imagem=os.path.join("uploads", "imoveis", filename).replace(
                        "\\", "/"
                    ),
                    id_imovel=imovel.id_imovel,
                )
                db.session.add(nova_imagem)

        # 3. Salva todas as alterações no banco de dados
        db.session.commit()
        flash("Imóvel atualizado com sucesso!", "success")
        return redirect(url_for("dashboard"))

    # Se a requisição for GET, apenas mostra a página com o formulário pré-preenchido
    return render_template("editar_imovel.html", title="Editar Imóvel", imovel=imovel)


@app.route("/imovel/novo", methods=["GET", "POST"])
@login_required
def cadastrar_imovel():
    if request.method == "POST":
        novo_imovel = Imovel(
            titulo=request.form["titulo"],
            descricao=request.form.get("descricao"),
            preco=request.form.get("preco"),
            finalidade=request.form.get("finalidade"),
            cidade=request.form.get("cidade"),
            bairro=request.form.get("bairro"),
            area_construida=request.form.get("area_construida"),
            quartos=request.form.get("quartos", type=int, default=0),
            banheiros=request.form.get("banheiros", type=int, default=0),
            vagas=request.form.get("vagas", type=int, default=0),
            vagas_cobertas=request.form.get("vagas_cobertas", type=int, default=0),
            piscina=1 if "piscina" in request.form else 0,
            area_gourmet=1 if "area_gourmet" in request.form else 0,
            id_usuario=current_user.id_usuario,
        )
        db.session.add(novo_imovel)
        db.session.commit()

        files = request.files.getlist("imagens")
        for file in files:
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
                file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))

                nova_imagem = ImagemImovel(
                    url_imagem=os.path.join("uploads", "imoveis", filename).replace(
                        "\\", "/"
                    ),
                    id_imovel=novo_imovel.id_imovel,
                )
                db.session.add(nova_imagem)

        db.session.commit()
        flash("Novo imóvel cadastrado com sucesso!", "success")
        return redirect(url_for("dashboard"))

    return render_template("cadastrar_imovel.html", title="Cadastrar Novo Imóvel")


@app.route("/registrar", methods=["GET", "POST"])
def registrar():
    # Se o usuário já estiver logado, não faz sentido ver esta página
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        nome = request.form.get("nome")
        email = request.form.get("email")
        senha = request.form.get("senha")
        confirmar_senha = request.form.get("confirmar_senha")

        # --- Validações ---
        # 1. Verifica se a senha e a confirmação são iguais
        if senha != confirmar_senha:
            flash("As senhas não coincidem. Por favor, tente novamente.", "danger")
            return redirect(url_for("registrar"))

        # 2. Verifica se o e-mail já existe no banco de dados
        usuario_existente = Usuario.query.filter_by(email=email).first()
        if usuario_existente:
            flash(
                "Este endereço de e-mail já está em uso. Por favor, faça o login.",
                "warning",
            )
            return redirect(url_for("login"))

        # --- Criação do Usuário ---
        # 3. Criptografa a senha antes de salvar
        hash_senha = bcrypt.generate_password_hash(senha).decode("utf-8")

        # 4. Cria o novo usuário (definindo como 'corretor' por padrão)
        novo_usuario = Usuario(
            nome=nome, email=email, senha_hash=hash_senha, tipo_usuario="corretor"
        )

        # 5. Salva o novo usuário no banco
        db.session.add(novo_usuario)
        db.session.commit()

        flash("Conta criada com sucesso! Agora você já pode fazer o login.", "success")
        return redirect(url_for("login"))

    return render_template("registrar.html", title="Registrar")


@app.route("/imagem/<int:imagem_id>/excluir", methods=["POST"])
@login_required
def excluir_imagem(imagem_id):
    """Rota para excluir uma imagem específica de um imóvel."""
    imagem = db.get_or_404(ImagemImovel, imagem_id)
    imovel = imagem.imovel  # Acessa o imóvel "pai" através do backref

    # Verificação de permissão: só o dono do imóvel ou um admin pode excluir.
    if imovel.anunciante != current_user and current_user.tipo_usuario != "admin":
        flash("Você não tem permissão para excluir esta imagem.", "danger")
        return redirect(url_for("editar_imovel", imovel_id=imovel.id_imovel))

    try:
        # Tenta apagar o arquivo físico do servidor
        caminho_arquivo = os.path.join(
            app.config["UPLOAD_FOLDER"], os.path.basename(imagem.url_imagem)
        )
        if os.path.exists(caminho_arquivo):
            os.remove(caminho_arquivo)
    except Exception as e:
        # Se não conseguir apagar o arquivo, apenas avisa no terminal, mas continua.
        print(f"AVISO: Não foi possível apagar o arquivo físico da imagem. Erro: {e}")

    # Apaga o registro da imagem do banco de dados
    db.session.delete(imagem)
    db.session.commit()

    flash("Imagem excluída com sucesso!", "success")
    # Redireciona de volta para a mesma página de edição
    return redirect(url_for("editar_imovel", imovel_id=imovel.id_imovel))


@app.route("/comprar")
def comprar():
    """
    Mostra todos os imóveis disponíveis para Venda, com paginação.
    """
    page = request.args.get("page", 1, type=int)

    # A consulta agora filtra especificamente por Finalidade == 'Venda'
    pagination = (
        Imovel.query.filter_by(finalidade="Venda", data_exclusao=None)
        .order_by(Imovel.destaque_ordem.desc())
        .paginate(page=page, per_page=9, error_out=False)
    )

    imoveis_a_venda = pagination.items

    return render_template(
        "comprar.html",
        imoveis=imoveis_a_venda,
        title="Imóveis à Venda",
        pagination=pagination,
    )


@app.route("/alugar")
def alugar():
    """
    Mostra todos os imóveis disponíveis para Aluguel, com paginação.
    """
    page = request.args.get("page", 1, type=int)

    # A única mudança é aqui: filtramos por 'Aluguel'
    pagination = (
        Imovel.query.filter_by(finalidade="Aluguel", data_exclusao=None)
        .order_by(Imovel.destaque_ordem.desc())
        .paginate(page=page, per_page=9, error_out=False)
    )

    imoveis_para_alugar = pagination.items

    return render_template(
        "alugar.html",
        imoveis=imoveis_para_alugar,
        title="Imóveis para Alugar",
        pagination=pagination,
    )


@app.route("/termos-de-uso")
def termos_de_uso():
    """Rota para a página de Termos de Uso."""
    return render_template("termos_de_uso.html", title="Termos de Uso")


@app.route("/politica-de-privacidade")
def politica_de_privacidade():
    """Rota para a página de Política de Privacidade."""
    return render_template(
        "politica_de_privacidade.html", title="Política de Privacidade"
    )


@app.route("/anunciar")
@login_required  # Garante que só usuários logados possam ver esta página
def anunciar():
    """
    Mostra a página onde o usuário pode escolher um plano
    para anunciar um novo imóvel.
    """
    return render_template("anunciar.html", title="Anunciar um Imóvel")


@app.route("/dashboard/leads")
@login_required
def meus_leads():
    """
    Mostra uma lista de todos os leads recebidos nos imóveis
    do usuário logado.
    """
    # Esta consulta busca os leads e já otimiza a busca pelo imóvel relacionado
    # para evitar múltiplas consultas ao banco de dados (join).
    leads = (
        Lead.query.join(Imovel)
        .filter(Imovel.id_usuario == current_user.id_usuario)
        .order_by(Lead.data_contato.desc())
        .all()
    )

    return render_template("meus_leads.html", title="Meus Leads", leads=leads)


# Em app.py


@app.route("/minha-conta", methods=["GET", "POST"])
@login_required
def minha_conta():
    user = current_user  # Pegamos o usuário logado para facilitar

    # --- LÓGICA DO POST (QUANDO O FORMULÁRIO É ENVIADO) ---
    if request.method == "POST":
        # Atualiza os dados básicos
        user.nome = request.form.get("nome")
        user.email = request.form.get("email")
        user.telefone = request.form.get("telefone")

        # Lógica para o upload da foto de perfil
        if "foto_perfil" in request.files:
            file = request.files["foto_perfil"]
            if file and file.filename != "" and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                os.makedirs(app.config["UPLOAD_FOLDER_PERFIS"], exist_ok=True)
                file.save(os.path.join(app.config["UPLOAD_FOLDER_PERFIS"], filename))
                user.foto_perfil = os.path.join("uploads", "perfis", filename).replace(
                    "\\", "/"
                )

        # Lógica para alterar a senha
        senha_atual = request.form.get("senha_atual")
        nova_senha = request.form.get("nova_senha")

        if nova_senha and senha_atual:
            if bcrypt.check_password_hash(user.senha_hash, senha_atual):
                if nova_senha == request.form.get("confirmar_nova_senha"):
                    user.senha_hash = bcrypt.generate_password_hash(nova_senha).decode(
                        "utf-8"
                    )
                    flash("Sua senha foi atualizada com sucesso!", "success")
                else:
                    flash("A nova senha e a confirmação não coincidem.", "danger")
            else:
                flash("A sua senha atual está incorreta.", "danger")

        db.session.commit()
        if not nova_senha:
            flash("Seus dados foram atualizados com sucesso!", "success")

        return redirect(url_for("minha_conta"))

    # --- LÓGICA DO GET (QUANDO A PÁGINA É CARREGADA) ---
    # Este bloco agora é executado APENAS quando a página é aberta pela primeira vez.
    url_foto_perfil = None
    if user.foto_perfil and user.foto_perfil != "default.jpg":
        url_foto_perfil = url_for("static", filename=user.foto_perfil)
    else:
        # Caminho para uma imagem padrão, caso o usuário não tenha foto.
        url_foto_perfil = url_for("static", filename="uploads/perfis/default.jpg")

    return render_template(
        "minha_conta.html", title="Minha Conta", url_foto_perfil=url_foto_perfil
    )

@app.route('/minha-conta/excluir', methods=['POST'])
@login_required
def excluir_conta():
    """ Exclui o usuário logado e todos os seus dados associados. """
    user_para_excluir = current_user
    
    try:
        # IMPORTANTE: Excluir os "filhos" antes do "pai" para evitar erros.
        # 1. Exclui os leads associados aos imóveis do usuário.
        imoveis_ids = [imovel.id_imovel for imovel in user_para_excluir.imoveis]
        if imoveis_ids:
            Lead.query.filter(Lead.id_imovel.in_(imoveis_ids)).delete(synchronize_session=False)

        # 2. Exclui os imóveis e as imagens (o 'cascade' deve cuidar das imagens)
        Imovel.query.filter_by(id_usuario=user_para_excluir.id_usuario).delete(synchronize_session=False)
        
        # 3. Agora, exclui o próprio usuário
        db.session.delete(user_para_excluir)
        
        # Encerra a sessão ANTES de salvar, para evitar conflitos
        logout_user()
        
        # 4. Salva todas as exclusões no banco de dados
        db.session.commit()
        
        flash('Sua conta e todos os seus dados foram excluídos com sucesso.', 'success')
        
    except Exception as e:
        db.session.rollback() # Desfaz tudo se der algum erro
        print(f"ERRO AO EXCLUIR CONTA: {e}")
        flash('Ocorreu um erro ao tentar excluir sua conta. Por favor, tente novamente.', 'danger')
        return redirect(url_for('minha_conta'))

    return redirect(url_for('index'))

@app.route("/dashboard/desempenho")
@login_required
def desempenho():

    return render_template("desempenho.html", title="Meu Desempenho")
    return render_template("meus_leads.html", title="Meus Leads", leads=leads)


# --- NOVA ROTA PARA A PÁGINA DE PERFIL DO CORRETOR ---
@app.route("/corretor/<int:usuario_id>")
def perfil_corretor(usuario_id):
    """
    Mostra a página de perfil de um corretor específico,
    listando todos os seus imóveis ativos.
    """
    # Busca o corretor pelo ID ou retorna um erro 404 se não existir
    corretor = db.get_or_404(Usuario, usuario_id)

    # Busca todos os imóveis ativos associados a esse corretor
    imoveis_do_corretor = (
        Imovel.query.filter_by(anunciante=corretor, data_exclusao=None)
        .order_by(Imovel.data_publicacao.desc())
        .all()
    )

    return render_template(
        "perfil_corretor.html",
        title=f"Imóveis de {corretor.nome}",
        corretor=corretor,
        imoveis=imoveis_do_corretor,
    )


# Ponto de entrada para rodar a aplicação
if __name__ == "__main__":
    app.run(debug=True)
