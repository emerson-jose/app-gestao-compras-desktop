import sqlite3
import os

# Caminho para o seu banco de dados
DB_PATH = os.path.abspath("compras.db")

def corrigir_data_em_lote(data_errada, data_certa):
    print(f"Conectando ao banco em: {DB_PATH}")
    
    try:
        # 1. Conecta ao banco de dados
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # 2. Executa o comando SQL de UPDATE
        cursor.execute(
            "UPDATE NotasFiscais SET data_compra = ? WHERE data_compra = ?",
            (data_certa, data_errada)
        )
        
        # 3. Verifica quantas linhas foram alteradas
        linhas_afetadas = cursor.rowcount
        
        # 4. Salva (commit) as alterações
        conn.commit()
        
        print("-" * 40)
        if linhas_afetadas > 0:
            print(f"✅ SUCESSO! {linhas_afetadas} nota(s) fiscal(is) atualizada(s)!")
            print(f"Todos os produtos dessa(s) nota(s) agora estão com a data: {data_certa}")
        else:
            print(f"⚠️ Nenhuma nota fiscal encontrada com a data '{data_errada}'.")
            print("Verifique se você digitou a data errada exatamente como aparece no sistema.")
        print("-" * 40)
        
    except sqlite3.Error as e:
        print(f"❌ Erro no banco de dados: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    # ==========================================
    # ALTERE AS DATAS AQUI ANTES DE RODAR
    # Use o formato "YYYY-MM-DD" (Ano-Mês-Dia)
    # ==========================================
    
    DATA_INCORRETA = "2026-05-29" # Coloque aqui a data que você cadastrou por engano
    DATA_CORRETA = "2026-07-20"   # Coloque aqui a data certa que você quer que fique
    
    corrigir_data_em_lote(DATA_INCORRETA, DATA_CORRETA)