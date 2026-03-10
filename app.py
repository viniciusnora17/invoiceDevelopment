from fastapi import FastAPI, Form, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from database import SessionLocal, engine, Base
from models import Usuario, CredenciaisVivo, Empresa

from baixar_fatura import baixar_fatura, enviar_email

import os

Base.metadata.create_all(bind=engine)

app = FastAPI()

templates = Jinja2Templates(directory="templates")

app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/faturas", StaticFiles(directory="faturas"), name="faturas")


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
    request: Request,
    cpf: str = Form(...),
    senha: str = Form(...),
    name: str = Form(...),
    email: str = Form(...),
    cnpj: str = Form(...),
    db: Session = Depends(get_db)
):

    cpf_limpo = cpf.replace(".", "").replace("-", "")

    usuario = db.query(Usuario).filter(Usuario.cpf == cpf_limpo).first()

    if not usuario:
        usuario = Usuario(
            cpf=cpf_limpo,
            name=name
        )
        db.add(usuario)
        db.commit()
        db.refresh(usuario)

    credencial = db.query(CredenciaisVivo).filter(
        CredenciaisVivo.usuario_id == usuario.id
    ).first()

    if not credencial:
        credencial = CredenciaisVivo(
            usuario_id=usuario.id,
            cpf=cpf_limpo,
            name=name,
            senha=senha,
            email=email
        )
        db.add(credencial)
    else:
        credencial.senha = senha
        credencial.email = email

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

    pasta = os.path.join("faturas", cpf_limpo)

    caminho_pdf = baixar_fatura(
        cpf_limpo,
        senha,
        email,
        pasta
    )

    if caminho_pdf == "erro":
        return templates.TemplateResponse(
            "status.html",
            {"request": request, "mensagem": "Erro ao acessar portal da Vivo"}
        )

    if caminho_pdf is None:
        return templates.TemplateResponse(
            "status.html",
            {"request": request, "mensagem": "Conta já está paga"}
        )

    return templates.TemplateResponse(
        "confirmar.html",
        {
            "request": request,
            "pdf": "/faturas/" + os.path.basename(os.path.dirname(caminho_pdf)) + "/" + os.path.basename(caminho_pdf),
            "email": email
        }
    )


@app.get("/usuarios", response_class=HTMLResponse)
def listar_usuarios(db: Session = Depends(get_db)):

    usuarios = db.query(Usuario).all()

    botoes = ""

    for u in usuarios:
        botoes += f"""
        <div class="usuario-card">

            <div class="usuario-info">
                <strong>{u.name if u.name else "Sem nome"}</strong><br>

            </div>

            <div class="acoes">

                <a href="/login-usuario/{u.id}" class="btn download" title="Baixar Fatura">
                    <i class="fa-solid fa-download"></i>
                </a>

                <a href="/editar-usuario/{u.id}" class="btn editar" title="Editar">
                    <i class="fa-solid fa-pen"></i>
                </a>

                <a href="/deletar-usuario/{u.id}" class="btn deletar"
                onclick="return confirm('Tem certeza que deseja deletar?')"
                title="Deletar">
                    <i class="fa-solid fa-trash"></i>
                </a>

            </div>

        </div>
        """

    with open("templates/usuarios.html", "r", encoding="utf-8") as f:
        html = f.read()

    html = html.replace("<!-- USUARIOS -->", botoes)

    return html

# ---------------- DELETAR USUARIO ----------------
@app.get("/deletar-usuario/{usuario_id}")
def deletar_usuario(usuario_id: int, db: Session = Depends(get_db)):

    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()

    if not usuario:
        return HTMLResponse("<h2>Usuário não encontrado</h2>")

    db.query(CredenciaisVivo).filter(
        CredenciaisVivo.usuario_id == usuario_id
    ).delete()

    db.query(Empresa).filter(
        Empresa.usuario_id == usuario_id
    ).delete()

    db.delete(usuario)

    db.commit()

    return HTMLResponse("""
        <h2>Usuário deletado com sucesso</h2>
        <a href="/usuarios">Voltar</a>
    """)

