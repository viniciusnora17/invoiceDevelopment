import yagmail
from jinja2 import Environment, FileSystemLoader

EMAIL_REMETENTE = "vnora@everco.com.br"
SENHA_APP = "jvnr gozp ghin ushl"

env = Environment(loader=FileSystemLoader("templates"))

def enviar_email(destinatario, arquivo_pdf, nome, valor, data, linha, mes, empresa):

    template = env.get_template("email_fatura.html")

    html = template.render(
        nome=nome,
        valor=valor,
        data=data,
        linha=linha,
        mes=mes,
        empresa=empresa
    )

    yag = yagmail.SMTP(EMAIL_REMETENTE, SENHA_APP)

    yag.send(
        to=destinatario,
        subject=f"Fatura Vivo - {empresa}",
        contents=[html],
        attachments=arquivo_pdf
    )

    print(f"Email enviado para {destinatario}")