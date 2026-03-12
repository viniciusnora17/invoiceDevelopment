import yagmail
from jinja2 import Environment, FileSystemLoader

EMAIL_REMETENTE = "vnora@everco.com.br"
SENHA_APP = "jvnr gozp ghin ushl"

env = Environment(loader=FileSystemLoader("templates"))

def enviar_email(destinatario, arquivo_pdf, nome):

    template = env.get_template("email_fatura.html")

    html = template.render(
        nome=nome
    )

    yag = yagmail.SMTP(EMAIL_REMETENTE, SENHA_APP)

    yag.send(
        to=destinatario,
        subject="Sua fatura Vivo",
        contents=[html],
        attachments=arquivo_pdf
    )

    print(f"Email enviado para {destinatario}")