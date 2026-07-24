import sqlite3
import os
import sys

def get_db_path():
    """
    Retorna o caminho ABSOLUTO e FIXO do banco de dados SQLite compras.db.
    Garante que o banco seja criado no mesmo local independentemente do diretório de onde o app foi iniciado.
    """
    if hasattr(sys, '_MEIPASS'):
        # Quando empacotado pelo PyInstaller (.exe), salva no diretório do executável
        base_dir = os.path.dirname(sys.executable)
    else:
        # Em desenvolvimento, obtém o caminho da raiz do projeto a partir da localização de database.py
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    
    return os.path.abspath(os.path.join(base_dir, "compras.db"))

DB_PATH = get_db_path()

def init_db():
    """
    Cria as tabelas 'NotasFiscais' e 'Produtos' caso ainda não existam no SQLite.
    Garante resiliência e previne erros 'no such table'.
    """
    # Garante que a pasta pai exista
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Tabela NotasFiscais (Nome exato com PascalCase)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS NotasFiscais (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        data_compra TEXT NOT NULL,
        local_mercado TEXT NOT NULL,
        valor_total REAL NOT NULL
    )
    """)
    
    # Tabela Produtos (Nome exato com PascalCase)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Produtos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nota_fiscal_id INTEGER NOT NULL,
        nome TEXT NOT NULL,
        categoria TEXT NOT NULL,
        quantidade REAL NOT NULL,
        preco_unitario REAL NOT NULL,
        subtotal REAL NOT NULL,
        FOREIGN KEY (nota_fiscal_id) REFERENCES NotasFiscais (id)
    )
    """)
    
    conn.commit()
    conn.close()

def get_connection():
    """
    Retorna uma conexão ativa com o SQLite, garantindo que o banco e tabelas existam.
    """
    init_db()
    return sqlite3.connect(DB_PATH)

# Garante auto-inicialização na importação do módulo
init_db()

if __name__ == "__main__":
    init_db()
    print(f"Banco de dados verificado e inicializado com sucesso em: {DB_PATH}")
