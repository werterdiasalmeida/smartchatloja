async function loadComponent(elementId, filePath) {
    try {
        const response = await fetch(filePath);
        if (response.ok) {
            const content = await response.text();
            document.getElementById(elementId).innerHTML = content;
            
            if (elementId === 'header-container' || elementId === 'sidebar-container') {
                initMenuLogic();
            }

            if (elementId === 'header-container') {
                await fillUserData();
            }

            document.dispatchEvent(new Event('componentsLoaded'));
        }
    } catch (error) {
        console.error("Erro ao carregar componente:", filePath, error);
    }
}

async function fillUserData() {
    try {
        if (!window.auth) {
            setTimeout(fillUserData, 100);
            return;
        }

        const user = await window.auth.getCurrentUser();
        if (!user) {
            return;
        }

        const nameEl = document.getElementById('header-user-name');
        const roleEl = document.getElementById('header-user-role');
        if (nameEl) nameEl.textContent = user.nome_completo;
        if (roleEl) roleEl.textContent = user.perfil_atuacao || 'Usuário';

        const avatarContainer = document.getElementById('header-user-avatar');
        if (avatarContainer) {
            const iniciais = user.avatar_iniciais || 
                user.nome_completo.split(' ').map(n => n[0]).join('').toUpperCase().substring(0, 2);
            
            avatarContainer.innerHTML = `
                <div class="rounded-circle bg-primary text-white d-flex align-items-center justify-content-center" 
                     style="width: 35px; height: 35px; font-size: 0.8rem; font-weight: 500;">
                    ${iniciais}
                </div>`;
        }

        const badge = document.getElementById('notification-badge');
        if (badge) {
            badge.textContent = user.notificacoes_nao_lidas || 0;
            badge.style.display = user.notificacoes_nao_lidas > 0 ? 'inline-block' : 'none';
        }

        if (user.perfil_atuacao === 'Apenas Negociador') {
            document.querySelectorAll('.apenas-proprietario').forEach(function (el) {
                el.style.display = 'none';
            });
        }

        await loadNotifications();
    } catch (error) {
        console.error("Erro ao carregar dados do usuário:", error);
    }
}

async function loadNotifications() {
    try {
        if (!window.api) return;

        const response = await window.api.get('/users/notificacoes');
        if (response.ok) {
            const notificacoes = await response.json();
            const list = document.getElementById('notifications-list');
            const badge = document.getElementById('notification-badge');
            
            if (list) {
                if (!notificacoes || notificacoes.length === 0) {
                    list.innerHTML = '<li><span class="dropdown-item text-muted">Nenhuma notificação</span></li>';
                } else {
                    const naoLidas = notificacoes.filter(n => !n.lida).length;
                    if (badge) {
                        badge.textContent = naoLidas;
                        badge.style.display = naoLidas > 0 ? 'inline-block' : 'none';
                    }
                    
                    list.innerHTML = notificacoes.map(n => `
                        <li>
                            <a class="dropdown-item py-2 ${n.lida ? 'text-muted' : 'fw-bold'}" href="#" onclick="marcarNotificacaoLida('${n.id}')">
                                <div class="d-flex align-items-center">
                                    <i class="bi ${n.icone || 'bi-info-circle'} me-3"></i>
                                    <div>
                                        <div class="small ${n.lida ? '' : 'fw-bold'}">${n.titulo}</div>
                                        <div class="text-muted x-small">${n.mensagem}</div>
                                    </div>
                                </div>
                            </a>
                        </li>
                    `).join('');
                }
            }
        }
    } catch (error) {
        console.error("Erro ao carregar notificações:", error);
    }
}

async function marcarNotificacaoLida(id) {
    try {
        if (!window.api) return;
        
        await window.api.post(`/users/notificacoes/${id}/ler`);
        await loadNotifications();
    } catch (error) {
        console.error("Erro ao marcar notificação:", error);
    }
}

function initMenuLogic() {
    const sidebar = document.getElementById('sidebar');
    const overlay = document.getElementById('sidebarOverlay');
    const toggle = document.getElementById('mobileMenuToggle');

    if (toggle && sidebar) {
        toggle.onclick = () => {
            sidebar.classList.toggle('show');
            overlay.classList.toggle('show');
        };
    }

    if (overlay) {
        overlay.onclick = () => {
            sidebar.classList.remove('show');
            overlay.classList.remove('show');
        };
    }
}

async function checkAuth() {
    const publicPages = ['cadastro-usuario.html', 'index.html'];
    const currentPage = window.location.pathname.split('/').pop() || 'index.html';
    
    if (publicPages.includes(currentPage)) {
        return true;
    }

    const token = localStorage.getItem('access_token');
    if (!token) {
        window.location.href = 'cadastro-usuario.html';
        return false;
    }

    const maxAttempts = 50;
    let attempts = 0;
    
    while (!window.auth && attempts < maxAttempts) {
        await new Promise(resolve => setTimeout(resolve, 100));
        attempts++;
    }

    if (!window.auth || typeof window.auth.getCurrentUser !== 'function') {
        console.error('Auth não disponível após', attempts, 'tentativas');
        window.location.href = 'cadastro-usuario.html';
        return false;
    }

    const user = await window.auth.getCurrentUser();
    if (!user) {
        localStorage.removeItem('access_token');
        window.location.href = 'cadastro-usuario.html';
        return false;
    }

    return true;
}

document.addEventListener('DOMContentLoaded', async () => {
    const isAuthenticated = await checkAuth();
    if (isAuthenticated) {
        loadComponent('sidebar-container', 'includes/sidebar.html');
        loadComponent('header-container', 'includes/header.html');
    }
});

window.loadNotifications = loadNotifications;
window.marcarNotificacaoLida = marcarNotificacaoLida;