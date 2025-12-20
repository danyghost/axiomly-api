// --- Конфигурация ---
const CONFIG = {
    buildingTypes: [
        {label: "Иное", value: 0},
        {label: "Панельный", value: 1},
        {label: "Монолитный", value: 2},
        {label: "Кирпичный", value: 3},
        {label: "Блочный", value: 4},
        {label: "Деревянный", value: 5}
    ],
    objectTypes: [
        {label: "Вторичный рынок", value: 1},
        {label: "Новостройки", value: 2}
    ],
    rooms: [
        {label: "Студия", value: 0},
        {label: "1", value: 1},
        {label: "2", value: 2},
        {label: "3", value: 3},
        {label: "4", value: 4},
        {label: "5+", value: 5}
    ],
    dealTypes: [
        {label: "Покупка/Продажа", value: "sale"},
        {label: "Аренда", value: "rent"}
    ]
};

// --- Глобальные переменные ---
let selectedLocation = { type: '', name: '', region: '' };
let selectedChips = {
    'deal-type-list': null,
    'building-type-list': null,
    'object-type-list': null,
    'rooms-list': null
};

// --- DOM элементы ---
const elements = {
    locationSearch: document.getElementById('location-search'),
    searchResults: document.getElementById('search-results'),
    selectedLocationInfo: document.getElementById('selected-location-info'),
    selectedLocationText: document.getElementById('selected-location-text'),
    resultBlock: document.getElementById('result'),
    predictButton: document.getElementById('predict-button')
};

// --- Утилиты ---
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// --- Работа с чипами ---
function renderChips(list, containerId, single = true) {
    const container = document.getElementById(containerId);
    container.innerHTML = '';

    list.forEach((item) => {
        const chip = document.createElement('div');
        chip.className = 'chip';
        chip.textContent = item.label;
        chip.dataset.value = item.value;

        chip.addEventListener('click', () => {
            if (single) {
                container.querySelectorAll('.chip').forEach(c => c.classList.remove('selected'));
                chip.classList.add('selected');
                selectedChips[containerId] = chip.dataset.value;
            } else {
                chip.classList.toggle('selected');
            }
        });

        if (selectedChips[containerId] && chip.dataset.value == selectedChips[containerId]) {
            chip.classList.add('selected');
        }

        container.appendChild(chip);
    });
}

function getSelected(containerId) {
    const sel = document.querySelector(`#${containerId} .chip.selected`);
    return sel ? sel.dataset.value : selectedChips[containerId] || null;
}

// --- Поиск локаций ---
async function searchLocations(query) {
    if (query.length < 2) {
        elements.searchResults.innerHTML = '';
        elements.searchResults.style.display = 'none';
        return;
    }

    try {
        const response = await fetch(`/api/search-locations?q=${encodeURIComponent(query)}`);
        if (!response.ok) throw new Error('Ошибка поиска');

        const locations = await response.json();
        renderSearchResults(locations);
    } catch (error) {
        console.error('Ошибка поиска локаций:', error);
        elements.searchResults.innerHTML = '<div class="no-results">Ошибка загрузки данных</div>';
        elements.searchResults.style.display = 'block';
    }
}

