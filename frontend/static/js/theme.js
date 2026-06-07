// Тёмная тема для Карманный Прораб
document.addEventListener('DOMContentLoaded', function() {
    // Проверяем сохранённую тему
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme === 'dark') {
        enableDarkTheme();
    }
    
    // Добавляем кнопку переключения темы в меню (если её нет)
    addThemeToggleButton();
});

function enableDarkTheme() {
    document.body.classList.add('dark-theme');
    localStorage.setItem('theme', 'dark');
    
    // Добавляем стили тёмной темы
    if (!document.getElementById('dark-theme-styles')) {
        const style = document.createElement('style');
        style.id = 'dark-theme-styles';
        style.textContent = `
            body.dark-theme {
                background: #1a1a2e;
            }
            body.dark-theme .card,
            body.dark-theme .top-bar,
            body.dark-theme .modal-content,
            body.dark-theme .accordion-item,
            body.dark-theme .list-group-item {
                background: #252540;
                color: #e0e0e0;
            }
            body.dark-theme .card-body,
            body.dark-theme .card-header,
            body.dark-theme .accordion-header,
            body.dark-theme .accordion-body {
                background: #252540 !important;
                color: #e0e0e0;
            }
            body.dark-theme .card-header.bg-success,
            body.dark-theme .card-header.bg-primary,
            body.dark-theme .card-header.bg-danger,
            body.dark-theme .card-header.bg-info,
            body.dark-theme .card-header.bg-dark,
            body.dark-theme .card-header.bg-secondary {
                background: #1a1a3e !important;
            }
            body.dark-theme .table thead th {
                background: #1a1a3e;
                color: #a0e0a0;
            }
            body.dark-theme .table tbody td {
                color: #d0d0e0;
                border-bottom-color: #3a3a5a;
            }
            body.dark-theme .form-control,
            body.dark-theme .form-select {
                background: #3a3a5a;
                border-color: #5a5a8a;
                color: #e0e0e0;
            }
            body.dark-theme .form-control:focus,
            body.dark-theme .form-select:focus {
                background: #4a4a6a;
                color: #ffffff;
            }
            body.dark-theme .alert-info,
            body.dark-theme .alert-success,
            body.dark-theme .alert-danger,
            body.dark-theme .alert-warning {
                background: #1a2a3a;
                color: #d0d0e0;
                border: 1px solid #4a6a8a;
            }
            body.dark-theme .alert-success {
                background: #1a3a2a;
            }
            body.dark-theme .alert-danger {
                background: #3a1a1a;
            }
            body.dark-theme .text-muted {
                color: #a0a0c0 !important;
            }
            body.dark-theme .btn-outline-secondary {
                color: #a0a0c0;
                border-color: #5a5a8a;
            }
            body.dark-theme .btn-outline-secondary:hover {
                background: #3a3a5a;
                color: #ffffff;
            }
            body.dark-theme .progress {
                background: #3a3a5a;
            }
            body.dark-theme .modal-header,
            body.dark-theme .modal-footer {
                background: #1a1a3e;
                border-color: #3a3a5a;
            }
            body.dark-theme .dropdown-menu {
                background: #252540;
                color: #e0e0e0;
            }
            body.dark-theme .dropdown-item {
                color: #e0e0e0;
            }
            body.dark-theme .dropdown-item:hover {
                background: #3a3a5a;
                color: #ffffff;
            }
            body.dark-theme .border {
                border-color: #3a3a5a !important;
            }
            body.dark-theme .bg-light {
                background: #1a1a3e !important;
            }
            body.dark-theme .side-menu {
                background: linear-gradient(135deg, #0d1f0d 0%, #1a3a1a 100%);
            }
            body.dark-theme .top-bar {
                background: #1a1a3e;
                border-bottom: 1px solid #3a3a5a;
            }
            body.dark-theme .user-avatar {
                background: #3a3a5a;
            }
            body.dark-theme .avatar-icon {
                background: linear-gradient(135deg, #1a5a1a 0%, #2a8a2a 100%);
            }
            body.dark-theme .badge.bg-warning {
                background: #8a6a1a !important;
                color: #e0e0e0;
            }
            body.dark-theme .badge.bg-success {
                background: #1a6a1a !important;
            }
            body.dark-theme .badge.bg-secondary {
                background: #4a4a6a !important;
            }
            body.dark-theme .badge.bg-info {
                background: #1a6a8a !important;
            }
            body.dark-theme .nav-tabs {
                border-bottom-color: #3a3a5a;
            }
            body.dark-theme .nav-tabs .nav-link {
                color: #a0a0c0;
            }
            body.dark-theme .nav-tabs .nav-link.active {
                color: #a0e0a0;
                border-bottom-color: #a0e0a0;
            }
        `;
        document.head.appendChild(style);
    }
}

function disableDarkTheme() {
    document.body.classList.remove('dark-theme');
    localStorage.setItem('theme', 'light');
}

function toggleTheme() {
    if (document.body.classList.contains('dark-theme')) {
        disableDarkTheme();
    } else {
        enableDarkTheme();
    }
}

function addThemeToggleButton() {
    // Проверяем, есть ли уже кнопка в меню
    if (document.getElementById('theme-menu-item')) return;
    
    // Находим меню пользователя (dropdown)
    const dropdownMenu = document.querySelector('.dropdown-menu');
    if (dropdownMenu) {
        // Создаём разделитель и пункт меню
        const divider = document.createElement('li');
        divider.innerHTML = '<hr class="dropdown-divider">';
        dropdownMenu.appendChild(divider);
        
        const themeItem = document.createElement('li');
        themeItem.id = 'theme-menu-item';
        themeItem.innerHTML = `
            <a class="dropdown-item" href="#" id="themeToggleBtn">
                <i class="bi bi-moon-stars"></i> Тёмная тема
            </a>
        `;
        dropdownMenu.appendChild(themeItem);
        
        const themeBtn = document.getElementById('themeToggleBtn');
        if (themeBtn) {
            themeBtn.addEventListener('click', function(e) {
                e.preventDefault();
                toggleTheme();
                // Обновляем текст кнопки
                if (document.body.classList.contains('dark-theme')) {
                    this.innerHTML = '<i class="bi bi-sun"></i> Светлая тема';
                } else {
                    this.innerHTML = '<i class="bi bi-moon-stars"></i> Тёмная тема';
                }
            });
        }
    }
}