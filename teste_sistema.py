#!/usr/bin/env python3
"""
Script de Teste - Validação do Sistema
Testa a estrutura sem executar operações reais
"""

import sqlite3
import os


def testar_banco_dados():
    """Testa inicialização do banco de dados"""
    print("\n" + "="*60)
    print("TESTE 1: Banco de Dados")
    print("="*60)
    
    db_path = 'vivo_clientes_test.db'
    
    # Remover banco de teste anterior
    if os.path.exists(db_path):
        os.remove(db_path)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Criar tabelas
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS clientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            cpf TEXT UNIQUE NOT NULL,
            senha_vivo TEXT NOT NULL,
            email TEXT NOT NULL,
            ativo BOOLEAN DEFAULT 1,
            data_cadastro DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS logs_downloads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cliente_id INTEGER,
            data_download DATETIME DEFAULT CURRENT_TIMESTAMP,
            mes_referencia TEXT,
            sucesso BOOLEAN,
            mensagem TEXT,
            FOREIGN KEY (cliente_id) REFERENCES clientes (id)
        )
    ''')
    
    conn.commit()
    
    # Inserir dados de teste
    cursor.execute('''
        INSERT INTO clientes (nome, cpf, senha_vivo, email)
        VALUES (?, ?, ?, ?)
    ''', ("João Teste", "12345678900", "senha123", "joao@teste.com"))
    
    cursor.execute('''
        INSERT INTO clientes (nome, cpf, senha_vivo, email)
        VALUES (?, ?, ?, ?)
    ''', ("Maria Teste", "98765432100", "senha456", "maria@teste.com"))
    
    conn.commit()
    
    # Verificar inserção
    cursor.execute('SELECT COUNT(*) FROM clientes')
    count = cursor.fetchone()[0]
    
    if count == 2:
        print("✓ Banco de dados criado com sucesso")
        print(f"✓ {count} clientes de teste inseridos")
    else:
        print("✗ Erro ao inserir clientes")
    
    # Listar clientes
    cursor.execute('SELECT id, nome, cpf, email FROM clientes')
    clientes = cursor.fetchall()
    
    print("\nClientes cadastrados:")
    for cliente in clientes:
        print(f"  ID: {cliente[0]} | {cliente[1]} | CPF: {cliente[2][:3]}*** | {cliente[3]}")
    
    conn.close()
    
    # Limpar banco de teste
    os.remove(db_path)
    print("\n✓ Banco de teste removido")


def testar_estrutura_arquivos():
    """Testa se todos os arquivos necessários existem"""
    print("\n" + "="*60)
    print("TESTE 2: Estrutura de Arquivos")
    print("="*60)
    
    arquivos_necessarios = [
        'vivo_fatura_automation.py',
        'gerenciar_clientes.py',
        'config_example.py',
        'README.md',
        '.gitignore'
    ]
    
    todos_existem = True
    
    for arquivo in arquivos_necessarios:
        if os.path.exists(arquivo):
            print(f"✓ {arquivo}")
        else:
            print(f"✗ {arquivo} NÃO ENCONTRADO")
            todos_existem = False
    
    if todos_existem:
        print("\n✓ Todos os arquivos necessários estão presentes")
    else:
        print("\n✗ Alguns arquivos estão faltando")


def testar_importacoes():
    """Testa se todas as bibliotecas necessárias estão disponíveis"""
    print("\n" + "="*60)
    print("TESTE 3: Bibliotecas Python")
    print("="*60)
    
    bibliotecas = [
        ('sqlite3', 'Banco de dados'),
        ('smtplib', 'Envio de email'),
        ('email', 'Construção de emails'),
        ('requests', 'Requisições HTTP'),
        ('os', 'Sistema operacional'),
        ('datetime', 'Data/hora'),
        ('json', 'JSON'),
        ('getpass', 'Input seguro')
    ]
    
    todas_disponiveis = True
    
    for lib, descricao in bibliotecas:
        try:
            __import__(lib)
            print(f"✓ {lib:<15} ({descricao})")
        except ImportError:
            print(f"✗ {lib:<15} ({descricao}) - NÃO DISPONÍVEL")
            todas_disponiveis = False
    
    if todas_disponiveis:
        print("\n✓ Todas as bibliotecas necessárias estão disponíveis")
    else:
        print("\n✗ Algumas bibliotecas precisam ser instaladas")


def verificar_config():
    """Verifica se arquivo de configuração foi criado"""
    print("\n" + "="*60)
    print("TESTE 4: Configuração")
    print("="*60)
    
    if os.path.exists('config.py'):
        print("✓ Arquivo config.py encontrado")
        print("⚠ LEMBRE-SE: Verifique se as credenciais estão configuradas")
    else:
        print("⚠ Arquivo config.py não encontrado")
        print("  → Copie config_example.py para config.py")
        print("  → Configure suas credenciais de email")


def exibir_proximos_passos():
    """Exibe próximos passos para o usuário"""
    print("\n" + "="*60)
    print("PRÓXIMOS PASSOS")
    print("="*60)
    
    print("""
1. Configurar credenciais de email:
   cp config_example.py config.py
   # Edite config.py com suas credenciais

2. Obter URLs reais da Vivo:
   - Abra DevTools (F12) no navegador
   - Faça login em meuvivo.vivo.com.br
   - Capture URLs de login e download
   - Atualize em vivo_fatura_automation.py

3. Adicionar clientes:
   python3 gerenciar_clientes.py

4. Testar com um cliente:
   python3 vivo_fatura_automation.py

5. Agendar execução automática:
   - Linux: Use cron
   - Windows: Use Agendador de Tarefas

DOCUMENTAÇÃO COMPLETA: Leia README.md
    """)


def main():
    """Executa todos os testes"""
    print("\n" + "="*60)
    print("SISTEMA DE AUTOMAÇÃO VIVO - TESTES")
    print("="*60)
    
    testar_banco_dados()
    testar_estrutura_arquivos()
    testar_importacoes()
    verificar_config()
    exibir_proximos_passos()
    
    print("\n" + "="*60)
    print("TESTES CONCLUÍDOS")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()