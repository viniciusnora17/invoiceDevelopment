from playwright.sync_api import sync_playwright
import os
import time

VIVO_URL = "https://mve.vivo.com.br"


def baixar_fatura(cpf: str, senha: str, pasta_destino: str):

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=100)
        context = browser.new_context(accept_downloads=True)
        context.clear_cookies()

        page = context.new_page()

        try:
            # ========================================
            # 1️⃣ ACESSAR SITE E ESPERAR OAUTH
            # ========================================
            print("➡️ Acessando portal Vivo...")
            page.goto(VIVO_URL, timeout=60000)

            # Espera sair do oauth/logout
            page.wait_for_load_state("networkidle")
            page.wait_for_timeout(5000)

            print("🌐 URL após carregar:", page.url)

            # ========================================
            # 2️⃣ LOGIN
            # ========================================

            cpf_limpo = cpf.strip()
            senha_limpa = senha.strip()

            print("⏳ Aguardando campo CPF real...")
            page.wait_for_selector("input", timeout=30000)

            print("✏️ Preenchendo CPF...")
            cpf_input = page.locator("input").first
            cpf_input.click()
            cpf_input.fill("")
            cpf_input.type(cpf_limpo, delay=100)

            print("➡️ Clicando em continuar...")
            page.get_by_role("button", name="Continuar").click()

            # 🔥 AGORA ESPERA A TRANSIÇÃO REAL
            print("⏳ Esperando campo senha aparecer...")
            page.wait_for_selector("input[type='password']", timeout=60000)

            print("🔐 Preenchendo senha...")
            senha_input = page.locator("input[type='password']").first
            senha_input.click()
            senha_input.fill("")
            senha_input.type(senha_limpa, delay=100)

            page.get_by_role("button", name="Entrar").click()

            print("⏳ Aguardando login confirmar...")
            page.wait_for_url("**/sec**", timeout=60000)
            page.wait_for_load_state("networkidle")

            print("✅ Login confirmado")
            print("🌐 URL após login:", page.url)

            # ========================================
            # 3️⃣ ABRIR MENU CONTAS
            # ========================================
            print("➡️ Abrindo menu Contas...")

            # Garante que o menu principal carregou
            page.wait_for_selector("#menu-desktop-wrapper", timeout=60000)

            # Clica apenas no item principal "Contas" dentro do menu
            page.locator("#menu-desktop-wrapper >> span.menu-item-caption", has_text="Contas").first.click()

            page.wait_for_timeout(2000)

            # Agora clica na opção correta do submenu
            page.locator("span.submenu-item-caption", has_text="Detalhes de contas e pagamentos").first.click()

            page.wait_for_load_state("networkidle")
            page.wait_for_timeout(4000)

            print("🌐 URL após abrir contas:", page.url)

            # ========================================
            # 4️⃣ VERIFICAR STATUS
            # ========================================
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

            # ========================================
            # 5️⃣ BAIXAR FATURA
            # ========================================
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
            return caminho

        except Exception as e:
            print(f"❌ Erro inesperado: {e}")
            return None

        finally:
            browser.close()