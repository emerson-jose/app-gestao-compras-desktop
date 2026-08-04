// =========================================================
// Compras.io - Client App.js (PyWebView Desktop Bridge)
// =========================================================

document.addEventListener('DOMContentLoaded', () => {
    // Definir data padrão no formulário como hoje
    const dateInput = document.getElementById('data_compra');
    if (dateInput) {
        dateInput.value = new Date().toISOString().split('T')[0];
    }
    
    // Adicionar primeira linha de produto por padrão
    addProdutoRow();
});

// Aguarda a API PyWebView estar pronta
window.addEventListener('pywebviewready', () => {
    console.log("PyWebView API inicializada com sucesso.");
    carregarDashboard();
    carregarHistorico();
});

// Fallback para quando aberto diretamente
setTimeout(() => {
    if (window.pywebview && window.pywebview.api) {
        carregarDashboard();
    }
}, 500);

// NAVEGAÇÃO SPA
function showSection(sectionId) {
    const sections = ['dashboard', 'add', 'historico'];
    sections.forEach(id => {
        const el = document.getElementById(id);
        const tab = document.getElementById(`tab-${id}`);
        if (el) {
            if (id === sectionId) {
                el.classList.remove('hidden');
                tab.classList.add('bg-primaryBlue/20', 'border-primaryBlue/30', 'text-white');
                tab.classList.remove('text-textMuted');
            } else {
                el.classList.add('hidden');
                tab.classList.remove('bg-primaryBlue/20', 'border-primaryBlue/30', 'text-white');
                tab.classList.add('text-textMuted');
            }
        }
    });

    if (sectionId === 'dashboard') carregarDashboard();
    if (sectionId === 'historico') carregarHistorico();
}

// HELPER PARA PARSE SEGURO DE NÚMEROS DECIMAIS (SUPORTA VÍRGULA E PONTO)
function parseNumber(value) {
    if (value === null || value === undefined || value === '') return 0;
    const cleanStr = String(value).trim().replace(',', '.');
    const num = parseFloat(cleanStr);
    return isNaN(num) ? 0 : num;
}

// FEATURE 1: Variáveis globais para interação com o gráfico de meses
let dashDadosPadrao = { mes: "", valor: 0 };
let mesSelecionado = null;

function toggleMesDash(elementoBarra, mes, valor) {
    const totalMesEl = document.getElementById('stat-total-mes');
    const labelEl = document.getElementById('label-total-mes');
    if (!totalMesEl || !labelEl) return;

    // Remove destaques de todas as barras
    document.querySelectorAll('.barra-grafico').forEach(b => {
        b.classList.remove('brightness-150', 'ring-2', 'ring-accentGreen');
    });

    if (mesSelecionado === mes) {
        // Restaurar valores originais (último mês)
        mesSelecionado = null;
        totalMesEl.innerText = `R$ ${dashDadosPadrao.valor.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}`;
        labelEl.innerText = '// Total Mês Atual';
    } else {
        // Atualizar com o mês selecionado
        mesSelecionado = mes;
        totalMesEl.innerText = `R$ ${valor.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}`;
        labelEl.innerText = `// Total de ${mes}`;
        elementoBarra.classList.add('brightness-150', 'ring-2', 'ring-accentGreen');
    }
}

