document.addEventListener('DOMContentLoaded', () => {
    // 1. Verificar Autenticação
    const token = localStorage.getItem('smartchat_token');
    if (!token) {
        window.location.href = 'index.html'; // Redireciona para login se não houver token
        return;
    }

    // Carregar Includes (Sidebar e Header)
    loadInclude('sidebar-include', '/admin/includes/sidebar.html');
    loadInclude('header-include', '/admin/includes/header.html');

    // 3. Buscar dados do usuário logado
    fetchUserData(token);

    // 4. Configurar Botão de Logout
    document.addEventListener('click', (e) => {
        if (e.target.closest('#logoutBtn')) {
            localStorage.removeItem('smartchat_token');
            window.location.href = 'index.html';
        }
    });

    // 5. Configurar Toggle da Sidebar
    document.addEventListener('click', (e) => {
        if (e.target.closest('#sidebarToggle')) {
            const sidebar = document.getElementById('adminSidebar');
            if (window.innerWidth <= 768) {
                sidebar.classList.toggle('mobile-open');
            } else {
                sidebar.classList.toggle('collapsed');
            }
        }
    });
});

// Função auxiliar para carregar HTML externo
async function loadInclude(elementId, filePath) {
    try {
        const response = await fetch(filePath);
        if (response.ok) {
            const html = await response.text();
            document.getElementById(elementId).innerHTML = html;

            // Se for o header, atualiza o título da página baseado no link ativo
            if (elementId === 'header-include') {
                updateActivePageTitle();
            }
        }
    } catch (error) {
        console.error('Erro ao carregar include:', error);
    }
}

// Função para buscar dados do usuário na API
async function fetchUserData(token) {
    try {
        const response = await fetch('/api/auth/me', {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });

        if (response.ok) {
            const data = await response.json();
            const userNameElement = document.getElementById('userNameDisplay');
            if (userNameElement) {
                userNameElement.textContent = data.nome || data.email;
            }
        } else {
            // Se o token for inválido/expirado, faz logout
            localStorage.removeItem('smartchat_token');
            window.location.href = 'index.html';
        }
    } catch (error) {
        console.error('Erro ao buscar dados do usuário:', error);
    }
}

// Atualiza o título do header E marca o item ativo na sidebar
function updateActivePageTitle() {
    const currentPage = window.location.pathname.split('/').pop() || 'dashboard.html';
    
    // 1. Remover classe 'active' de todos os itens
    document.querySelectorAll('.nav-item').forEach(item => {
        item.classList.remove('active');
    });
    
    // 2. Adicionar classe 'active' ao item correspondente à página atual
    const activeLink = document.querySelector(`.nav-item[href="${currentPage}"]`);
    if (activeLink) {
        activeLink.classList.add('active');
        
        // 3. Atualizar o título do header
        const titleText = activeLink.querySelector('span').textContent;
        const headerTitle = document.querySelector('.header-left h6');
        if (headerTitle) {
            headerTitle.textContent = titleText;
        }
    }
}