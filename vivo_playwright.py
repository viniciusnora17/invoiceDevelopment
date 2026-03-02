from playwright.sync_api import sync_playwright
import time

VIVO_URL = "https://mve.vivo.com.br"

def listar_empresas(cpf: str, senha: str):
    empresas = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        page.goto(VIVO_URL, timeout=60000)
        page.wait_for_selector("#login-input")
        page.fill("#login-input", cpf)
        page.click("button[data-test-access-button]")

        page.wait_for_selector("input[type='password']")
        page.fill("input[type='password']", senha)
        page.click("button[data-test-access-button]")

        page.wait_for_url("**/sec", timeout=60000)
        page.wait_for_load_state("networkidle")

        time.sleep(2)

        # ⚠️ ESSE SELETOR PODE VARIAR
        cards = page.locator(".empresa-card")

        for i in range(cards.count()):
            nome = cards.nth(i).locator(".empresa-nome").inner_text()
            cnpj = cards.nth(i).locator(".empresa-cnpj").inner_text()

            empresas.append({
                "nome": nome.strip(),
                "cnpj": cnpj.strip()
            })

        browser.close()

    return empresas
