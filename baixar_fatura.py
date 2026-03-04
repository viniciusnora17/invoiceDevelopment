from playwright.sync_api import sync_playwright
import os
import time
import smtplib
from email.message import EmailMessage

VIVO_URL = "https://mve.vivo.com.br"


# =========================================
# 📧 FUNÇÃO PARA ENVIAR E-MAIL COM PDF
# =========================================
def enviar_email(destinatario, caminho_pdf):
    msg = EmailMessage()
    msg["Subject"] = "Sua fatura Vivo"
    msg["From"] = "SEU_EMAIL@gmail.com"  # <-- ALTERAR
    msg["To"] = destinatario
    msg.set_content("Segue em anexo sua fatura Vivo.")

    with open(caminho_pdf, "rb") as f:
        msg.add_attachment(
            f.read(),
            maintype="application",
            subtype="pdf",
            filename=os.path.basename(caminho_pdf),
        )

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login("SEU_EMAIL@gmail.com", "SUA_SENHA_DE_APP")  # <-- ALTERAR
        smtp.send_message(msg)


# =========================================
# 🔥 FUNÇÃO PRINCIPAL
# =========================================
def baixar_fatura(cpf: str, senha: str, email: str, pasta_destino: str):

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=100)
        context = browser.new_context(accept_downloads=True)
        context.clear_cookies()

        page = context.new_page()

        try:

            print("➡️ Acessando portal Vivo...")
            page.goto(VIVO_URL, timeout=60000)

            page.wait_for_load_state("networkidle")
            page.wait_for_timeout(5000)

            print("🌐 URL após carregar:", page.url)

            cpf_limpo = cpf.strip()
            senha_limpa = senha.strip()

            print("⏳ Aguardando campo CPF real...")
            page.wait_for_selector("input", timeout=30000)

            print("✏️ Preenchendo CPF...")
            cpf_input = page.locator("input").first
            cpf_input.fill("")
            cpf_input.type(cpf_limpo, delay=100)

            print("➡️ Clicando em continuar...")
            page.get_by_role("button", name="Continuar").click()

            print("⏳ Esperando campo senha aparecer...")
            page.wait_for_selector("input[type='password']", timeout=60000)

            print("🔐 Preenchendo senha...")
            senha_input = page.locator("input[type='password']").first
            senha_input.fill("")
            senha_input.type(senha_limpa, delay=100)

            page.get_by_role("button", name="Entrar").click()

            print("⏳ Aguardando login confirmar...")
            page.wait_for_url("**/sec**", timeout=60000)
            page.wait_for_load_state("networkidle")

            print("✅ Login confirmado")
            print("🌐 URL após login:", page.url)

            # =========================================
            # 🔥 MENU CONTAS → ACESSAR FATURAS
            # =========================================

            print("➡️ Abrindo menu Contas...")

            page.wait_for_selector("#menu-desktop-wrapper", timeout=60000)

            menu_contas = page.locator(
                "#menu-desktop-wrapper span.menu-item-caption",
                has_text="Contas"
            ).first

            menu_contas.hover()
            page.wait_for_timeout(1500)

            print("➡️ Clicando em Acessar faturas...")

            page.locator(
                "li[data-nav-menu-dropdown-item='invoices']"
            ).first.click()

            page.wait_for_load_state("networkidle")
            page.wait_for_timeout(4000)

            print("🌐 URL após acessar faturas:", page.url)

            # =========================================
            # 🔍 VERIFICAR STATUS DA FATURA
            # =========================================

            print("🔄 Verificando status da fatura...")

            badges = page.locator(".badge p")
            start = time.time()
            status_texts = []

            while time.time() - start < 40:
                if badges.count() > 0:
                    status_texts = [
                        badges.nth(i).inner_text().strip().lower()
                        for i in range(badges.count())
                    ]
                    break
                time.sleep(1)

            if not status_texts:
                print("⚠️ Não encontrou status.")
                return None

            print("📄 Status encontrados:", status_texts)

            if any("paga" in s or "isenta" in s for s in status_texts):
                print("✅ Fatura paga ou isenta.")
                return None

            print("⚠️ Fatura em aberto. Baixando...")

            baixar_btn = page.locator("button:has-text('Baixar fatura')").first
            baixar_btn.wait_for(state="visible", timeout=30000)
            baixar_btn.click()

            pdf_item = page.locator("a:has-text('Conta detalhada e nota fiscal')")
            pdf_item.wait_for(state="visible", timeout=30000)

            with page.expect_download() as download_info:
                pdf_item.click()

            download = download_info.value

            os.makedirs(pasta_destino, exist_ok=True)
            caminho = os.path.join(pasta_destino, download.suggested_filename)
            download.save_as(caminho)

            print(f"✅ Fatura salva em: {caminho}")

            # =========================================
            # 📧 ENVIO AUTOMÁTICO
            # =========================================

            print("📧 Enviando fatura por e-mail...")
            enviar_email(email, caminho)
            print("✅ E-mail enviado com sucesso!")

            return caminho

        except Exception as e:
            print(f"❌ Erro inesperado: {e}")
            return None

        finally:
            browser.close()