function renderSearchResults(locations) {
    if (!locations || locations.length === 0) {
        elements.searchResults.innerHTML = '<div class="no-results">Ничего не найдено</div>';
        elements.searchResults.style.display = 'block';
        return;
    }

    // Группируем по регионам
    const grouped = {};
    locations.forEach(location => {
        if (location.type === 'region') {
            if (!grouped[location.value]) {
                grouped[location.value] = { region: location, cities: [] };
            }
        } else {
            if (!grouped[location.region]) {
                grouped[location.region] = {
                    region: { type: 'region', name: location.region, value: location.region },
                    cities: []
                };
            }
            grouped[location.region].cities.push(location);
        }
    });

    // Сортируем регионы по алфавиту
    const sortedRegions = Object.keys(grouped).sort((a, b) => a.localeCompare(b, 'ru'));

    // Рендерим результаты
    const html = sortedRegions.map(regionName => {
        const group = grouped[regionName];
        const sortedCities = group.cities.sort((a, b) => a.name.localeCompare(b.name, 'ru'));

        return `
            <div class="region-group">
                <div class="region-name">${group.region.name}</div>
                ${sortedCities.map(city => `
                    <div class="city-item" data-type="city" data-name="${city.name}" data-region="${city.region}">
                        ${city.name}
                    </div>
                `).join('')}
            </div>
        `;
    }).join('');

    elements.searchResults.innerHTML = html;
    elements.searchResults.style.display = 'block';

    // Добавляем обработчики событий
    document.querySelectorAll('.city-item').forEach(item => {
        item.addEventListener('click', () => {
            const type = item.dataset.type;
            const name = item.dataset.name;
            const region = item.dataset.region;

            selectedLocation = { type, name, region };
            elements.locationSearch.value = name;
            elements.selectedLocationText.textContent = `${name} (${region})`;
            elements.selectedLocationInfo.style.display = 'block';
            elements.searchResults.style.display = 'none';
        });
    });
}

// --- Валидация ---
function clearFieldErrors() {
    document.querySelectorAll('.field-error').forEach(e => e.textContent = '');
    document.querySelectorAll('.input-error').forEach(e => e.classList.remove('input-error'));
    document.querySelectorAll('.chip-list').forEach(e => e.classList.remove('chip-error'));
}

function showFieldError(inputId, errorId, message) {
    document.getElementById(errorId).textContent = message;
    const inputElement = document.getElementById(inputId);
    if (inputElement) {
        inputElement.classList.add('input-error');
    }
}

function showChipError(errorId, message, chipListId) {
    document.getElementById(errorId).textContent = message;
    document.getElementById(chipListId).classList.add('chip-error');
}

function validateForm() {
    let hasError = false;
    clearFieldErrors();

    // Валидация локации
    if (!selectedLocation.name || !selectedLocation.region) {
        showFieldError('location-search', 'error-location', 'Выберите город из списка');
        hasError = true;
    }

    // Валидация чипов
    const building_type = getSelected('building-type-list');
    const object_type = getSelected('object-type-list');
    const roomsVal = getSelected('rooms-list');
    const deal_type = getSelected('deal-type-list');

    if (!building_type || !CONFIG.buildingTypes.some(t => String(t.value) === String(building_type))) {
        showChipError('error-building-type', 'Выберите тип здания из списка', 'building-type-list');
        hasError = true;
    }
    if (!object_type || !CONFIG.objectTypes.some(t => String(t.value) === String(object_type))) {
        showChipError('error-object-type', 'Выберите тип объекта из списка', 'object-type-list');
        hasError = true;
    }
    if (!roomsVal || !CONFIG.rooms.some(t => String(t.value) === String(roomsVal))) {
        showChipError('error-rooms', 'Выберите количество комнат из списка', 'rooms-list');
        hasError = true;
    }
    if (!deal_type || !CONFIG.dealTypes.some(t => String(t.value) === String(deal_type))) {
        showChipError('error-deal-type', 'Выберите тип сделки из списка', 'deal-type-list');
        hasError = true;
    }

    // Валидация числовых полей
    const level = document.getElementById('level').value;
    const levels = document.getElementById('levels').value;
    const area = document.getElementById('area').value;
    const kitchen_area = document.getElementById('kitchen_area').value;

    if (!level) {
        showFieldError('level', 'error-level', 'Заполните этаж');
        hasError = true;
    }
    if (!levels) {
        showFieldError('levels', 'error-levels', 'Заполните этажность');
        hasError = true;
    }
    if (!area) {
        showFieldError('area', 'error-area', 'Заполните площадь');
        hasError = true;
    }
    if (!kitchen_area) {
        showFieldError('kitchen_area', 'error-kitchen_area', 'Заполните кухню');
        hasError = true;
    }

    return !hasError;
}