# ---------------- EDITAR USUARIO ----------------
@app.get("/editar-usuario/{usuario_id}", response_class=HTMLResponse)
def editar_usuario(usuario_id: int, db: Session = Depends(get_db)):

    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    credencial = db.query(CredenciaisVivo).filter(
        CredenciaisVivo.usuario_id == usuario_id
    ).first()

    if not usuario or not credencial:
        return HTMLResponse("<h2>Usuário não encontrado</h2>")

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>

    <meta charset="UTF-8">
    <title>Editar Usuário</title>

    <link rel="stylesheet" href="/static/usuarios.css">

    </head>

    <body>

    <div class="container">

    <h2>Editar Usuário</h2>

    <form method="post" style="display: flex; flex-direction: column; gap: 25px; background: white;
    padding: 30px;
    border-radius: 16px;
    width: 400px;
    box-shadow: 0 8px 25px rgba(0, 0, 0, 0.08);" action="/salvar-edicao/{usuario_id}">

    <div style="display: flex; flex-direction: column;">
        <label style="font-weight: bold;">Nome</label>
        <input style="width: 100%;
            padding: 12px 6px 12px 6px;
            border-radius: 10px;
            border: 1px solid #d9e5e0;
            font-size: 14px;
            outline: none;" type="text" name="name" value="{usuario.name}">
    </div>

    <div style="display: flex; flex-direction: column;">
        <label style="font-weight: bold;">CPF</label>
        <input style="width: 100%;
            padding: 12px 6px 12px 6px;
            border-radius: 10px;
            border: 1px solid #d9e5e0;
            font-size: 14px;
            outline: none;" type="text" name="cpf" value="{usuario.cpf}">
    </div>

    <div style="display: flex; flex-direction: column;">
        <label style="font-weight: bold;">Email</label>
        <input style="width: 100%;
            padding: 12px 6px 12px 6px;
            border-radius: 10px;
            border: 1px solid #d9e5e0;
            font-size: 14px;
            outline: none;" type="text" name="email" value="{credencial.email}">
    </div>

    <div style="display: flex; flex-direction: column;">
        <label style="font-weight: bold;">Senha Vivo</label>
        <input style="width: 100%;
            padding: 12px 6px 12px 6px;
            border-radius: 10px;
            border: 1px solid #d9e5e0;
            font-size: 14px;
            outline: none;" type="text" name="senha" value="{credencial.senha}">
    </div>

    <button type="submit" class="btn">Salvar</button>

    </form>

    <br>

    <a href="/usuarios" style="color: black;">Voltar</a>

    </div>

    </body>
    </html>
    """

    return HTMLResponse(html)

@app.post("/salvar-edicao/{usuario_id}")
def salvar_edicao(
    usuario_id: int,
    name: str = Form(...),
    cpf: str = Form(...),
    email: str = Form(...),
    senha: str = Form(...),
    db: Session = Depends(get_db)
):

    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    credencial = db.query(CredenciaisVivo).filter(
        CredenciaisVivo.usuario_id == usuario_id
    ).first()

    usuario.name = name
    usuario.cpf = cpf

    credencial.email = email
    credencial.senha = senha

    db.commit()

    return HTMLResponse("""
        <h2>Usuário atualizado com sucesso</h2>
        <a href="/usuarios">Voltar</a>
    """)

# ---------------- LOGIN AUTOMATICO ----------------
@app.get("/login-usuario/{usuario_id}")
def login_usuario(usuario_id: int, request: Request, db: Session = Depends(get_db)):

    credencial = db.query(CredenciaisVivo).filter(
        CredenciaisVivo.usuario_id == usuario_id
    ).first()

    if not credencial:
        return HTMLResponse("<h2>Credencial não encontrada</h2>")

    pasta = os.path.join("faturas", credencial.cpf)

    caminho_pdf = baixar_fatura(
        credencial.cpf,
        credencial.senha,
        credencial.email,
        pasta
    )

    if caminho_pdf == "erro":
        return templates.TemplateResponse(
            "status.html",
            {"request": request, "mensagem": "Erro ao acessar portal da Vivo"}
        )

    if caminho_pdf is None:
        return templates.TemplateResponse(
            "status.html",
            {"request": request, "mensagem": "Conta já está paga"}
        )

    return templates.TemplateResponse(
    "confirmar.html",
    {
        "request": request,
        "pdf": "/faturas/" + os.path.basename(os.path.dirname(caminho_pdf)) + "/" + os.path.basename(caminho_pdf),
        "email": credencial.email
    }
)


# ---------------- ENVIAR EMAIL ----------------
@app.post("/enviar-email")
def enviar_email_rota(
    request: Request,
    pdf: str = Form(...),
    email: str = Form(...)
):

    caminho = pdf.lstrip("/").replace("/", os.sep)

    enviar_email(email, caminho)

    # apaga pdf depois de enviar
    if os.path.exists(caminho):
        os.remove(caminho)

    return templates.TemplateResponse(
        "status.html",
        {
            "request": request,
            "mensagem": "Email enviado com sucesso!"
        }
    )