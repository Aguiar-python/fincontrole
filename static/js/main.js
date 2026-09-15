// Menu lateral no mobile
document.addEventListener('DOMContentLoaded', () => {
  const toggle = document.getElementById('menuToggle');
  const sidebar = document.querySelector('.sidebar');
  if (toggle && sidebar) {
    toggle.addEventListener('click', () => sidebar.classList.toggle('open'));
  }
});

// Modais
function abrirModal(id) {
  const el = document.getElementById(id);
  if (el) el.classList.add('open');
}

function fecharModal(id) {
  const el = document.getElementById(id);
  if (el) el.classList.remove('open');
}

// Fecha ao clicar fora
document.addEventListener('click', (e) => {
  if (e.target.classList && e.target.classList.contains('modal-backdrop')) {
    e.target.classList.remove('open');
  }
});

document.addEventListener('keydown', (e) => {
  if (e.key === 'Escape') {
    document.querySelectorAll('.modal-backdrop.open').forEach(m => m.classList.remove('open'));
  }
});

// Mostra/esconde campos de cartão conforme a forma de pagamento
function alternarCamposCartao(selectEl, wrapperIds) {
  const ehCartao = selectEl.value === 'cartao';
  wrapperIds.forEach(id => {
    const el = document.getElementById(id);
    if (el) el.style.display = ehCartao ? '' : 'none';
  });
}