// ADICIONAR LINHA DE PRODUTO NO FORMULÁRIO
function addProdutoRow() {
    const container = document.getElementById('produtos-container');
    if (!container) return;

    const row = document.createElement('div');
    row.className = 'produto-item grid grid-cols-12 gap-2 items-center animate-fade-in';
    row.innerHTML = `
        <input type="text" placeholder="Nome (ex: Linguiça)" class="col-span-4 glass-input rounded-xl px-3 py-2 text-sm prod-nome" oninput="calcularTotalNotaPreview()" required>
        <input type="text" placeholder="Categoria (ex: Açougue)" class="col-span-3 glass-input rounded-xl px-3 py-2 text-sm prod-cat" required>
        <input type="number" step="any" min="0" placeholder="Qtd (ex: 0.478)" class="col-span-2 glass-input rounded-xl px-3 py-2 text-sm prod-qtd" oninput="calcularTotalNotaPreview()" required>
        <input type="number" step="any" min="0" placeholder="Preço (R$)" class="col-span-2 glass-input rounded-xl px-3 py-2 text-sm prod-preco" oninput="calcularTotalNotaPreview()" required>
        <button type="button" onclick="this.parentElement.remove(); calcularTotalNotaPreview();" class="col-span-1 text-red-400 hover:text-red-300 font-bold text-center">✕</button>
    `;
    container.appendChild(row);
}

// CALCULAR PRÉVIA DO TOTAL DA NOTA
function calcularTotalNotaPreview() {
    let total = 0;
    document.querySelectorAll('.produto-item').forEach(row => {
        const qtd = parseNumber(row.querySelector('.prod-qtd').value);
        const preco = parseNumber(row.querySelector('.prod-preco').value);
        total += qtd * preco;
    });

    const previewEl = document.getElementById('total-nota-preview');
    if (previewEl) {
        previewEl.innerText = `R$ ${total.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 3 })}`;
    }
}

// SALVAR NOTA FISCAL VIA PYWEBVIEW
async function handleSalvarNota(event) {
    event.preventDefault();
    if (!window.pywebview || !window.pywebview.api) {
        alert("Aguarde a inicialização do aplicativo desktop.");
        return;
    }

    const data_compra = document.getElementById('data_compra').value;
    const local_mercado = document.getElementById('local_mercado').value;
    
    const produtos = [];
    document.querySelectorAll('.produto-item').forEach(row => {
        const nome = row.querySelector('.prod-nome').value.trim();
        const categoria = row.querySelector('.prod-cat').value.trim();
        const quantidade = parseNumber(row.querySelector('.prod-qtd').value);
        const preco_unitario = parseNumber(row.querySelector('.prod-preco').value);

        if (nome && quantidade > 0 && preco_unitario > 0) {
            produtos.push({ nome, categoria, quantidade, preco_unitario });
        }
    });

    if (produtos.length === 0) {
        alert("Adicione pelo menos um produto válido com quantidade e preço.");
        return;
    }

    const payload = { data_compra, local_mercado, produtos };

    const btnSalvar = document.getElementById('btn-salvar');
    btnSalvar.disabled = true;
    btnSalvar.innerText = "SALVANDO...";

    try {
        const res = await window.pywebview.api.salvar_nota(payload);
        if (res.success) {
            alert("Nota fiscal salva com sucesso!");
            // Limpar formulário
            document.getElementById('local_mercado').value = "";
            document.getElementById('produtos-container').innerHTML = "";
            addProdutoRow();
            calcularTotalNotaPreview();
            showSection('dashboard');
        } else {
            alert(`Erro ao salvar: ${res.error}`);
        }
    } catch (err) {
        console.error(err);
        alert("Erro de comunicação com o backend Python.");
    } finally {
        btnSalvar.disabled = false;
        btnSalvar.innerText = "SALVAR NOTA FISCAL";
    }
}

// CARREGAR DASHBOARD (AGREGAÇÕES POLARS)
async function carregarDashboard() {
    if (!window.pywebview || !window.pywebview.api) return;

    try {
        const [gastos, produtos] = await Promise.all([
            window.pywebview.api.obter_gastos_mensais(),
            window.pywebview.api.obter_produtos_populares()
        ]);

        renderGastosMensais(gastos);
        renderProdutosPopulares(produtos);
    } catch (e) {
        console.error("Erro ao carregar dashboard:", e);
    }
}

