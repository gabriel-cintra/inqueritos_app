// ========================================
// MAIN.JS - Sistema Jurídico MP
// ========================================

// Confirmação de exclusão
function confirmarExclusao(tipo, numero) {
    return confirm(`Tem certeza que deseja excluir ${tipo} ${numero}?\n\nEsta ação não pode ser desfeita.`);
}

// Confirmação de conclusão/finalização
function confirmarAcao(acao, numero) {
    return confirm(`Confirmar ${acao} de ${numero}?`);
}

// Marcar/desmarcar todos os checkboxes
function toggleAllCheckboxes() {
    const masterCheckbox = document.getElementById('checkAll');
    const checkboxes = document.querySelectorAll('.item-checkbox');
    
    checkboxes.forEach(checkbox => {
        checkbox.checked = masterCheckbox.checked;
    });
    
    updateActionButtons();
}

// Atualizar botões de ação em massa
function updateActionButtons() {
    const checkboxes = document.querySelectorAll('.item-checkbox:checked');
    const actionButtons = document.querySelectorAll('.bulk-action-btn');
    
    if (checkboxes.length > 0) {
        actionButtons.forEach(btn => {
            btn.disabled = false;
            btn.textContent = btn.dataset.text.replace('{count}', checkboxes.length);
        });
    } else {
        actionButtons.forEach(btn => {
            btn.disabled = true;
            btn.textContent = btn.dataset.defaultText;
        });
    }
}

// Processar ação em massa
function processarAcaoMassa(acao) {
    const checkboxes = document.querySelectorAll('.item-checkbox:checked');
    const ids = Array.from(checkboxes).map(cb => cb.value);
    
    if (ids.length === 0) {
        alert('Nenhum item selecionado!');
        return false;
    }
    
    if (!confirm(`Confirmar ${acao} de ${ids.length} item(ns)?`)) {
        return false;
    }
    
    // Aqui seria feita a requisição ao backend
    console.log(`Ação: ${acao}, IDs: ${ids}`);
    alert(`${acao} de ${ids.length} item(ns) realizado com sucesso! (Simulação)`);
    return true;
}

// Filtrar tabela por busca
function filtrarTabela(inputId, tableId) {
    const input = document.getElementById(inputId);
    const filter = input.value.toUpperCase();
    const table = document.getElementById(tableId);
    const rows = table.getElementsByTagName('tr');
    
    for (let i = 1; i < rows.length; i++) {
        const row = rows[i];
        const text = row.textContent || row.innerText;
        
        if (text.toUpperCase().indexOf(filter) > -1) {
            row.style.display = '';
        } else {
            row.style.display = 'none';
        }
    }
}

// Toast de notificação
function showToast(message, type = 'success') {
    const toastContainer = document.getElementById('toastContainer');
    
    if (!toastContainer) {
        console.error('Toast container não encontrado');
        return;
    }
    
    const toastId = 'toast-' + Date.now();
    const bgClass = type === 'success' ? 'bg-success' : 
                    type === 'danger' ? 'bg-danger' : 
                    type === 'warning' ? 'bg-warning' : 'bg-info';
    
    const toastHTML = `
        <div id="${toastId}" class="toast align-items-center text-white ${bgClass} border-0" role="alert">
            <div class="d-flex">
                <div class="toast-body">
                    ${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
            </div>
        </div>
    `;
    
    toastContainer.insertAdjacentHTML('beforeend', toastHTML);
    
    const toastElement = document.getElementById(toastId);
    const toast = new bootstrap.Toast(toastElement, { delay: 3000 });
    toast.show();
    
    toastElement.addEventListener('hidden.bs.toast', () => {
        toastElement.remove();
    });
}

// Inicialização ao carregar a página
document.addEventListener('DOMContentLoaded', function() {
    
    // Adicionar event listeners aos checkboxes individuais
    const itemCheckboxes = document.querySelectorAll('.item-checkbox');
    itemCheckboxes.forEach(checkbox => {
        checkbox.addEventListener('change', updateActionButtons);
    });
    
    // Adicionar event listener ao checkbox mestre
    const masterCheckbox = document.getElementById('checkAll');
    if (masterCheckbox) {
        masterCheckbox.addEventListener('change', toggleAllCheckboxes);
    }
    
    // Inicializar tooltips do Bootstrap
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Auto-hide alerts após 5 segundos
    const alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
    alerts.forEach(alert => {
        setTimeout(() => {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 5000);
    });
    
    console.log('Sistema Jurídico MP - Protótipo carregado');
});

// Função para imprimir
function imprimirPagina() {
    window.print();
}

// Exportar para Excel (simulação)
function exportarExcel(nomeArquivo) {
    alert(`Exportação para Excel: ${nomeArquivo}.xlsx\n\n(Esta é uma simulação - será implementada no backend)`);
}

// Exportar para PDF (simulação)
function exportarPDF(nomeArquivo) {
    alert(`Exportação para PDF: ${nomeArquivo}.pdf\n\n(Esta é uma simulação - será implementada no backend)`);
}

// Validação de formulário
function validarFormulario(formId) {
    const form = document.getElementById(formId);
    
    if (!form.checkValidity()) {
        form.classList.add('was-validated');
        return false;
    }
    
    return true;
}

// Limpar formulário
function limparFormulario(formId) {
    const form = document.getElementById(formId);
    form.reset();
    form.classList.remove('was-validated');
}
