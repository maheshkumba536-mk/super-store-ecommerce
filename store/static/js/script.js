document.addEventListener('DOMContentLoaded', () => {
    // --- Dark Mode Toggle ---
    const themeToggle = document.getElementById('themeToggle');
    const body = document.body;

    // Check for saved preference
    if (localStorage.getItem('theme') === 'dark') {
        body.classList.add('dark-mode');
        themeToggle.textContent = '☀️';
    }

    themeToggle?.addEventListener('click', () => {
        body.classList.toggle('dark-mode');
        const isDark = body.classList.contains('dark-mode');
        themeToggle.textContent = isDark ? '☀️' : '🌙';
        localStorage.setItem('theme', isDark ? 'dark' : 'light');
    });

    // --- Wishlist Toggle (AJAX) ---
    const wishlistBtns = document.querySelectorAll('.btn-wishlist-toggle, .btn-wishlist-large');
    wishlistBtns.forEach(btn => {
        btn.addEventListener('click', async (e) => {
            e.preventDefault();
            const productId = btn.dataset.productId;
            const url = btn.dataset.url;

            if (!url) return;

            try {
                const response = await fetch(url, {
                    headers: {
                        'X-Requested-With': 'XMLHttpRequest',
                        'X-CSRFToken': getCookie('csrftoken')
                    }
                });
                const data = await response.json();

                if (data.message) {
                    showToast(data.message, data.added ? 'success' : 'info');
                    
                    // Update UI
                    if (btn.classList.contains('btn-wishlist-toggle')) {
                        btn.classList.toggle('active', data.added);
                        btn.textContent = data.added ? '❤️' : '🤍';
                    } else {
                        btn.classList.toggle('wishlisted', data.added);
                        btn.textContent = data.added ? '❤️ In Wishlist' : '🤍 Add to Wishlist';
                    }

                    // Update badge if exists
                    const badge = document.querySelector('.nav-badge');
                    if (badge) {
                        badge.textContent = data.count;
                        badge.style.display = data.count > 0 ? 'block' : 'none';
                    }
                }
            } catch (err) {
                console.error('Wishlist error:', err);
                showToast('Something went wrong. Please try again.', 'error');
            }
        });
    });

    // --- Live Search ---
    const searchInput = document.getElementById('searchInput');
    const searchDropdown = document.getElementById('searchDropdown');
    let searchTimeout;

    searchInput?.addEventListener('input', (e) => {
        const query = e.target.value.trim();
        clearTimeout(searchTimeout);

        if (query.length < 2) {
            searchDropdown.classList.remove('show');
            return;
        }

        searchTimeout = setTimeout(async () => {
            try {
                const response = await fetch(`/search/?q=${encodeURIComponent(query)}`, {
                    headers: { 'X-Requested-With': 'XMLHttpRequest' }
                });
                const data = await response.json();
                
                if (data.products && data.products.length > 0) {
                    displaySearchResults(data.products);
                } else {
                    searchDropdown.innerHTML = '<div class="search-no-results">No deals found</div>';
                    searchDropdown.classList.add('show');
                }
            } catch (err) {
                console.error('Search error:', err);
            }
        }, 300);
    });

    function displaySearchResults(products) {
        searchDropdown.innerHTML = products.map(p => `
            <a href="/product/${p.id}/" class="search-result-item">
                <img src="${p.image || ''}" alt="">
                <div class="result-info">
                    <span class="result-title">${p.name}</span>
                    <span class="result-price">₹${p.price}</span>
                </div>
            </a>
        `).join('');
        searchDropdown.classList.add('show');
    }

    // Close dropdown on click outside
    document.addEventListener('click', (e) => {
        if (!searchInput?.contains(e.target) && !searchDropdown?.contains(e.target)) {
            searchDropdown?.classList.remove('show');
        }
    });

    // --- Helpers ---
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    function showToast(message, type = 'info') {
        const container = document.getElementById('toastContainer') || createToastContainer();
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        
        const icons = { success: '✅', error: '❌', warning: '⚠️', info: 'ℹ️' };
        
        toast.innerHTML = `
            <span class="toast-icon">${icons[type]}</span>
            <span class="toast-text">${message}</span>
            <button class="toast-close">✕</button>
        `;
        
        container.appendChild(toast);
        
        // Auto remove
        setTimeout(() => {
            toast.style.opacity = '0';
            toast.style.transform = 'translateX(20px)';
            setTimeout(() => toast.remove(), 300);
        }, 5000);

        toast.querySelector('.toast-close').onclick = () => toast.remove();
    }

    function createToastContainer() {
        const container = document.createElement('div');
        container.id = 'toastContainer';
        container.className = 'toast-container';
        document.body.appendChild(container);
        return container;
    }
    
    // --- Mobile User Dropdown ---
    const userMenuBtn = document.getElementById('userMenuBtn');
    const userDropdown = document.getElementById('userDropdown');
    
    userMenuBtn?.addEventListener('click', (e) => {
        e.stopPropagation();
        userDropdown.classList.toggle('show');
    });
    
    document.addEventListener('click', () => {
        userDropdown?.classList.remove('show');
    });
});