function renderGastosMensais(data) {
    const container = document.getElementById('chart-gastos');
    const totalMesEl = document.getElementById('stat-total-mes');
    const labelEl = document.getElementById('label-total-mes');
    if (!container) return;

    // Reset seleção ao recarregar
    mesSelecionado = null;

    if (!data || data.length === 0) {
        container.innerHTML = `<p class="text-sm text-textMuted m-auto py-8">Nenhum gasto registrado ainda.</p>`;
        if (totalMesEl) totalMesEl.innerText = "R$ 0,00";
        dashDadosPadrao = { mes: "", valor: 0 };
        return;
    }

    const maxValor = Math.max(...data.map(d => d.total_mensal));
    const ultimoMes = data[data.length - 1];

    // Salvar dados padrão do último mês
    dashDadosPadrao = { mes: ultimoMes.mes, valor: ultimoMes.total_mensal };

    if (totalMesEl) {
        totalMesEl.innerText = `R$ ${ultimoMes.total_mensal.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}`;
    }
    if (labelEl) {
        labelEl.innerText = '// Total Mês Atual';
    }

    container.innerHTML = data.map(item => {
        const alturaPercent = maxValor > 0 ? (item.total_mensal / maxValor) * 100 : 10;
        return `
            <div class="flex-1 flex flex-col items-center group">
                <div class="text-[10px] font-mono text-accentGreen opacity-0 group-hover:opacity-100 transition-all mb-1">
                    R$ ${item.total_mensal.toFixed(0)}
                </div>
                <div class="barra-grafico cursor-pointer w-full bg-gradient-to-t from-primaryBlue to-accentGreen rounded-t-lg transition-all duration-500 hover:brightness-125" 
                     style="height: ${Math.max(alturaPercent, 15)}px;"
                     onclick="toggleMesDash(this, '${item.mes}', ${item.total_mensal})"></div>
                <span class="text-[10px] font-mono text-textMuted mt-2">${item.mes}</span>
            </div>
        `;
    }).join('');
}

function renderProdutosPopulares(data) {
    const listEl = document.getElementById('list-produtos');
    const topProdutoEl = document.getElementById('stat-top-produto');
    const topQtdEl = document.getElementById('stat-top-qtd');
    if (!listEl) return;

    if (!data || data.length === 0) {
        listEl.innerHTML = `<p class="text-sm text-textMuted py-4">Nenhum produto cadastrado.</p>`;
        if (topProdutoEl) topProdutoEl.innerText = "-";
        if (topQtdEl) topQtdEl.innerText = "0 unidades";
        return;
    }

    if (topProdutoEl) topProdutoEl.innerText = data[0].nome;
    if (topQtdEl) topQtdEl.innerText = `${data[0].total_quantidade} unidades acumuladas`;

    listEl.innerHTML = data.slice(0, 5).map(item => `
        <div class="flex items-center justify-between p-3 rounded-xl bg-black/30 border border-cardBorder hover:border-primaryBlue/40 transition-all">
            <div>
                <div class="font-mono text-sm font-semibold text-white">${item.nome}</div>
                <div class="text-xs text-textMuted">${item.categoria}</div>
            </div>
            <div class="text-right">
                <div class="font-mono text-sm text-accentGreen font-bold">${item.total_quantidade} un</div>
                <div class="text-xs text-textMuted">R$ ${item.total_gasto.toFixed(2)}</div>
            </div>
        </div>
    `).join('');
}

// CARREGAR HISTÓRICO DE PREÇOS (busca completa uma única vez)
let dadosHistoricoGlobal = [];

async function carregarHistorico() {
    if (!window.pywebview || !window.pywebview.api) return;
    try {
        dadosHistoricoGlobal = await window.pywebview.api.obter_historico_precos("");
        popularDropdownsFiltros(dadosHistoricoGlobal);
        renderTabelaHistorico(dadosHistoricoGlobal);
    } catch (e) {
        console.error("Erro ao carregar histórico:", e);
    }
}

