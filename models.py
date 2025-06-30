# models.py
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

# Cria a instância do SQLAlchemy que será usada em toda a aplicação.
db = SQLAlchemy()

# Tabela de Associação (ou Tabela de Ligação)
# Esta tabela é especial e não precisa de uma classe Model.
# Ela conecta as tabelas Imoveis e Caracteristicas em uma relação Muitos-para-Muitos.
imovel_caracteristicas = db.Table('imovel_caracteristicas',
    db.Column('Id_imovel', db.Integer, db.ForeignKey('Imoveis.Id_imovel'), primary_key=True),
    db.Column('Id_caracteristica', db.Integer, db.ForeignKey('Caracteristicas.Id_caracteristica'), primary_key=True)
)

class Usuario(db.Model):
    """ Mapeia a tabela 'Usuarios' do banco de dados. """
    __tablename__ = 'Usuarios'
    id_usuario = db.Column('Id_usuario', db.Integer, primary_key=True)
    nome = db.Column('Nome', db.String(100), nullable=False)
    email = db.Column('Email', db.String(100), unique=True, nullable=False)
    senha_hash = db.Column('SenhaHash', db.String(255), nullable=False)
    telefone = db.Column('Telefone', db.String(20))
    tipo_usuario = db.Column('TipoUsuario', db.String(20), nullable=False)
    tipo_documento = db.Column('TipoDocumento', db.String(4))
    documento = db.Column('Documento', db.String(18), unique=True)
    data_cadastro = db.Column('DataCadastro', db.DateTime, nullable=False, default=datetime.utcnow)
    aceitou_lgpd = db.Column('AceitouLGPD', db.Boolean, default=False)
    aceitou_contrato = db.Column('AceitouContrato', db.Boolean, default=False)
    data_exclusao = db.Column('DataExclusao', db.DateTime, nullable=True)

    # Relacionamentos: um usuário pode ter vários imóveis e ser responsável por vários leads.
    imoveis = db.relationship('Imovel', backref='anunciante', lazy=True)
    leads_responsavel = db.relationship('Lead', backref='responsavel', lazy=True, foreign_keys='Lead.id_usuario_responsavel')

class Imovel(db.Model):
    """ Mapeia a tabela 'Imoveis' do banco de dados. """
    __tablename__ = 'Imoveis'
    id_imovel = db.Column('Id_imovel', db.Integer, primary_key=True)
    id_usuario = db.Column('Id_usuario', db.Integer, db.ForeignKey('Usuarios.Id_usuario'), nullable=False)
    titulo = db.Column('Titulo', db.String(150), nullable=False)
    descricao = db.Column('Descricao', db.Text)
    preco = db.Column('Preco', db.Numeric(18, 2), nullable=False)
    bairro = db.Column('Bairro', db.String(100))
    cidade = db.Column('Cidade', db.String(100))
    estado = db.Column('Estado', db.String(2))
    area_construida = db.Column('AreaConstruida', db.Numeric(10, 2))
    quartos = db.Column('Quartos', db.Integer, default=0)
    suites = db.Column('Suites', db.Integer, default=0)
    banheiros = db.Column('Banheiros', db.Integer, default=0)
    piscina = db.Column('Piscina', db.Integer, default=0)
    vagas = db.Column('Vagas', db.Integer, default=0)
    vagas_cobertas = db.Column('VagasCobertas', db.Integer, default=0)
    area_gourmet = db.Column('AreaGourmet', db.Integer, default=0)
    data_exclusao = db.Column('DataExclusao', db.DateTime, nullable=True)
    destaque_ordem = db.Column('DestaqueOrdem', db.Integer, default=0)
    finalidade = db.Column('Finalidade', db.String(20), nullable=False, default='Venda')

    # Relacionamentos
    imagens = db.relationship('ImagemImovel', backref='imovel', lazy=True, cascade="all, delete-orphan")
    leads = db.relationship('Lead', backref='imovel_solicitado', lazy=True, foreign_keys='Lead.id_imovel')

class ImagemImovel(db.Model):
    """ Mapeia a tabela 'ImagensImovel'. """
    __tablename__ = 'ImagensImovel'
    id_imagem = db.Column('Id_imagem', db.Integer, primary_key=True)
    id_imovel = db.Column('Id_imovel', db.Integer, db.ForeignKey('Imoveis.Id_imovel'), nullable=False)
    url_imagem = db.Column('UrlImagem', db.String(255), nullable=False)
    ordem = db.Column('Ordem', db.Integer, default=0)

class Lead(db.Model):
    """ Mapeia a tabela 'Leads'. """
    __tablename__ = 'Leads'
    id_lead = db.Column('Id_lead', db.Integer, primary_key=True)
    nome = db.Column('Nome', db.String(100), nullable=False)
    email = db.Column('Email', db.String(100))
    telefone = db.Column('Telefone', db.String(20))
    mensagem = db.Column('Mensagem', db.Text)
    id_imovel = db.Column('Id_imovel', db.Integer, db.ForeignKey('Imoveis.Id_imovel'), nullable=False)
    data_contato = db.Column('DataContato', db.DateTime, nullable=False, default=datetime.utcnow)
    id_usuario_responsavel = db.Column('Id_usuario_responsavel', db.Integer, db.ForeignKey('Usuarios.Id_usuario'), nullable=True)


class Anuncio(db.Model):
    """ Mapeia a tabela 'Anuncios'. """
    __tablename__ = 'Anuncios'
    id_anuncio = db.Column('Id_anuncio', db.Integer, primary_key=True)
    id_imovel = db.Column('Id_imovel', db.Integer, db.ForeignKey('Imoveis.Id_imovel'), nullable=False)
    data_inicio = db.Column('DataInicio', db.DateTime, nullable=False)
    data_fim = db.Column('DataFim', db.DateTime, nullable=False)
    valor_pago = db.Column('ValorPago', db.Numeric(10, 2))
    metodo_pagamento = db.Column('MetodoPagamento', db.String(30))
    status = db.Column('Status', db.String(20))

class HistoricoStatusImovel(db.Model):
    """ Mapeia a tabela 'HistoricoStatusImovel'. """
    __tablename__ = 'HistoricoStatusImovel'
    id_historico = db.Column('Id_historico', db.Integer, primary_key=True)
    id_imovel = db.Column('Id_imovel', db.Integer, db.ForeignKey('Imoveis.Id_imovel'), nullable=False)
    evento = db.Column('Evento', db.String(50), nullable=False)
    data_evento = db.Column('DataEvento', db.DateTime, nullable=False, default=datetime.utcnow)
    descricao_adicional = db.Column('DescricaoAdicional', db.Text)

class ConfiguracaoSistema(db.Model):
    """ Mapeia a tabela 'ConfiguracoesSistema'. """
    __tablename__ = 'ConfiguracoesSistema'
    chave = db.Column('Chave', db.String(50), primary_key=True)
    valor = db.Column('Valor', db.String(255), nullable=False)
