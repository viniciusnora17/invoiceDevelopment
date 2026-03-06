from fastapi import FastAPI, Form, Depends
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

from database import SessionLocal, engine
from models import Usuario, CredenciaisVivo, Empresa
from database import Base



from baixar_fatura import baixar_fatura

import os

Base.metadata.create_all(bind=engine)

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")


# ---------------- DB ----------------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ---------------- HOME ----------------
@app.get("/", response_class=HTMLResponse)
def index():
    with open("templates/index.html", "r", encoding="utf-8") as f:
        return f.read()


# ---------------- NOVO CADASTRO ----------------
@app.get("/novo", response_class=HTMLResponse)
def novo():
    with open("templates/dados.html", "r", encoding="utf-8") as f:
        return f.read()


# ---------------- SALVAR E LOGAR ----------------
@app.post("/login-vivo")
def login_vivo(
    cpf: str = Form(...),
    senha: str = Form(...),
    name: str = Form(...),
    email: str = Form(...),
    cnpj: str = Form(...),
    db: Session = Depends(get_db)
):

    cpf_limpo = cpf.replace(".", "").replace("-", "")

    # ---------------- USUARIO ----------------
    usuario = db.query(Usuario).filter(Usuario.cpf == cpf_limpo).first()

    if not usuario:
        usuario = Usuario(
            cpf=cpf_limpo,
            name=name
        )
        db.add(usuario)
        db.commit()
        db.refresh(usuario)

    # ---------------- CREDENCIAL ----------------
    credencial = db.query(CredenciaisVivo).filter(
        CredenciaisVivo.usuario_id == usuario.id
    ).first()

    if not credencial:
        credencial = CredenciaisVivo(
            usuario_id=usuario.id,
            cpf=cpf_limpo,
            name=name,
            senha=senha
        )
        db.add(credencial)
    else:
        credencial.senha = senha

    # ---------------- EMPRESA ----------------
    empresa = db.query(Empresa).filter(
        Empresa.usuario_id == usuario.id,
        Empresa.cnpj == cnpj
    ).first()

    if not empresa:
        empresa = Empresa(
            usuario_id=usuario.id,
            cnpj=cnpj,
            nome_empresa=name
        )
        db.add(empresa)
        db.commit()
        db.refresh(empresa)

    db.commit()

    # ---------------- BAIXAR FATURA ----------------
    pasta = os.path.join("faturas", cpf_limpo)

    caminho_pdf = baixar_fatura(
         cpf_limpo,
            senha,
            email,
            pasta
    )

    return {
        "status": "ok",
        "usuario_id": usuario.id,
        "empresa_id": empresa.id,
        "pdf": caminho_pdf
    }


# ---------------- LISTAR USUARIOS ----------------
@app.get("/usuarios", response_class=HTMLResponse)
def listar_usuarios(db: Session = Depends(get_db)):

    usuarios = db.query(Usuario).all()

    botoes = ""

    for u in usuarios:
        botoes += f"""
        <div>
            <a href="/login-usuario/{u.id}">
                <button class="btn">
                    {u.name if u.name else u.cpf}
                </button>
            </a>
        </div>
        """

    with open("templates/usuarios.html", "r", encoding="utf-8") as f:
        html = f.read()

    html = html.replace("<!-- USUARIOS -->", botoes)

    return html



# ---------------- LOGIN AUTOMATICO ----------------
@app.get("/login-usuario/{usuario_id}", response_class=HTMLResponse)
def login_usuario(usuario_id: int, db: Session = Depends(get_db)):

    credencial = db.query(CredenciaisVivo).filter(
        CredenciaisVivo.usuario_id == usuario_id
    ).first()

    if not credencial:
        return """
        <h2>Erro</h2>
        <p>Credencial não encontrada</p>
        <a href="/"><button>Voltar ao início</button></a>
        """

    pasta = os.path.join("faturas", credencial.cpf)

    caminho_pdf = baixar_fatura(
        credencial.cpf,
        credencial.senha,
        credencial.email,
        pasta
    )

    # ---------------- ERRO NO ROBÔ ----------------
    if caminho_pdf == "erro":

        return """
        <html>
        <head>
            <link rel="stylesheet" href="/static/style.css">
        </head>

        <body>

        <div class="container">

            <h2>❌ Erro ao processar</h2>

            <p>
            Ocorreu um erro ao acessar o portal da Vivo.
            </p>

            <a href="/">
                <button>Voltar ao início</button>
            </a>

        </div>

        </body>
        </html>
        """

    # ---------------- FATURA ENVIADA ----------------
    elif caminho_pdf:

        return """
        <html>
        <head>
            <link rel="stylesheet" href="/static/style.css">
        </head>

        <body>

        <div class="container">

            <h2>✅ Fatura enviada!</h2>

            <p>
            A fatura foi enviada para o email cadastrado.
            </p>

            <a href="/">
                <button>Voltar ao início</button>
            </a>

        </div>

        </body>
        </html>
        """

    # ---------------- CONTA JÁ PAGA ----------------
    else:

        return """
        <html>
        <head>
            <link rel="stylesheet" href="/static/style.css">
        </head>

        <body>

        <div class="container">

            <h2>💳 Conta já está paga</h2>

            <p>
            Não existem faturas em aberto para este cliente.
            </p>

            <a href="/">
                <button>Voltar ao início</button>
            </a>

        </div>

        </body>
        </html>
        """