from pydantic import BaseModel
from typing import List, Optional

class ProdutoCreate(BaseModel):
    nome: str
    categoria: str
    quantidade: float
    preco_unitario: float
    subtotal: Optional[float] = None

class NotaFiscalCreate(BaseModel):
    data_compra: str
    local_mercado: str
    produtos: List[ProdutoCreate]
    valor_total: Optional[float] = None

class ProdutoResponse(BaseModel):
    id: int
    nota_fiscal_id: int
    nome: str
    categoria: str
    quantidade: float
    preco_unitario: float
    subtotal: float

class NotaFiscalResponse(BaseModel):
    id: int
    data_compra: str
    local_mercado: str
    valor_total: float
