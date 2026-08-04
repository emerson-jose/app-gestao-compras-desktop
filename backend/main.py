import os
import sys

# Ajuste de PYTHONPATH dinâmico para suporte a imports e PyInstaller (.exe)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import webview
from database import init_db, get_connection, DB_PATH
from data_processing import (
    get_total_gasto_por_mes, 
    get_produtos_mais_comprados, 
    get_historico_precos,
    exportar_dados_brutos,
    gerar_relatorio_pdf,
)
from models import NotaFiscalCreate

def get_frontend_path():
    """
    Retorna o caminho absoluto de frontend/index.html.
    Funciona em desenvolvimento e quando empacotado (.exe com PyInstaller via sys._MEIPASS).
    """
    if hasattr(sys, '_MEIPASS'):
        base_dir = sys._MEIPASS
    else:
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    
    return os.path.join(base_dir, "frontend", "index.html")

class DesktopApi:
    """
    Funções registradas e expostas para a interface JS (window.pywebview.api)
    """
    def __init__(self):
        # Obriga a verificação e criação das tabelas no SQLite ANTES de expor a API
        init_db()

    def salvar_nota(self, payload: dict):
        try:
            # Garante tabelas existentes
            init_db()

            nota = NotaFiscalCreate(**payload)
            conn = get_connection()
            cursor = conn.cursor()
            
            valor_total = sum(p.quantidade * p.preco_unitario for p in nota.produtos)
            
            # Inserção explícita na tabela 'NotasFiscais'
            cursor.execute(
                "INSERT INTO NotasFiscais (data_compra, local_mercado, valor_total) VALUES (?, ?, ?)",
                (nota.data_compra, nota.local_mercado, valor_total)
            )
            nota_id = cursor.lastrowid
            
            # Inserção explícita na tabela 'Produtos'
            for p in nota.produtos:
                subtotal = p.quantidade * p.preco_unitario
                cursor.execute(
                    """INSERT INTO Produtos 
                    (nota_fiscal_id, nome, categoria, quantidade, preco_unitario, subtotal) 
                    VALUES (?, ?, ?, ?, ?, ?)""",
                    (nota_id, p.nome, p.categoria, p.quantidade, p.preco_unitario, subtotal)
                )
            
            conn.commit()
            conn.close()
            return {"success": True, "message": "Nota Fiscal registrada com sucesso!", "id": nota_id}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def obter_gastos_mensais(self):
        return get_total_gasto_por_mes()

    def obter_produtos_populares(self):
        return get_produtos_mais_comprados()

    def obter_historico_precos(self, nome_filtro=""):
        return get_historico_precos(nome_filtro)

    def solicitar_exportacao_dados(self, formato="csv"):
        """
        Abre um File Dialog nativo "Salvar Como..." e exporta os dados brutos.
        Suporta CSV e Parquet.
        """
        try:
            formato_lower = formato.strip().lower()

            if formato_lower == "csv":
                file_types = ('Arquivo CSV (*.csv)',)
                default_name = 'compras_historico.csv'
            elif formato_lower == "parquet":
                file_types = ('Arquivo Parquet (*.parquet)',)
                default_name = 'compras_historico.parquet'
            else:
                return {"success": False, "error": f"Formato '{formato}' não suportado."}

            # File Dialog nativo via PyWebView
            result = webview.windows[0].create_file_dialog(
                webview.SAVE_DIALOG,
                save_filename=default_name,
                file_types=file_types,
            )

            if not result:
                return {"success": False, "error": "Exportação cancelada pelo usuário."}

            caminho = result if isinstance(result, str) else result[0]
            return exportar_dados_brutos(formato_lower, caminho)

        except Exception as e:
            return {"success": False, "error": f"Erro ao abrir diálogo: {str(e)}"}

    def solicitar_relatorio_pdf(self):
        """
        Abre um File Dialog nativo "Salvar Como..." e gera o relatório PDF Dark Carbon.
        """
        try:
            result = webview.windows[0].create_file_dialog(
                webview.SAVE_DIALOG,
                save_filename='relatorio_compras.pdf',
                file_types=('Documento PDF (*.pdf)',),
            )

            if not result:
                return {"success": False, "error": "Geração cancelada pelo usuário."}

            caminho = result if isinstance(result, str) else result[0]
            return gerar_relatorio_pdf(caminho)

        except Exception as e:
            return {"success": False, "error": f"Erro ao gerar relatório: {str(e)}"}

    def atualizar_registro(self, produto_id, nota_id, nova_data, novo_nome, nova_qtd, novo_preco):
        """
        Atualiza um registro existente (Produto + NotaFiscal) no SQLite.
        Recalcula subtotal do produto e valor_total da nota fiscal.
        """
        try:
            conn = get_connection()
            cursor = conn.cursor()

            # 1. Atualizar data_compra na NotaFiscal
            cursor.execute(
                "UPDATE NotasFiscais SET data_compra = ? WHERE id = ?",
                (nova_data, nota_id)
            )

            # 2. Atualizar produto (nome, quantidade, preco_unitario, subtotal recalculado)
            novo_subtotal = nova_qtd * novo_preco
            cursor.execute(
                "UPDATE Produtos SET nome = ?, quantidade = ?, preco_unitario = ?, subtotal = ? WHERE id = ?",
                (novo_nome, nova_qtd, novo_preco, novo_subtotal, produto_id)
            )

            # 3. Recalcular valor_total da nota fiscal (soma de todos os subtotais)
            cursor.execute(
                "SELECT SUM(subtotal) FROM Produtos WHERE nota_fiscal_id = ?",
                (nota_id,)
            )
            novo_total = cursor.fetchone()[0] or 0
            cursor.execute(
                "UPDATE NotasFiscais SET valor_total = ? WHERE id = ?",
                (novo_total, nota_id)
            )

            conn.commit()
            conn.close()
            return {"success": True, "message": "Registro atualizado com sucesso!"}
        except Exception as e:
            return {"success": False, "error": str(e)}

if __name__ == "__main__":
    # 1. Garantia estrita de que as tabelas SQLite existem ANTES de abrir a janela PyWebView
    init_db()
    
    api = DesktopApi()
    html_file = get_frontend_path()
    
    # Gestão Desktop de Compras & Estoque 2. Inicia janela desktop nativa
    window = webview.create_window(
        title=" ",
        url=html_file,
        js_api=api,
        width=1200,
        height=800,
        min_size=(900, 600),
        background_color="#0a0a0c"
    )
    webview.start(debug=False)
