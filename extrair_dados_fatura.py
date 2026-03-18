import pdfplumber
import re

def extrair_dados_fatura(caminho_pdf):
    texto = ""

    with pdfplumber.open(caminho_pdf) as pdf:
        for pagina in pdf.pages:
            texto += pagina.extract_text() + "\n"

    valor_match = re.search(r"R\$\s?(\d+[.,]\d+)", texto)
    valor = valor_match.group(1) if valor_match else "Não encontrado"

    # 📅 DATA VENCIMENTO
    data_match = re.search(r"(\d{2}/\d{2}/\d{4})", texto)
    data = data_match.group(1) if data_match else "Não encontrado"

    # 📱 LINHA (telefone)
    linha_match = re.search(r"(\(\d{2}\)\s?\d{4,5}-\d{4})", texto)
    linha = linha_match.group(1) if linha_match else "Não encontrado"

    # 📆 MÊS (simples)
    mes_match = re.search(r"(JAN|FEV|MAR|ABR|MAI|JUN|JUL|AGO|SET|OUT|NOV|DEZ)", texto, re.IGNORECASE)
    mes = mes_match.group(1) if mes_match else "Mês atual"

    return {
        "valor": valor,
        "data": data,
        "linha": linha,
        "mes": mes
    }