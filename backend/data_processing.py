import polars as pl
import sqlite3
import os
import sys
from datetime import datetime
from fpdf import FPDF # Importando a biblioteca que resolve o problema do .exe

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from database import DB_PATH, init_db

def get_total_gasto_por_mes():
    # Garante que o banco e tabelas existam
    init_db()

    conn = sqlite3.connect(DB_PATH)
    query = "SELECT data_compra, valor_total FROM NotasFiscais"
    
    try:
        df = pl.read_database(query=query, connection=conn)
    except Exception:
        df = pl.DataFrame()
    finally:
        conn.close()
    
    if df.is_empty():
        return []

    df = df.with_columns(
        pl.col("valor_total").cast(pl.Float64),
        pl.col("data_compra").str.to_date("%Y-%m-%d")
    ).with_columns(
        pl.col("data_compra").dt.truncate("1mo").alias("mes")
    )
    
    agrupado = df.group_by("mes").agg(
        pl.col("valor_total").sum().alias("total_mensal")
    ).sort("mes")
    
    return agrupado.with_columns(
        pl.col("mes").dt.to_string("%Y-%m")
    ).to_dicts()

def get_produtos_mais_comprados():
    init_db()

    conn = sqlite3.connect(DB_PATH)
    query = "SELECT nome, categoria, quantidade, subtotal FROM Produtos"
    
    try:
        df = pl.read_database(query=query, connection=conn)
    except Exception:
        df = pl.DataFrame()
    finally:
        conn.close()
    
    if df.is_empty():
        return []

    df = df.with_columns([
        pl.col("quantidade").cast(pl.Float64),
        pl.col("subtotal").cast(pl.Float64)
    ])

    agrupado = df.group_by(["nome", "categoria"]).agg(
        pl.col("quantidade").sum().alias("total_quantidade"),
        pl.col("subtotal").sum().alias("total_gasto")
    ).sort("total_quantidade", descending=True)
    
    return agrupado.to_dicts()

def get_historico_precos(nome_filtro: str = ""):
    init_db()

    conn = sqlite3.connect(DB_PATH)
    query = """
    SELECT P.nome, P.categoria, P.preco_unitario, P.quantidade, N.data_compra, N.local_mercado
    FROM Produtos P
    JOIN NotasFiscais N ON P.nota_fiscal_id = N.id
    """
    try:
        df = pl.read_database(query=query, connection=conn)
    except Exception:
        df = pl.DataFrame()
    finally:
        conn.close()

    if df.is_empty():
        return []

    df = df.with_columns([
        pl.col("quantidade").cast(pl.Float64),
        pl.col("preco_unitario").cast(pl.Float64)
    ])

    if nome_filtro:
        df = df.filter(pl.col("nome").str.to_lowercase().str.contains(nome_filtro.lower()))

    return df.sort("data_compra", descending=True).to_dicts()


# ===========================================================================
# FUNÇÕES DE EXPORTAÇÃO (CSV, Parquet, PDF Dark Carbon)
# ===========================================================================

def _get_historico_dataframe() -> pl.DataFrame:
    """
    Retorna o DataFrame Polars completo do JOIN entre NotasFiscais e Produtos.
    Usado internamente pelas funções de exportação para evitar duplicação de query.
    """
    init_db()
    conn = sqlite3.connect(DB_PATH)
    query = """
    SELECT 
        P.nome, 
        P.categoria, 
        P.preco_unitario, 
        P.quantidade, 
        P.subtotal,
        N.data_compra, 
        N.local_mercado,
        N.valor_total AS valor_nota
    FROM Produtos P
    JOIN NotasFiscais N ON P.nota_fiscal_id = N.id
    ORDER BY N.data_compra DESC
    """
    try:
        df = pl.read_database(query=query, connection=conn)
    except Exception:
        df = pl.DataFrame()
    finally:
        conn.close()

    if not df.is_empty():
        df = df.with_columns([
            pl.col("quantidade").cast(pl.Float64),
            pl.col("preco_unitario").cast(pl.Float64),
            pl.col("subtotal").cast(pl.Float64),
            pl.col("valor_nota").cast(pl.Float64),
        ])

    return df


def exportar_dados_brutos(formato: str, caminho_destino: str) -> dict:
    """
    Exporta os dados brutos (JOIN completo) como CSV ou Parquet.
    """
    try:
        df = _get_historico_dataframe()

        if df.is_empty():
            return {"success": False, "error": "Nenhum dado encontrado para exportar."}

        formato_lower = formato.strip().lower()

        if formato_lower == "csv":
            df.write_csv(caminho_destino)
        elif formato_lower == "parquet":
            df.write_parquet(caminho_destino)
        else:
            return {"success": False, "error": f"Formato '{formato}' não suportado. Use 'csv' ou 'parquet'."}

        return {
            "success": True,
            "message": f"Dados exportados com sucesso ({formato_lower.upper()})!",
            "caminho": caminho_destino,
            "registros": len(df),
        }
    except Exception as e:
        return {"success": False, "error": f"Erro na exportação: {str(e)}"}

