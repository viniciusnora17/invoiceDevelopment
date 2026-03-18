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
    msg["From"] = "SEU_EMAIL@gmail.com"
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
        smtp.login("SEU_EMAIL@gmail.com", "SUA_SENHA_DE_APP")
        smtp.send_message(msg)


# =========================================
# 🔥 FUNÇÃO PRINCIPAL
# =========================================
def baixar_fatura(cpf: str, senha: str, email: str, pasta_destino: str):

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=100)
        context = browser.new_context(accept_downloads=True)
        page = context.new_page()

        try:

            print("➡️ Acessando portal Vivo...")
            page.goto(VIVO_URL, timeout=60000)

            page.wait_for_load_state("networkidle")

            print("🌐 URL após carregar:", page.url)

            cpf_limpo = cpf.strip()
            senha_limpa = senha.strip()

            print("⏳ Aguardando campo CPF...")
            page.wait_for_selector("input", timeout=30000)

            print("✏️ Preenchendo CPF...")
            cpf_input = page.locator("input").first
            cpf_input.fill("")
            cpf_input.type(cpf_limpo, delay=100)

            print("➡️ Clicando em continuar...")
            page.get_by_role("button", name="Continuar").click()

            print("⏳ Esperando campo senha...")
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
            # 🔥 BLOCO INTELIGENTE - SELETOR DE EMPRESA
            # =========================================
            print("➡️ Aguardando seletor de empresa...")

            page.wait_for_selector("[data-e2e-header-customer-box]", timeout=60000)

            nome_empresa = "ARTUR MARCHI DE SOUZA"

            print("🔍 Verificando empresa atual...")

            empresa_atual = page.locator("[data-e2e-header-customer-box]").first.inner_text().strip()

            print("🏢 Empresa atual:", empresa_atual)

            empresa_atual_lower = empresa_atual.lower()
            nome_empresa_lower = nome_empresa.lower()
            cnpj_limpo = ''.join(filter(str.isdigit, cpf))

            if nome_empresa_lower in empresa_atual_lower or cnpj_limpo in empresa_atual:
                print("✅ Já está na empresa correta, não precisa trocar")

            else:
                print("🔄 Empresa diferente, abrindo seletor...")

                seletor_empresa = page.locator("[data-e2e-header-customer-box]").first
                seletor_empresa.wait_for(state="visible", timeout=30000)
                seletor_empresa.click()

                print("✅ Seletor de empresa aberto")

                page.wait_for_timeout(2000)

                print("🔍 Selecionando empresa automaticamente...")

                def formatar_cnpj(cnpj):
                    cnpj = ''.join(filter(str.isdigit, cnpj))
                    return f"{cnpj[:2]}.{cnpj[2:5]}.{cnpj[5:8]}/{cnpj[8:12]}-{cnpj[12:]}"

                cnpj_alvo = formatar_cnpj(cpf)

                page.wait_for_selector("[data-customer-select-slider-list]", timeout=30000)

                print(f"🔎 Buscando por nome: {nome_empresa}")

                empresa_bloco = page.locator(
                    "[data-slide-target]",
                    has=page.locator("[data-test-company-name]", has_text=nome_empresa)
                ).first

                if empresa_bloco.count() > 0:
                    print("✅ Encontrado pelo NOME")
                    empresa_bloco.locator("[data-test-customer]").first.click()

                else:
                    print("⚠️ Nome não encontrado, tentando pelo CNPJ...")

                    lista = page.locator("[data-test-customer]")
                    encontrado = False

                    for i in range(lista.count()):
                        texto = lista.nth(i).inner_text().strip()

                        if cnpj_alvo in texto:
                            print("✅ Encontrado pelo CNPJ")
                            lista.nth(i).click()
                            encontrado = True
                            break

                    if not encontrado:
                        print("⚠️ Não encontrou nada, selecionando primeira empresa")
                        lista.first.click()

                page.wait_for_load_state("networkidle")

                print("✅ Empresa selecionada")

            # =========================================
            # MENU CONTAS
            # =========================================
            print("➡️ Abrindo menu Contas...")

            page.wait_for_selector("#menu-desktop-wrapper", timeout=60000)

            menu_contas = page.locator(
                "#menu-desktop-wrapper span.menu-item-caption",
                has_text="Contas"
            ).first

            menu_contas.hover()
            page.wait_for_timeout(1000)

            print("➡️ Clicando em Acessar faturas...")

            page.locator(
                "li[data-nav-menu-dropdown-item='invoices']"
            ).first.click()

            page.wait_for_load_state("networkidle")

            print("🌐 URL após acessar faturas:", page.url)

            # =========================================
            # VERIFICAR STATUS
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

            if any(
                "atrasada" in s
                or "pronta pra pagar" in s
                or "aberta" in s
                for s in status_texts
            ):
                print("⚠️ Fatura em aberto. Baixando...")
            else:
                print("✅ Fatura paga ou isenta.")
                return None

            # =========================================
            # BAIXAR FATURA
            # =========================================
            baixar_btn = page.locator("button:has-text('Baixar fatura')").first
            baixar_btn.wait_for(state="visible", timeout=30000)
            baixar_btn.click()

            page.wait_for_selector(
                "a:has-text('Conta detalhada e nota fiscal')",
                timeout=30000
            )

            pdf_item = page.locator(
                "a:has-text('Conta detalhada e nota fiscal')"
            ).first

            print("⬇️ Iniciando download da fatura...")

            os.makedirs(pasta_destino, exist_ok=True)

            with page.expect_download(timeout=120000) as download_info:
                pdf_item.click()

            download = download_info.value

            caminho = os.path.abspath(
                os.path.join(pasta_destino, download.suggested_filename)
            )

            download.save_as(caminho)

            print("📂 Arquivo salvo em:", caminho)

            return caminho

        except Exception as e:
            print(f"❌ Erro inesperado: {e}")
            return "erro"

        finally:
            browser.close()