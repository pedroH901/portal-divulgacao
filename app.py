# app.py
from flask import Flask, render_template

# Cria uma instância da aplicação Flask
app = Flask(__name__)

# Define a rota para a página inicial
@app.route('/')
def index():
    """
    Esta função é chamada quando alguém acessa a URL raiz ('/').
    Ela renderiza o template 'index.html'.
    """
    return render_template('index.html')

# Inicia a aplicação
if __name__ == '__main__':
    """
    Esta condição garante que o servidor só vai rodar se o
    script for executado diretamente (e não importado).
    O modo de debug (debug=True) ajuda a ver os erros no navegador
    e recarrega o servidor automaticamente a cada alteração no código.
    """
    app.run(debug=True)