# models.py
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Imovel(db.Model):
    __tablename__ = 'Imoveis'
    id_imovel = db.Column('Id_imovel', db.Integer, primary_key=True)
    titulo = db.Column('Titulo', db.String(150), nullable=False)
    descricao = db.Column('Descricao', db.Text)
    preco = db.Column('Preco', db.Numeric(18, 2), nullable=False)
    bairro = db.Column('Bairro', db.String(100))
    cidade = db.Column('Cidade', db.String(100))
    estado = db.Column('Estado', db.String(2))
    area_construida = db.Column('AreaConstruida', db.Numeric(10, 2))
    quartos = db.Column('Quartos', db.Integer)
    suites = db.Column('Suites', db.Integer)
    banheiros = db.Column('Banheiros', db.Integer)
    vagas = db.Column('Vagas', db.Integer)
    destaque_ordem = db.Column('DestaqueOrdem', db.Integer, default=0)
    data_exclusao = db.Column('DataExclusao', db.DateTime, nullable=True)

    # Relacionamento para buscar as imagens
    imagens = db.relationship('ImagemImovel', backref='imovel', lazy=True)

    def __repr__(self):
        return f'<Imovel {self.titulo}>'

class ImagemImovel(db.Model):
    __tablename__ = 'ImagensImovel'
    id_imagem = db.Column('Id_imagem', db.Integer, primary_key=True)
    id_imovel = db.Column('Id_imovel', db.Integer, db.ForeignKey('Imoveis.Id_imovel'), nullable=False)
    url_imagem = db.Column('UrlImagem', db.String(255), nullable=False)
    ordem = db.Column('Ordem', db.Integer, default=0)

    def __repr__(self):
        return f'<Imagem {self.url_imagem}>'