# ===========================================================================
# NOVA CLASSE FPDF2: PDF DARK CARBON 100% PYTHON (Sem WeasyPrint)
# ===========================================================================
class DarkCarbonPDF(FPDF):
    def header(self):
        # Cor de fundo da página inteira (Dark Carbon #121212)
        self.set_fill_color(18, 18, 18)
        self.rect(0, 0, 210, 297, 'F') # Preenche a página A4 (210x297mm)
        
        # Título do Relatório
        self.set_font('helvetica', 'B', 20)
        self.set_text_color(91, 140, 255) # Primary Blue do app
        self.cell(0, 15, 'compras.io - Relatório Analítico', ln=True, align='L')
        
        self.set_font('helvetica', 'I', 10)
        self.set_text_color(138, 143, 152) # Text Muted
        data_atual = datetime.now().strftime("%d/%m/%Y às %H:%M")
        self.cell(0, 10, f'Gerado em: {data_atual} | 100% Offline', ln=True, align='L')
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font('helvetica', 'I', 8)
        self.set_text_color(138, 143, 152)
        self.cell(0, 10, f'Página {self.page_no()}', 0, 0, 'C')

def gerar_relatorio_pdf(caminho_destino: str) -> dict:
    """
    Gera um relatório visual em PDF com design Dark Carbon desenhado do zero,
    sem dependências de sistema (perfeito para PyInstaller/.exe).
    """
    try:
        # Coletar dados
        df = _get_historico_dataframe()
        top_produtos = get_produtos_mais_comprados()
        
        if df.is_empty():
            return {"success": False, "error": "Nenhum dado para gerar relatório."}

        # Inicializa o PDF
        pdf = DarkCarbonPDF()
        pdf.add_page()
        
        # --- SEÇÃO 1: KPIs ---
        gasto_total_num = df.select(pl.col("subtotal").sum()).item()
        gasto_total_str = f"R$ {gasto_total_num:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        
        pdf.set_font('helvetica', 'B', 14)
        pdf.set_text_color(255, 255, 255) # Branco
        pdf.cell(100, 10, 'Gasto Total Registrado', ln=False)
        pdf.cell(90, 10, 'Produto Mais Comprado', ln=True)
        
        pdf.set_font('helvetica', 'B', 24)
        pdf.set_text_color(0, 255, 136) # Verde Neon
        pdf.cell(100, 15, gasto_total_str, ln=False)
        
        if top_produtos:
            produto_top = top_produtos[0]
            nome_top = produto_top['nome'].upper()
            qtd_top = produto_top['total_quantidade']
            pdf.cell(90, 15, f"{nome_top} ({qtd_top} un)", ln=True)
        else:
            pdf.cell(90, 15, "-", ln=True)
            
        pdf.ln(15)

        # --- SEÇÃO 2: TABELA DE HISTÓRICO ---
        pdf.set_font('helvetica', 'B', 12)
        pdf.set_text_color(91, 140, 255) # Primary Blue
        pdf.cell(0, 10, 'Últimas Compras (Histórico)', ln=True)
        
        # Cabeçalho da Tabela
        colunas = [("Data", 30), ("Produto", 60), ("Mercado", 50), ("Qtd", 20), ("Preço Un.", 30)]
        pdf.set_font('helvetica', 'B', 10)
        pdf.set_fill_color(30, 30, 35) # Cinza um pouco mais claro para o cabeçalho
        pdf.set_text_color(255, 255, 255)
        
        for nome_col, largura in colunas:
            pdf.cell(largura, 10, nome_col, border=1, align='C', fill=True)
        pdf.ln()

        # Linhas da Tabela
        pdf.set_font('helvetica', '', 9)
        pdf.set_text_color(200, 200, 200) # Cinza claro para o texto
        
        # Pega as 30 últimas compras para não lotar o PDF
        historico = df.head(30).to_dicts() 
        
        for linha in historico:
            # Alterna a cor do fundo sutilmente
            if pdf.get_y() > 270: # Adiciona nova página se chegar no fim
                pdf.add_page()
            
            pdf.cell(30, 8, linha.get('data_compra', ''), border=1, align='C')
            pdf.cell(60, 8, str(linha.get('nome', ''))[:25], border=1, align='L') # Corta nomes longos
            pdf.cell(50, 8, str(linha.get('local_mercado', ''))[:20], border=1, align='C')
            pdf.cell(20, 8, f"{linha.get('quantidade', 0):.3f}".rstrip('0').rstrip('.'), border=1, align='C')
            
            preco = f"R$ {linha.get('preco_unitario', 0):.2f}".replace('.', ',')
            pdf.set_text_color(0, 255, 136) # Preço em verde
            pdf.cell(30, 8, preco, border=1, align='C')
            pdf.set_text_color(200, 200, 200) # Volta pra cinza
            pdf.ln()

        pdf.output(caminho_destino)

        return {
            "success": True,
            "message": "Relatório PDF Dark Carbon gerado com sucesso!",
            "caminho": caminho_destino,
            "registros": len(historico),
        }
    except ImportError:
        return {
            "success": False,
            "error": "Dependência ausente. Execute no terminal: pip install fpdf2",
        }
    except Exception as e:
        return {"success": False, "error": f"Erro ao gerar PDF: {str(e)}"}