from fastapi import FastAPI, Form, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from database import SessionLocal, engine, Base
from models import Usuario, CredenciaisVivo, Empresa, EmailDestino

from baixar_fatura import baixar_fatura
from email_service import enviar_email

from extrair_dados_fatura import extrair_dados_fatura

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
    else:
        usuario.name = name
        db.commit()

    # -------- MULTIPLOS EMAILS --------
    lista_emails = email.split(",")

    for e in lista_emails:
        e = e.strip()

        if not e:
            continue

        email_existente = db.query(EmailDestino).filter(
            EmailDestino.usuario_id == usuario.id,
            EmailDestino.email == e
        ).first()

        if not email_existente:
            novo_email = EmailDestino(
                usuario_id=usuario.id,
                email=e
            )
            db.add(novo_email)

    db.commit()

    email_principal = lista_emails[0].strip()

    # -------- CREDENCIAIS --------
    credencial = db.query(CredenciaisVivo).filter(
        CredenciaisVivo.usuario_id == usuario.id
    ).first()

    if not credencial:
        credencial = CredenciaisVivo(
            usuario_id=usuario.id,
            cpf=cpf_limpo,
            name=name,
            senha=senha,
            email=email_principal
        )
        db.add(credencial)
    else:
        credencial.senha = senha
        credencial.email = email_principal

    # -------- EMPRESA --------
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

    # 🔥 AGORA APENAS CONFIRMA CADASTRO
    return HTMLResponse("""
        <script>
            alert("Usuário cadastrado com sucesso!");
            window.location.href = "/usuarios";
        </script>
    """)
# ---------------- LISTAR USUARIOS ----------------
@app.get("/usuarios", response_class=HTMLResponse)
def listar_usuarios(db: Session = Depends(get_db)):

    usuarios = db.query(Usuario).order_by(Usuario.id.desc()).all()

    botoes = ""

    for u in usuarios:
        botoes += f"""
        <div class="usuario-card">

            <div class="usuario-info">
                <strong>{u.name if u.name else "Sem nome"}</strong>
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

# ---------------- EDITAR USUARIO ----------------
@app.get("/editar-usuario/{usuario_id}", response_class=HTMLResponse)
def editar_usuario(usuario_id: int, request: Request, db: Session = Depends(get_db)):

    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()

    if not usuario:
        return HTMLResponse("<h2>Usuário não encontrado</h2>")

    credencial = db.query(CredenciaisVivo).filter(
        CredenciaisVivo.usuario_id == usuario_id
    ).first()

    empresa = db.query(Empresa).filter(
        Empresa.usuario_id == usuario_id
    ).first()

    emails = db.query(EmailDestino).filter(
        EmailDestino.usuario_id == usuario_id
    ).all()

    lista_emails = ", ".join([e.email for e in emails])

    return templates.TemplateResponse(
        "editar_usuario.html",
        {
            "request": request,
            "usuario": usuario,
            "credencial": credencial,
            "empresa": empresa,
            "emails": lista_emails
        }
    )


# ---------------- SALVAR EDICAO ----------------
@app.post("/salvar-edicao")
def salvar_edicao(
    usuario_id: int = Form(...),
    name: str = Form(...),
    email: str = Form(...),
    senha: str = Form(...),
    cnpj: str = Form(...),
    db: Session = Depends(get_db)
):

    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()

    if not usuario:
        return HTMLResponse("<h2>Usuário não encontrado</h2>")

    usuario.name = name

    # -------- ATUALIZAR EMAILS --------
    db.query(EmailDestino).filter(
        EmailDestino.usuario_id == usuario_id
    ).delete()

    lista_emails = email.split(",")

    for e in lista_emails:

        e = e.strip()

        if not e:
            continue

        novo_email = EmailDestino(
            usuario_id=usuario_id,
            email=e
        )

        db.add(novo_email)

    # -------- ATUALIZAR CREDENCIAIS --------
    credencial = db.query(CredenciaisVivo).filter(
        CredenciaisVivo.usuario_id == usuario_id
    ).first()

    if credencial:
        credencial.senha = senha
        credencial.email = lista_emails[0].strip()

    # -------- ATUALIZAR EMPRESA --------
    empresa = db.query(Empresa).filter(
        Empresa.usuario_id == usuario_id
    ).first()

    if empresa:
        empresa.cnpj = cnpj
        empresa.nome_empresa = name

    db.commit()

    return HTMLResponse("""
        <script>
            alert("Usuário atualizado com sucesso!");
            window.location.href = "/usuarios";
        </script>
    """)


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

    db.query(EmailDestino).filter(
        EmailDestino.usuario_id == usuario_id
    ).delete()

    db.delete(usuario)

    db.commit()

    return HTMLResponse("""
        <h2>Usuário deletado com sucesso</h2>
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

    empresa = db.query(Empresa).filter(
        Empresa.usuario_id == usuario_id
    ).first()

    if not empresa:
        return HTMLResponse("<h2>Empresa não encontrada</h2>")

    try:
        caminho_pdf = baixar_fatura(
            credencial.cpf,
            credencial.senha,
            credencial.email,  # continua usando o principal aqui (ok)
            pasta,
            empresa.cnpj,
            empresa.nome_empresa
        )

    except Exception:
        return templates.TemplateResponse(
            "status.html",
            {"request": request, "mensagem": "Erro ao baixar fatura"}
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

    # 🔥 PEGAR TODOS OS EMAILS DO BANCO
    emails = db.query(EmailDestino).filter(
        EmailDestino.usuario_id == usuario_id
    ).all()

    lista_emails = ", ".join([e.email for e in emails])

    dados = extrair_dados_fatura(caminho_pdf)

    return templates.TemplateResponse(
        "confirmar.html",
        {
            "request": request,
            "pdf": "/faturas/" + os.path.basename(os.path.dirname(caminho_pdf)) + "/" + os.path.basename(caminho_pdf),
            "email": lista_emails,  # 🔥 AQUI ESTÁ A CORREÇÃO
            "nome": credencial.name,
            "valor": dados["valor"],
            "data": dados["data"],
            "linha": dados["linha"],
            "mes": dados["mes"],
            "empresa": empresa.nome_empresa if empresa else credencial.name
        }
    )
# ---------------- ENVIAR EMAIL ----------------
@app.post("/enviar-email")
def enviar_email_rota(
    request: Request,
    pdf: str = Form(...),
    email: str = Form(...),
    nome: str = Form(...),
    valor: str = Form(...),
    data: str = Form(...),
    linha: str = Form(...),
    mes: str = Form(...),
    empresa: str = Form(...),
):

    lista_emails = email.split(",")

    caminho = os.path.join(os.getcwd(), pdf.lstrip("/"))

    for e in lista_emails:

        e = e.strip()

        if not e:
            continue

        enviar_email(
            e,
            caminho,
            nome,
            valor,
            data,
            linha,
            mes,
            empresa
        )

    if os.path.exists(caminho):
        os.remove(caminho)

    return templates.TemplateResponse(
        "status.html",
        {
            "request": request,
            "mensagem": "Email enviado com sucesso!"
        }
    )