function popularDropdownsFiltros(data) {
    const selectCategoria = document.getElementById('filter-categoria');
    const selectMercado = document.getElementById('filter-mercado');
    if (!selectCategoria || !selectMercado) return;

    const categorias = [...new Set(data.map(item => item.categoria))].sort();
    const mercados = [...new Set(data.map(item => item.local_mercado))].sort();

    // Preservar seleção atual antes de reconstruir
    const catAtual = selectCategoria.value;
    const mercAtual = selectMercado.value;

    selectCategoria.innerHTML = '<option value="">Todas Categorias</option>' +
        categorias.map(c => `<option value="${c}">${c}</option>`).join('');

    selectMercado.innerHTML = '<option value="">Todos Mercados</option>' +
        mercados.map(m => `<option value="${m}">${m}</option>`).join('');

    // Restaurar seleção se ainda existir
    selectCategoria.value = catAtual;
    selectMercado.value = mercAtual;
}

function filtrarHistorico() {
    const search = (document.getElementById('search-produto')?.value || "").toLowerCase();
    const categoria = document.getElementById('filter-categoria')?.value || "";
    const mercado = document.getElementById('filter-mercado')?.value || "";

    const dadosFiltrados = dadosHistoricoGlobal.filter(row => {
        const matchNome = row.nome.toLowerCase().includes(search);
        const matchCategoria = categoria === "" || row.categoria === categoria;
        const matchMercado = mercado === "" || row.local_mercado === mercado;
        return matchNome && matchCategoria && matchMercado;
    });

    renderTabelaHistorico(dadosFiltrados);
}

