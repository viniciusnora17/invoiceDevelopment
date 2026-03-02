

import mysql.connector
from mysql.connector import Error
from db_config import DB_CONFIG
from getpass import getpass


def get_conn():
    return mysql.connector.connect(**DB_CONFIG)


class GerenciadorClientes:
    """Gerencia operações CRUD de clientes"""

    def __init__(self):
        pass

    def adicionar_cliente(self):
        print("\n" + "=" * 60)
        print("ADICIONAR NOVO CLIENTE")
        print("=" * 60)

        nome = input("Nome completo: ").strip()
        cpf = input("CPF (apenas números): ").strip()
        senha = getpass("Senha Vivo: ")
        email = input("Email: ").strip()

        if not all([nome, cpf, senha, email]):
            print("✗ Todos os campos são obrigatórios!")
            return

        if len(cpf) != 11 or not cpf.isdigit():
            print("✗ CPF deve conter 11 dígitos!")
            return

        if '@' not in email:
            print("✗ Email inválido!")
            return

        print("\nConfirmar dados:")
        print(f"Nome: {nome}")
        print(f"CPF: {cpf[:3]}***{cpf[-2:]}")
        print(f"Email: {email}")

        if input("\nConfirmar adição? (s/n): ").lower() != 's':
            print("✗ Operação cancelada")
            return

        try:
            conn = get_conn()
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO clientes (nome, cpf, senha_vivo, email)
                VALUES (%s, %s, %s, %s)
            """, (nome, cpf, senha, email))

            conn.commit()
            print(f"\n✓ Cliente {nome} adicionado com sucesso!")

        except Error as e:
            print(f"\n✗ Erro ao inserir cliente: {e}")

        finally:
            cursor.close()
            conn.close()

    def listar_clientes(self):
        print("\n" + "=" * 60)
        print("LISTA DE CLIENTES")
        print("=" * 60)

        conn = get_conn()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, nome, cpf, email, ativo, data_cadastro
            FROM clientes
            ORDER BY nome
        """)

        clientes = cursor.fetchall()
        cursor.close()
        conn.close()

        if not clientes:
            print("\nNenhum cliente cadastrado.")
            return

        print(f"\nTotal: {len(clientes)} cliente(s)\n")
        print(f"{'ID':<5} {'Nome':<30} {'CPF':<15} {'Email':<30} {'Status':<10}")
        print("-" * 95)

        for id_, nome, cpf, email, ativo, _ in clientes:
            status = "ATIVO" if ativo else "INATIVO"
            cpf_mask = f"{cpf[:3]}***{cpf[-2:]}"
            print(f"{id_:<5} {nome:<30} {cpf_mask:<15} {email:<30} {status:<10}")

    def visualizar_logs(self):
        print("\n" + "=" * 60)
        print("LOGS DE DOWNLOADS")
        print("=" * 60)

        conn = get_conn()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT l.data_download, c.nome, l.mes_referencia, l.sucesso, l.mensagem
            FROM logs_downloads l
            JOIN clientes c ON l.cliente_id = c.id
            ORDER BY l.data_download DESC
            LIMIT 50
        """)

        logs = cursor.fetchall()
        cursor.close()
        conn.close()

        if not logs:
            print("\nNenhum log encontrado.")
            return

        for data, nome, mes, sucesso, msg in logs:
            status = "✓ SUCESSO" if sucesso else "✗ FALHA"
            print(f"{data} | {nome:<25} | {mes} | {status} | {msg}")

    def desativar_cliente(self):
        self.listar_clientes()

        try:
            cliente_id = int(input("\nID do cliente para desativar (0 para cancelar): "))
            if cliente_id == 0:
                return
        except ValueError:
            print("✗ ID inválido!")
            return

        conn = get_conn()
        cursor = conn.cursor()

        cursor.execute("UPDATE clientes SET ativo = 0 WHERE id = %s", (cliente_id,))
        conn.commit()

        print("✓ Cliente desativado!" if cursor.rowcount else "✗ Cliente não encontrado!")

        cursor.close()
        conn.close()

    def reativar_cliente(self):
        conn = get_conn()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, nome, cpf FROM clientes WHERE ativo = 0 ORDER BY nome
        """)

        clientes = cursor.fetchall()

        if not clientes:
            print("\nNenhum cliente inativo encontrado.")
            conn.close()
            return

        for id_, nome, cpf in clientes:
            print(f"ID: {id_} | {nome} | CPF: {cpf[:3]}***")

        try:
            cliente_id = int(input("\nID do cliente para reativar (0 para cancelar): "))
            if cliente_id == 0:
                return
        except ValueError:
            print("✗ ID inválido!")
            return

        cursor.execute("UPDATE clientes SET ativo = 1 WHERE id = %s", (cliente_id,))
        conn.commit()

        print("✓ Cliente reativado!" if cursor.rowcount else "✗ Cliente não encontrado!")

        cursor.close()
        conn.close()


def menu_principal():
    print("\n" + "=" * 60)
    print("GERENCIADOR DE CLIENTES - VIVO")
    print("=" * 60)
    print("""
1. Adicionar novo cliente
2. Listar clientes
3. Visualizar logs de downloads
4. Desativar cliente
5. Reativar cliente
0. Sair
""")


def main():
    gerenciador = GerenciadorClientes()

    while True:
        menu_principal()
        opcao = input("Escolha uma opção: ").strip()

        if opcao == '1':
            gerenciador.adicionar_cliente()
        elif opcao == '2':
            gerenciador.listar_clientes()
        elif opcao == '3':
            gerenciador.visualizar_logs()
        elif opcao == '4':
            gerenciador.desativar_cliente()
        elif opcao == '5':
            gerenciador.reativar_cliente()
        elif opcao == '0':
            break
        else:
            print("✗ Opção inválida!")

        input("\nPressione ENTER para continuar...")


if __name__ == "__main__":
    main()
