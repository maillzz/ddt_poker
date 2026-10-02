'use strict';
(() => {
  const assetRoot = document.body.dataset.assets;
  const suits = {s: 'пик', h: 'червей', d: 'бубен', c: 'треф'};
  const ranks = {A: 'Туз', K: 'Король', Q: 'Дама', J: 'Валет', T: '10'};
  const normalize = card => card.length === 2 ? card[0].toUpperCase() + card[1].toLowerCase() : card;
  const validCard = card => /^[2-9TJQKA][shdc]$/.test(card);
  const name = card => `${ranks[card[0]] || card[0]} ${suits[card[1]]}`;
  const form = document.getElementById('poker-form');
  const paramsNode = document.getElementById('task-params');
  const picker = document.getElementById('card-picker');
  let cards = {hole: [null, null], board: Array(5).fill(null)};
  let target = null;
  const readInput = id => document.getElementById(id).value.trim().split(/\s+/).filter(Boolean).map(normalize);
  function fromInputs() {
    cards.hole = Array.from({length: 2}, (_, i) => readInput('id_hole_cards')[i] || null);
    cards.board = Array.from({length: 5}, (_, i) => readInput('id_community')[i] || null);
    renderTable();
  }
  function updateInputs() {
    document.getElementById('id_hole_cards').value = cards.hole.filter(Boolean).join(' ');
    document.getElementById('id_community').value = cards.board.filter(Boolean).join(' ');
    renderTable();
  }
  function renderTable() {
    for (const [group, id] of [['hole', 'hole-cards'], ['board', 'board-cards']]) {
      const container = document.getElementById(id);
      if (!container) continue;
      container.replaceChildren();
      cards[group].forEach((card, index) => {
        const button = document.createElement('button');
        button.type = 'button';
        button.className = 'playing-card';
        button.disabled = !form;
        const label = group === 'hole' ? 'Карманная карта' : 'Карта стола';
        if (card && validCard(card)) {
          const img = document.createElement('img');
          img.src = `${assetRoot}${card}.svg`;
          img.alt = name(card);
          button.append(img);
          button.setAttribute('aria-label', `${label} ${index + 1}: ${name(card)}`);
        } else {
          button.classList.add('empty');
          button.setAttribute('aria-label', `${label} ${index + 1}: выбрать карту`);
        }
        if (form) button.addEventListener('click', () => openPicker(group, index));
        container.append(button);
      });
    }
    const count = cards.board.filter(Boolean).length;
    const street = count === 0 ? 'PREFLOP' : count === 3 ? 'FLOP' : count === 4 ? 'TURN' : count === 5 ? 'RIVER' : `БОРД · ${count} КАРТЫ`;
    const streetLabel = document.getElementById('street-label');
    if (streetLabel) streetLabel.textContent = street;
  }
  function openPicker(group, index) {
    target = {group, index};
    document.getElementById('picker-title').textContent = `${group === 'hole' ? 'Ваша рука' : 'Общие карты'} · карта ${index + 1}`;
    const selected = cards[group][index];
    const used = [...cards.hole, ...cards.board].filter(Boolean);
    const deck = document.getElementById('deck');
    deck.replaceChildren();
    for (const suit of 'shcd') {
      for (const rank of 'AKQJT98765432') {
        const card = rank + suit;
        const button = document.createElement('button');
        button.type = 'button';
        button.disabled = used.includes(card) && card !== selected;
        button.setAttribute('aria-label', name(card));
        button.setAttribute('aria-pressed', String(selected === card));
        const img = document.createElement('img');
        img.src = `${assetRoot}${card}.svg`;
        img.alt = '';
        button.append(img);
        button.addEventListener('click', () => {
          cards[group][index] = card;
          if (group === 'board') cards.board = [...cards.board.filter(Boolean), ...Array(5).fill(null)].slice(0, 5);
          updateInputs();
          picker.close();
        });
        deck.append(button);
      }
    }
    document.getElementById('remove-card').disabled = !selected;
    picker.showModal();
  }
  function updatePot(value) {
    const display = document.getElementById('pot-display');
    if (display) display.textContent = Number(value || 0).toLocaleString('ru-RU', {maximumFractionDigits: 2});
  }
  function refreshPresets() {
    document.querySelectorAll('[data-simulations]').forEach(button => {
      const selected = Number(button.dataset.simulations) === Number(document.getElementById('id_simulations').value);
      button.classList.toggle('selected', selected);
      button.setAttribute('aria-pressed', String(selected));
    });
  }
  if (form) {
    fromInputs();
    document.getElementById('id_hole_cards').addEventListener('input', fromInputs);
    document.getElementById('id_community').addEventListener('input', fromInputs);
    document.getElementById('close-picker').addEventListener('click', () => picker.close());
    picker.addEventListener('click', event => {if (event.target === picker) {
      const rect = picker.getBoundingClientRect();
      if (event.clientX < rect.left || event.clientX > rect.right || event.clientY < rect.top || event.clientY > rect.bottom) picker.close();
    }});
    document.getElementById('remove-card').addEventListener('click', () => {
      cards[target.group][target.index] = null;
      if (target.group === 'board') cards.board = [...cards.board.filter(Boolean), ...Array(5).fill(null)].slice(0, 5);
      updateInputs(); picker.close();
    });
    document.getElementById('clear-board').addEventListener('click', () => {cards.board = Array(5).fill(null); updateInputs();});
    document.querySelectorAll('[data-step]').forEach(button => button.addEventListener('click', () => {
      const input = document.getElementById('id_opponents');
      input.value = Math.max(1, Math.min(9, (Number(input.value) || 1) + Number(button.dataset.step)));
    }));
    document.querySelectorAll('[data-simulations]').forEach(button => button.addEventListener('click', () => {
      document.getElementById('id_simulations').value = button.dataset.simulations; refreshPresets();
    }));
    document.getElementById('id_simulations').addEventListener('input', refreshPresets);
    document.getElementById('id_pot_size').addEventListener('input', event => updatePot(event.target.value));
    updatePot(document.getElementById('id_pot_size').value);
    refreshPresets();
    form.addEventListener('submit', () => {
      const button = form.querySelector('[type="submit"]');
      button.disabled = true; button.firstElementChild.textContent = 'Запускаем расчёт…';
    });
    // Browsers restore pages from their back/forward cache with disabled buttons.
    window.addEventListener('pageshow', () => {
      const button = form.querySelector('[type="submit"]');
      button.disabled = false; button.firstElementChild.textContent = 'Рассчитать шансы';
    });
  } else if (paramsNode) {
    const params = JSON.parse(paramsNode.textContent);
    cards.hole = Array.from({length: 2}, (_, i) => params.hole_cards[i] || null);
    cards.board = Array.from({length: 5}, (_, i) => params.community[i] || null);
    renderTable(); updatePot(params.pot_size);
    document.getElementById('table-hint').textContent = 'Исходная раздача · карты, использованные в расчёте';
  }
  const pollStatus = document.getElementById('poll-status');
  if (pollStatus) {
    let failures = 0;
    async function poll() {
      try {
        const response = await fetch(pollStatus.dataset.url, {headers: {Accept: 'application/json'}});
        if (response.status === 401 || response.redirected) {
          document.getElementById('poll-message').textContent = 'Сессия завершена. Обновите страницу и войдите снова.';
          return;
        }
        if (!response.ok) throw new Error('Status unavailable');
        const task = await response.json();
        if (task.status === 'FINISHED' || task.status === 'FAILED') {location.reload(); return;}
        failures = 0;
        document.getElementById('poll-message').textContent = task.status === 'RUNNING' ? 'Расчёт выполняется…' : 'Ожидаем запуска…';
      } catch (_) {
        failures++;
        document.getElementById('poll-message').textContent = 'Связь прервана. Пробуем подключиться снова…';
      }
      setTimeout(poll, Math.min(1500 * (failures + 1), 10000));
    }
    poll();
  }
})();
