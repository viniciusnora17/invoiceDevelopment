import yagmail

EMAIL_REMETENTE = "vnora@everco.com.br"
SENHA_APP = "jvnr gozp ghin ushl"

def enviar_email(destinatario, arquivo_pdf):

    yag = yagmail.SMTP(EMAIL_REMETENTE, SENHA_APP)

    yag.send(
        to=destinatario,
        subject="Fatura Vivo",
        contents="Segue sua fatura da Vivo em anexo.",
        attachments=arquivo_pdf
    )

    print(f"📧 Email enviado para {destinatario}")