// --- Основная функция расчета ---
async function calculate() {
    if (!validateForm()) return;

    elements.resultBlock.style.display = 'none';
    elements.resultBlock.innerHTML = '';

    try {
        const building_type = getSelected('building-type-list');
        const object_type = getSelected('object-type-list');
        const roomsVal = getSelected('rooms-list');
        const deal_type = getSelected('deal-type-list');
        const level = document.getElementById('level').value;
        const levels = document.getElementById('levels').value;
        const area = document.getElementById('area').value;
        const kitchen_area = document.getElementById('kitchen_area').value;

        const response = await fetch('/api/predict', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                location: selectedLocation.name,
                building_type: building_type,
                object_type: object_type,
                level: Number(level),
                levels: Number(levels),
                rooms: Number(roomsVal),
                area: Number(area),
                kitchen_area: Number(kitchen_area) || Number(area) * 0.2,
                deal_type: deal_type
            })
        });

        const data = await response.json();

        if (response.ok && data.success) {
            renderResult(data);
        } else {
            showError(data.error || 'Ошибка расчёта');
        }
    } catch (e) {
        console.error('Ошибка:', e);
        showError('Ошибка соединения с сервером');
    }
}

function renderResult(data) {
    const isRent = data.is_rent || false;
    const description = isRent ?
        'Ориентировочная стоимость аренды по введённым параметрам' :
        'Ориентировочная стоимость по введённым параметрам';

    const pricePerSqmInfo = isRent ? '' :
        `<div><strong>Цена за м²:</strong> ${Math.round(data.price / data.area).toLocaleString('ru-RU')} руб.</div>`;

    elements.resultBlock.innerHTML = `
        <div class="result-block">
            <div class="result-price">${data.price_formatted}</div>
            <div class="result-desc">${description}</div>
            <div class="result-details">
                <div><strong>Регион:</strong> ${data.region}</div>
                <div><strong>Город:</strong> ${data.city}</div>
                <div><strong>Площадь:</strong> ${data.area} м²</div>
                <div><strong>Комнат:</strong> ${data.rooms}</div>
                ${pricePerSqmInfo}
            </div>
        </div>
    `;
    elements.resultBlock.style.display = 'block';
}

function showError(message) {
    elements.resultBlock.innerHTML = `
        <div class="result-block">
            <div class="result-desc">${message}</div>
        </div>
    `;
    elements.resultBlock.style.display = 'block';
}

// --- Инициализация ---
function initializeApp() {
    // Устанавливаем значения по умолчанию
    selectedChips['building-type-list'] = '0';
    selectedChips['object-type-list'] = '1';
    selectedChips['rooms-list'] = '1';
    selectedChips['deal-type-list'] = 'sale';

    // Инициализируем чипы
    renderChips(CONFIG.buildingTypes, 'building-type-list');
    renderChips(CONFIG.objectTypes, 'object-type-list');
    renderChips(CONFIG.rooms, 'rooms-list');
    renderChips(CONFIG.dealTypes, 'deal-type-list');

    // Настраиваем обработчики событий
    elements.locationSearch.addEventListener('input', debounce((e) => {
        searchLocations(e.target.value.trim());
    }, 300));

    elements.locationSearch.addEventListener('focus', () => {
        if (elements.locationSearch.value.trim().length >= 2) {
            searchLocations(elements.locationSearch.value.trim());
        }
    });

    elements.predictButton.addEventListener('click', calculate);

    // Скрытие результатов поиска при клике вне поля
    document.addEventListener('click', (e) => {
        if (!elements.locationSearch.contains(e.target) && !elements.searchResults.contains(e.target)) {
            elements.searchResults.style.display = 'none';
        }
    });
}

// Запуск приложения
document.addEventListener('DOMContentLoaded', initializeApp);