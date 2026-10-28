const search = document.querySelector('#demo-search');
const filters = [...document.querySelectorAll('[data-filter]')];
const cards = [...document.querySelectorAll('.demo-card')];
const result = document.querySelector('.demo-result');
const empty = document.querySelector('.demo-empty');
let selectedType = 'all';

function updateDemo() {
  const query = search.value.trim().toLocaleLowerCase();
  let count = 0;
  for (const card of cards) {
    const matchesType = selectedType === 'all' || card.dataset.type === selectedType;
    const matchesQuery = card.dataset.search.toLocaleLowerCase().includes(query);
    card.hidden = !(matchesType && matchesQuery);
    if (!card.hidden) count += 1;
  }
  for (const filter of filters) {
    filter.setAttribute('aria-pressed', String(filter.dataset.filter === selectedType));
  }
  empty.hidden = count !== 0;
  result.textContent = `${count} 条演示记录`;
}

search.addEventListener('input', updateDemo);
for (const filter of filters) {
  filter.addEventListener('click', () => {
    selectedType = filter.dataset.filter;
    updateDemo();
  });
}
document.querySelector('.demo-reset').addEventListener('click', () => {
  selectedType = 'all';
  search.value = '';
  updateDemo();
  search.focus();
});
