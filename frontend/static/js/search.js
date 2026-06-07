// умный поиск с подсказками
document.addEventListener('DOMContentLoaded', function() {
    const searchInput = document.getElementById('searchInput');
    if (!searchInput) return;
    
    // контейнер для подсказок
    let suggestionsBox = document.createElement('div');
    suggestionsBox.className = 'search-suggestions';
    suggestionsBox.style.cssText = `
        position: absolute;
        top: 100%;
        left: 0;
        right: 0;
        background: white;
        border-radius: 12px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.15);
        z-index: 1000;
        max-height: 300px;
        overflow-y: auto;
        display: none;
    `;
    searchInput.parentNode.style.position = 'relative';
    searchInput.parentNode.appendChild(suggestionsBox);
    
    let debounceTimer;
    
    searchInput.addEventListener('input', function() {
        clearTimeout(debounceTimer);
        const query = this.value.trim();
        
        if (query.length < 2) {
            suggestionsBox.style.display = 'none';
            return;
        }
        
        debounceTimer = setTimeout(() => {
            fetch(`/api/search-projects?q=${encodeURIComponent(query)}`)
                .then(response => response.json())
                .then(projects => {
                    if (projects.length === 0) {
                        suggestionsBox.innerHTML = '<div style="padding: 12px; color: #999;">Ничего не найдено</div>';
                        suggestionsBox.style.display = 'block';
                        return;
                    }
                    
                    suggestionsBox.innerHTML = projects.map(project => `
                        <div class="suggestion-item" data-project-id="${project.id}" style="padding: 12px 16px; cursor: pointer; border-bottom: 1px solid #eee; transition: background 0.2s;">
                            <div style="font-weight: 600; color: #2E7D32;">🏗️ ${escapeHtml(project.name)}</div>
                            <div style="font-size: 12px; color: #666;">${escapeHtml(project.address)} | ${escapeHtml(project.client_name)}</div>
                        </div>
                    `).join('');
                    
                    suggestionsBox.style.display = 'block';
                    
                    // обработчики кликов
                    document.querySelectorAll('.suggestion-item').forEach(item => {
                        item.addEventListener('click', function() {
                            const projectId = this.dataset.projectId;
                            window.location.href = `/project/${projectId}`;
                        });
                        
                        item.addEventListener('mouseenter', function() {
                            this.style.background = '#f5f5f5';
                        });
                        
                        item.addEventListener('mouseleave', function() {
                            this.style.background = '';
                        });
                    });
                });
        }, 300);
    });
    
    // закрываем подсказки при клике вне
    document.addEventListener('click', function(e) {
        if (!searchInput.parentNode.contains(e.target)) {
            suggestionsBox.style.display = 'none';
        }
    });
    
    function escapeHtml(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
});