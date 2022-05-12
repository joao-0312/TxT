from flask import Flask, render_template, request, session, redirect
from werkzeug.security import check_password_hash, generate_password_hash
from cs50 import SQL

app = Flask(__name__)

app.secret_key = "619da81163b0ec3be00c9d25a01437bd92260db353fed6e4d352076579cbeeab"

app.config["TEMPLATES_AUTO_RELOAD"] = True

db = SQL("sqlite:///txt.db")

@app.route("/")
def home():
    return render_template("home.html")

@app.route("/usuario")
def usuario():
    perfil = request.args.get("q")

    if not db.execute("SELECT nome FROM usuarios WHERE nome = ?", perfil):
        return render_template("erro.html", erro="Usuário inexistente.")

    # Apresenta todos os textos escritos pelo usuário
    textos = db.execute("SELECT * FROM textos WHERE nome_usuario = ? ORDER BY julian DESC", perfil)
    return render_template("usuario.html", textos=textos, perfil=perfil)

@app.route("/cadastro", methods=["GET", "POST"])
def cadastro():
    if request.method == "POST":
        nome = request.form.get("nome")
        senha = request.form.get("senha")
        repita = request.form.get("repita")
        # Procura por nomes na database iguais ao digitado
        nomeexistente = db.execute("SELECT nome FROM usuarios WHERE nome = ?", nome)

        # Alerta o usuário caso ele não insira um nome
        if not nome:
            return render_template("cadastro.html", erro = "Insira um nome.")
        # Alerta o usuário caso já exista uma conta com o nome digitado
        if nomeexistente:
            return render_template("cadastro.html", erro = "Esse nome já está em uso.")
        # Alerta o usuário caso ele não insira uma senha
        if not senha:
            return render_template("cadastro.html", erro = "Insira uma senha.")
        # Alerta o usuário caso as senhas digistadas não sejam iguais
        if senha != repita:
            return render_template("cadastro.html", erro = "As senha não correspondem.")

        # Hasheia(?) a senha
        hash = generate_password_hash(senha)

        # Insere os dados na database
        db.execute("INSERT INTO usuarios (nome, hash) VALUES (?, ?)", nome, hash)

        return redirect("/entrar")

    return render_template("cadastro.html")


@app.route("/entrar", methods=["GET", "POST"])
def entrar():
    if request.method == "POST":
        nome = request.form.get("nome")
        senha = request.form.get("senha")

        # Alerta o usuário caso ele não preencha algum dos campos
        if not nome or not senha:
            return render_template("entrar.html", erro = "Preencha todos os campos.")

        # Alerta o usuário caso o nome ou a senha estejam errados
        check = db.execute("SELECT * FROM usuarios WHERE nome = ?", nome)
        if not check or not check_password_hash(check[0]["hash"], senha):
            return render_template("entrar.html", erro = "Nome e/ou senha incorretos.")

        session["nome"] = nome
        session["id"] = check[0]["id"]
        return redirect("/usuario?q=" + nome)

    return render_template("entrar.html")

@app.route("/sair")
def sair():
    session.clear()
    return redirect("/")

@app.route("/novo", methods=["GET", "POST"])
def novo():
    if session.get("id") is None:
            return redirect("/entrar")

    if request.method == "POST":
        titulo = request.form.get("titulo")
        texto = request.form.get("texto")

        # Impede o usuário de enviar textos vazios/sem título
        if not titulo or not texto:
            return render_template("novo.html", erro = "Preencha todos os campos.")

        # Registra o texto
        db.execute("INSERT INTO textos (nome_usuario, titulo, texto, data, julian) VALUES (?, ?, ?, date(), julianday('now'))", session["nome"], titulo, texto)

        return redirect("/usuario?q=" + session.get("nome"))
    return render_template("novo.html")

@app.route("/post", methods=["GET"])
def post():
    id = request.args.get("q")
    post = db.execute("SELECT * FROM textos WHERE id = ?", id)

    return render_template("post.html", texto=post[0], nome=session.get("nome"))

@app.route("/editar", methods=["GET", "POST"])
def editar():
    if request.method == "POST":
        titulo = request.form.get("titulo")
        paragrafo = request.form.get("texto")
        id = request.form.get("id")

        # Impede o usuário de deixar os campos em branco
        if not titulo or not paragrafo:
            texto = db.execute("SELECT * FROM textos WHERE id = ?", id)
            return render_template("editar.html", texto=texto[0], erro="Todos os campos devem ser preenchidos")

        # Atualiza o texto na database
        db.execute("UPDATE textos SET titulo = ?, texto = ? WHERE id = ?", titulo, paragrafo, id)
        return redirect("/usuario?q=" + session.get("nome"))

    texto = db.execute("SELECT * FROM textos WHERE id = ?", request.args.get("editar"))
    # Impede o usuário de editar posts de outras pessoas.
    if session.get("nome") != texto[0]["nome_usuario"]:
        return render_template("erro.html", erro="Você não possui permissão para acessar essa página.")

    return render_template("editar.html", texto=texto[0])


@app.route("/excluir", methods=["POST"])
def apagar():
    # Apaga o texto da database
    db.execute("DELETE FROM textos WHERE id = ?", request.form.get("excluir"))

    return redirect("/usuario?q=" + session.get("nome"))