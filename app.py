from fastapi import FastAPI, Form, Depends
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from database import SessionLocal, engine, Base
from models import Usuario, CredencialVivo
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
    with open("dados.html", "r", encoding="utf-8") as f:
        return f.read()


# ---------------- SALVAR E LOGAR ----------------
@app.post("/login-vivo")
def login_vivo(
    cpf: str = Form(...),
    senha: str = Form(...),
    name: str = Form(...),
    db: Session = Depends(get_db)
):
    cpf_limpo = cpf.replace(".", "").replace("-", "")

    # 🔎 Verifica se usuário já existe
    usuario = db.query(Usuario).filter(Usuario.cpf == cpf_limpo).first()

    if not usuario:
        usuario = Usuario(
            cpf=cpf_limpo,
            name=name  
        )
        db.add(usuario)
        db.commit()
        db.refresh(usuario)
    else:
       
        usuario.name = name
        db.commit()

   
    credencial = db.query(CredencialVivo).filter(
        CredencialVivo.usuario_id == usuario.id
    ).first()

    if credencial:
        credencial.senha = senha
    else:
        credencial = CredencialVivo(
            usuario_id=usuario.id,
            cpf=cpf_limpo,
            name=name,
            senha=senha
        )
        db.add(credencial)

    db.commit()

    pasta = os.path.join("faturas", cpf_limpo)

    caminho_pdf = baixar_fatura(
        cpf_limpo,
        senha,
        pasta
    )

    return {
        "status": "login realizado",
        "pdf": caminho_pdf
    }



@app.get("/usuarios", response_class=HTMLResponse)
def listar_usuarios(db: Session = Depends(get_db)):

    usuarios = db.query(Usuario).all()

    html = """
    <html>
    <head>
        <link rel="stylesheet" href="/static/style.css">
        <style>
            body {
                margin:0;
                background: linear-gradient(180deg, #f5faf8 0%, #eef5f2 100%);
                font-family: "Segoe UI", sans-serif;
                display:flex;
                justify-content:center;
                align-items:center;
                min-height:100vh;
            }

            .container {
                width:100%;
                max-width:500px;
                text-align:center;
            }

            h2 {
                color:#0b2e24;
            }

            .user-card {
                margin:12px 0;
            }

            .btn {
                width:100%;
                padding:14px;
                border:none;
                border-radius:12px;
                background:#0b5f4b;
                color:white;
                font-size:16px;
                cursor:pointer;
            }

            .btn:hover {
                background:#094c3d;
                color: white;
            }

            .secondary {
                background:#cfdad6;
                color:#0b2e24;
            }

        </style>
    </head>
    <body>
        <div class="container">
            <h2>Usuários Cadastrados</h2>
    """

    for u in usuarios:
        html += f"""
            <div class="user-card">
                <a href="/login-usuario/{u.id}">
                    <button class="btn">
                        {u.name if u.name else u.cpf}
                    </button>
                </a>
            </div>
        """

    html += """
            <br>
            <a href="/"><button class="btn secondary">Voltar</button></a>
        </div>
    </body>
    </html>
    """

    return html


# ---------------- LOGIN AUTOMÁTICO ----------------
@app.get("/login-usuario/{usuario_id}")
def login_usuario(usuario_id: int, db: Session = Depends(get_db)):

    credencial = db.query(CredencialVivo).filter(
        CredencialVivo.usuario_id == usuario_id
    ).first()

    if not credencial:
        return {"erro": "Credencial não encontrada"}

    pasta = os.path.join("faturas", credencial.cpf)

    caminho_pdf = baixar_fatura(
        credencial.cpf,
        credencial.senha,
        pasta
    )

    return {
        "status": "login automático realizado",
        "pdf": caminho_pdf
    }