function renderTabelaHistorico(data) {
    const tbody = document.getElementById('table-historico-body');
    if (!tbody) return;

    if (!data || data.length === 0) {
        tbody.innerHTML = `<tr><td colspan="7" class="py-6 text-center text-textMuted">Nenhum registro encontrado.</td></tr>`;
        return;
    }

    tbody.innerHTML = data.map(row => {
        // Escapar aspas simples no nome para evitar erro no onclick
        const nomeEscapado = row.nome.replace(/'/g, "\\'");
        return `
        <tr class="hover:bg-white/5 transition-colors font-mono">
            <td class="py-3 px-4 text-textMuted">${row.data_compra}</td>
            <td class="py-3 px-4 font-semibold text-white">${row.nome}</td>
            <td class="py-3 px-4 text-textMuted">${row.categoria}</td>
            <td class="py-3 px-4 text-primaryBlue">${row.local_mercado}</td>
            <td class="py-3 px-4 text-white">${row.quantidade}</td>
            <td class="py-3 px-4 text-accentGreen font-bold">R$ ${row.preco_unitario.toFixed(2)}</td>
            <td class="py-3 px-4 text-center">
                <button onclick="editarRegistroHTML(${row.produto_id}, ${row.nota_id}, '${row.data_compra}', '${nomeEscapado}', ${row.quantidade}, ${row.preco_unitario})" 
                        class="text-base hover:scale-125 transition-transform" title="Editar registro">✏️</button>
            </td>
        </tr>
    `;
    }).join('');
}

// FEATURE 2: Edição de registro via prompt() nativo
async function editarRegistroHTML(produto_id, nota_id, dataAtual, nomeAtual, qtdAtual, precoAtual) {
    const novaData = prompt('Data da compra (AAAA-MM-DD):', dataAtual);
    if (novaData === null) return;

    const novoNome = prompt('Nome do produto:', nomeAtual);
    if (novoNome === null) return;

    const novaQtdStr = prompt('Quantidade:', String(qtdAtual));
    if (novaQtdStr === null) return;
    const novaQtd = parseNumber(novaQtdStr);

    const novoPrecoStr = prompt('Preço unitário (R$):', String(precoAtual));
    if (novoPrecoStr === null) return;
    const novoPreco = parseNumber(novoPrecoStr);

    if (!novaData || !novoNome || novaQtd <= 0 || novoPreco <= 0) {
        showToast('Preencha todos os campos com valores válidos.', 'error');
        return;
    }

    try {
        const res = await window.pywebview.api.atualizar_registro(produto_id, nota_id, novaData, novoNome, novaQtd, novoPreco);
        if (res.success) {
            showToast(res.message || 'Registro atualizado!', 'success');
            carregarHistorico();
            carregarDashboard();
        } else {
            showToast(res.error || 'Erro ao atualizar registro.', 'error');
        }
    } catch (err) {
        console.error('Erro ao atualizar registro:', err);
        showToast('Erro de comunicação com o backend Python.', 'error');
    }
}


// =========================================================
// TOAST NOTIFICATION SYSTEM
// =========================================================

function showToast(message, type = 'success', durationMs = 4000) {
    const container = document.getElementById('toast-container');
    if (!container) return;

    const toast = document.createElement('div');
    toast.className = `toast-notification toast-${type} pointer-events-auto`;
    
    const icon = type === 'success' ? '✅' : type === 'error' ? '❌' : 'ℹ️';
    
    toast.innerHTML = `
        <span class="toast-icon">${icon}</span>
        <span class="toast-message">${message}</span>
        <button onclick="this.parentElement.remove()" class="toast-close">✕</button>
    `;

    container.appendChild(toast);

    // Auto-remove após duração
    setTimeout(() => {
        toast.classList.add('toast-exit');
        setTimeout(() => toast.remove(), 300);
    }, durationMs);
}


// =========================================================
// EXPORTAÇÃO — DROPDOWN & HANDLERS
// =========================================================

function toggleExportDropdown() {
    const dropdown = document.getElementById('export-dropdown');
    if (dropdown) {
        dropdown.classList.toggle('hidden');
    }
}

// Fechar dropdown ao clicar fora
document.addEventListener('click', (e) => {
    const wrapper = document.getElementById('export-dropdown-wrapper');
    const dropdown = document.getElementById('export-dropdown');
    if (wrapper && dropdown && !wrapper.contains(e.target)) {
        dropdown.classList.add('hidden');
    }
});


async function handleExportarDados(formato) {
    // Fecha dropdown
    const dropdown = document.getElementById('export-dropdown');
    if (dropdown) dropdown.classList.add('hidden');

    if (!window.pywebview || !window.pywebview.api) {
        showToast('Aguarde a inicialização do aplicativo desktop.', 'error');
        return;
    }

    const btn = document.getElementById('btn-exportar-dados');
    const originalContent = btn.innerHTML;
    
    // Estado loading
    btn.disabled = true;
    btn.innerHTML = `
        <span class="export-spinner"></span>
        <span>Exportando...</span>
    `;

    try {
        const res = await window.pywebview.api.solicitar_exportacao_dados(formato);
        
        if (res.success) {
            showToast(`${res.message} (${res.registros} registros)`, 'success');
        } else {
            showToast(res.error, 'error');
        }
    } catch (err) {
        console.error('Erro exportação:', err);
        showToast('Erro de comunicação com o backend Python.', 'error');
    } finally {
        btn.disabled = false;
        btn.innerHTML = originalContent;
    }
}


async function handleGerarPDF() {
    if (!window.pywebview || !window.pywebview.api) {
        showToast('Aguarde a inicialização do aplicativo desktop.', 'error');
        return;
    }

    const btn = document.getElementById('btn-relatorio-pdf');
    const originalContent = btn.innerHTML;

    // Estado loading
    btn.disabled = true;
    btn.innerHTML = `
        <span class="export-spinner"></span>
        <span>Gerando...</span>
    `;

    try {
        const res = await window.pywebview.api.solicitar_relatorio_pdf();

        if (res.success) {
            showToast(`${res.message} (${res.registros} registros)`, 'success');
        } else {
            showToast(res.error, 'error');
        }
    } catch (err) {
        console.error('Erro PDF:', err);
        showToast('Erro de comunicação com o backend Python.', 'error');
    } finally {
        btn.disabled = false;
        btn.innerHTML = originalContent;
    }
}
