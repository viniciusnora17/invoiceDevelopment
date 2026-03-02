# Configurações do Sistema de Automação Vivo
# IMPORTANTE: Renomeie este arquivo para config.py e preencha com suas credenciais

# Configurações de Email (SMTP)
SMTP_HOST = 'smtp.gmail.com'  # Para Gmail
SMTP_PORT = 587

# Credenciais de email
EMAIL_USUARIO = 'seu_email@gmail.com'  # ALTERAR
EMAIL_SENHA = 'sua_senha_de_app'  # ALTERAR - usar senha de aplicativo, não a senha normal

# Diretório para salvar faturas
PASTA_FATURAS = 'faturas'

# Configurações do banco de dados
DATABASE_PATH = 'vivo_clientes.db'

# ============================================
# INSTRUÇÕES PARA CONFIGURAR EMAIL NO GMAIL:
# ============================================
# 1. Acesse: https://myaccount.google.com/security
# 2. Ative a verificação em duas etapas
# 3. Vá em "Senhas de app"
# 4. Selecione "Email" e "Outro dispositivo"
# 5. Copie a senha de 16 caracteres gerada
# 6. Use essa senha no campo EMAIL_SENHA acima
#
# Para outros provedores de email:
# - Outlook/Hotmail: smtp.office365.com (porta 587)
# - Yahoo: smtp.mail.yahoo.com (porta 587)
# - Verifique as configurações SMTP do seu provedor

# ============================================
# OBSERVAÇÕES IMPORTANTES:
# ============================================
# 1. As URLs e endpoints da Vivo são exemplos
#    Você precisará inspecionar o site da Vivo para obter as URLs reais
# 2. Use ferramentas como DevTools do navegador (F12) para:
#    - Ver requisições de login
#    - Identificar URLs de download de fatura
#    - Capturar tokens/cookies necessários
# 3. A Vivo pode usar CAPTCHA ou autenticação de dois fatores
#    Nestes casos, será necessário adaptar o código