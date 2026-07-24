import pytest
import os
from ..main import DesktopApi
from ..database import init_db, DB_PATH

@pytest.fixture(autouse=True)
def setup_db():
    if os.path.exists(DB_PATH):
        try:
            os.remove(DB_PATH)
        except PermissionError:
            pass
    init_db()
    yield
    if os.path.exists(DB_PATH):
        try:
            os.remove(DB_PATH)
        except PermissionError:
            pass

def test_salvar_nota():
    api = DesktopApi()
    payload = {
        "data_compra": "2026-07-23",
        "local_mercado": "Mercado Teste",
        "produtos": [
            {"nome": "Arroz", "categoria": "Grãos", "quantidade": 2.0, "preco_unitario": 25.50},
            {"nome": "Feijão", "categoria": "Grãos", "quantidade": 1.0, "preco_unitario": 8.00}
        ]
    }
    result = api.salvar_nota(payload)
    assert result["success"] is True
    assert "id" in result

def test_produto_fracionado():
    """Valida produto com gramatura/quantidade fracionada de 3 casas decimais (ex: 0.478 kg)"""
    api = DesktopApi()
    payload = {
        "data_compra": "2026-07-24",
        "local_mercado": "Açougue Central",
        "produtos": [
            {"nome": "Linguiça Toscana", "categoria": "Açougue", "quantidade": 0.478, "preco_unitario": 29.90}
        ]
    }
    result = api.salvar_nota(payload)
    assert result["success"] is True

    produtos = api.obter_produtos_populares()
    assert len(produtos) == 1
    assert produtos[0]["nome"] == "Linguiça Toscana"
    assert pytest.approx(produtos[0]["total_quantidade"], 0.0001) == 0.478
    assert pytest.approx(produtos[0]["total_gasto"], 0.01) == 0.478 * 29.90

def test_gastos_mensais_stats():
    api = DesktopApi()
    payload = {
        "data_compra": "2026-07-23",
        "local_mercado": "Mercado Teste",
        "produtos": [
            {"nome": "Item 1", "categoria": "Categoria A", "quantidade": 1.0, "preco_unitario": 100.0}
        ]
    }
    api.salvar_nota(payload)
    
    gastos = api.obter_gastos_mensais()
    assert len(gastos) > 0
    assert gastos[0]["total_mensal"] == 100.0

def test_produtos_populares_stats():
    api = DesktopApi()
    payload1 = {
        "data_compra": "2026-07-23",
        "local_mercado": "Mercado A",
        "produtos": [{"nome": "Maçã", "categoria": "Fruta", "quantidade": 5.0, "preco_unitario": 2.0}]
    }
    api.salvar_nota(payload1)
    
    payload2 = {
        "data_compra": "2026-07-24",
        "local_mercado": "Mercado B",
        "produtos": [{"nome": "Maçã", "categoria": "Fruta", "quantidade": 3.0, "preco_unitario": 2.0}]
    }
    api.salvar_nota(payload2)
    
    produtos = api.obter_produtos_populares()
    assert len(produtos) > 0
    assert produtos[0]["nome"] == "Maçã"
    assert produtos[0]["total_quantidade"] == 8.0
