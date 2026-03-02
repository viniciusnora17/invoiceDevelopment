import mysql.connector
from db_config import DB_CONFIG

class DatabaseManager:
    def __init__(self):
        self.db_config = DB_CONFIG

    def get_connection(self):
        return mysql.connector.connect(**self.db_config)

    def obter_clientes_ativos(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, nome, cpf, senha_vivo, email
            FROM clientes
            WHERE ativo = 1
        """)
        
        clientes = cursor.fetchall()
        cursor.close()
        conn.close()
        return clientes

    def registrar_log(self, cliente_id, mes_referencia, sucesso, mensagem):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO logs_downloads
            (cliente_id, mes_referencia, sucesso, mensagem)
            VALUES (%s, %s, %s, %s)
        """, (cliente_id, mes_referencia, sucesso, mensagem))
        
        conn.commit()
        cursor.close()
        conn.close()
