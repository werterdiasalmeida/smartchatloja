const GOOGLE_CLIENT_ID = "677683874020-jk8cl10664ama89mlrd6ev8qclhcs95t.apps.googleusercontent.com";
const LINKEDIN_CLIENT_ID = "77nvgsn2ecil6q";

function decodeJWT(token) {
  try {
    const base64Url = token.split('.')[1];
    const base64 = base64Url
      .replace(/-/g, '+')
      .replace(/_/g, '/');

    const jsonPayload = decodeURIComponent(
      atob(base64)
        .split('')
        .map(c =>
          '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2)
        )
        .join('')
    );

    return JSON.parse(jsonPayload);
  } catch (e) {
    return {};
  }
}

function obterModulosAcessiveis(perfis) {
  return Object.keys(perfis).filter(modulo => {
    const perfil = perfis[modulo];
    return (
      perfil !== null &&
      perfil !== undefined &&
      perfil !== '' &&
      perfil !== 'null'
    );
  });
}

function obterUrlModulo(modulo) {
  const rotas = {
    negociacoes: '/painel.html',
    projetos: '/novosprojetos/index.html',
    inventario: '/inventarios/index.html'
  };
  return rotas[modulo] || null;
}

function criarModalSelecaoModulos(perfis) {
  const modalExistente = document.getElementById('dynamic-module-modal');
  if (modalExistente) modalExistente.remove();

  const acessiveis = obterModulosAcessiveis(perfis);
  if (acessiveis.length === 0) return;

  const modalHtml = `
    <div class="modal fade" id="dynamic-module-modal" tabindex="-1" data-bs-backdrop="static" style="z-index: 9999;">
      <div class="modal-dialog modal-dialog-centered">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">Selecione o Módulo</h5>
          </div>
          <div class="modal-body">
            <p>Olá! Você tem acesso a mais de um módulo. Escolha por onde deseja começar:</p>
            <div class="list-group">
              ${acessiveis.map(modulo => {
                let nomeModulo = '';
                if (modulo === 'negociacoes') nomeModulo = 'Mesa de Negociações';
                if (modulo === 'projetos') nomeModulo = 'Novos Projetos';
                if (modulo === 'inventario') nomeModulo = 'Inventário';
                return `<button type="button" class="list-group-item list-group-item-action" data-modulo="${modulo}">${nomeModulo}</button>`;
              }).join('')}
            </div>
          </div>
        </div>
      </div>
    </div>
  `;

  document.body.insertAdjacentHTML('beforeend', modalHtml);
  const modalElement = document.getElementById('dynamic-module-modal');
  const modal = new bootstrap.Modal(modalElement, { backdrop: 'static' });

  modalElement.querySelectorAll('.list-group-item').forEach(btn => {
    btn.addEventListener('click', () => {
      const modulo = btn.getAttribute('data-modulo');
      const url = obterUrlModulo(modulo);
      if (url) {
        sessionStorage.setItem('selected_module', modulo);
        window.location.href = url;
      }
    });
  });

  modal.show();
}

function processarRedirecionamentoPosLogin(accessToken) {
  const payload = decodeJWT(accessToken);
  const perfis = payload.perfis_modulos || {};
  const acessiveis = obterModulosAcessiveis(perfis);

  if (acessiveis.length === 0) {
    alert('Nenhum módulo habilitado para sua conta.');
    return;
  }

  if (acessiveis.length === 1) {
    const modulo = acessiveis[0];
    const url = obterUrlModulo(modulo);
    if (!url) {
      alert('Módulo inválido.');
      return;
    }
    sessionStorage.setItem('selected_module', modulo);
    window.location.href = url;
    return;
  }

  // Múltiplos módulos: tenta usar a função global, senão cria modal dinâmica
  if (typeof window.showModuleSelector === 'function') {
    window.showModuleSelector(perfis);
  } else {
    criarModalSelecaoModulos(perfis);
  }
}

async function login(email, senha) {
  try {
    const response = await fetch(`${API_BASE_URL}/users/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        email,
        senha
      })
    });

    if (!response.ok) {
      const error = await response.text();
      throw new Error(error || 'Erro ao fazer login');
    }

    const data = await response.json();

    localStorage.setItem('access_token', data.access_token);
    localStorage.setItem('token_type', data.token_type);

    processarRedirecionamentoPosLogin(data.access_token);

    return {
      success: true,
      data
    };
  } catch (error) {
    console.error('Erro no login:', error);
    return {
      success: false,
      error: error.message
    };
  }
}

async function register(userData) {
  try {
    const response = await fetch(`${API_BASE_URL}/users/register`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(userData)
    });

    if (!response.ok) {
      const error = await response.text();
      throw new Error(error || 'Erro ao registrar');
    }

    await response.json();

    return await login(userData.email, userData.senha);
  } catch (error) {
    console.error('Erro no registro:', error);
    return {
      success: false,
      error: error.message
    };
  }
}

async function getCurrentUser() {
  const token = localStorage.getItem('access_token');
  if (!token) return null;

  try {
    const response = await fetch(`${API_BASE_URL}/users/me`, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });

    if (!response.ok) {
      if (response.status === 401) {
        logout();
      }
      return null;
    }

    return await response.json();
  } catch (error) {
    console.error('Erro ao buscar usuário:', error);
    return null;
  }
}

function logout() {
  localStorage.removeItem('access_token');
  localStorage.removeItem('token_type');
  sessionStorage.removeItem('selected_module');
  window.location.href = '/cadastro-usuario.html';
}

async function authFetch(url, options = {}) {
  const token = localStorage.getItem('access_token');
  if (!token) {
    window.location.href = 'cadastro-usuario.html';
    throw new Error('Não autenticado');
  }

  const headers = {
    ...options.headers,
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  };

  const response = await fetch(`${API_BASE_URL}${url}`, {
    ...options,
    headers
  });

  if (response.status === 401) {
    logout();
    throw new Error('Sessão expirada');
  }

  return response;
}

function initGoogleLogin() {
  if (
    typeof google === 'undefined' ||
    !google.accounts ||
    !google.accounts.id
  ) {
    setTimeout(initGoogleLogin, 500);
    return;
  }

  google.accounts.id.initialize({
    client_id: GOOGLE_CLIENT_ID,
    callback: handleGoogleResponse,
    auto_select: false,
    ux_mode: 'popup'
  });

  renderGoogleButtons();

  document.querySelectorAll('.auth-tabs button, .nav-tabs a, [data-bs-toggle="tab"]').forEach(tab => {
    tab.addEventListener('click', () => {
      setTimeout(renderGoogleButtons, 300);
    });
  });

  window.addEventListener('resize', () => {
    setTimeout(renderGoogleButtons, 100);
  });
}

function renderGoogleButtons() {
  const config = {
    theme: "outline",
    size: "large",
    shape: "rectangular",
    logo_alignment: "left",
    width: "100%"
  };

  const loginBtn = document.getElementById("google-btn-login");
  const registerBtn = document.getElementById("google-btn-register");

  if (loginBtn && loginBtn.offsetParent !== null) {
    loginBtn.innerHTML = "";
    try {
      google.accounts.id.renderButton(loginBtn, {
        ...config,
        text: "signin_with"
      });
    } catch (e) {
      console.warn('Erro ao renderizar botão login:', e);
    }
  }

  if (registerBtn && registerBtn.offsetParent !== null) {
    registerBtn.innerHTML = "";
    try {
      google.accounts.id.renderButton(registerBtn, {
        ...config,
        text: "signup_with"
      });
    } catch (e) {
      console.warn('Erro ao renderizar botão register:', e);
    }
  }
}

async function handleGoogleResponse(response) {
  if (!response.credential) return;

  try {
    const res = await fetch(`${API_BASE_URL}/users/google`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        token: response.credential
      })
    });

    if (!res.ok) {
      const err = await res.text();
      console.error('Erro no backend Google:', err);
      return;
    }

    const data = await res.json();

    localStorage.setItem('access_token', data.access_token);
    localStorage.setItem('token_type', data.token_type);

    processarRedirecionamentoPosLogin(data.access_token);
  } catch (error) {
    console.error('Erro no callback Google:', error);
  }
}

function loginLinkedIn() {
  const currentOrigin = window.location.origin;
  const redirectUri = encodeURIComponent(currentOrigin + "/cadastro-usuario.html");
  const scope = encodeURIComponent("openid profile email");

  window.location.href = `https://www.linkedin.com/oauth/v2/authorization?response_type=code&client_id=${LINKEDIN_CLIENT_ID}&redirect_uri=${redirectUri}&scope=${scope}`;
}

async function checkLinkedInCallback() {
  const urlParams = new URLSearchParams(window.location.search);
  const code = urlParams.get('code');
  if (!code) return;

  window.history.replaceState({}, document.title, window.location.pathname);

  try {
    const res = await fetch(`${API_BASE_URL}/users/linkedin`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        code
      })
    });

    if (!res.ok) return;

    const data = await res.json();

    localStorage.setItem('access_token', data.access_token);
    localStorage.setItem('token_type', data.token_type);

    processarRedirecionamentoPosLogin(data.access_token);
  } catch (error) {
    console.error('Erro LinkedIn:', error);
  }
}

window.auth = {
  login,
  register,
  getCurrentUser,
  logout,
  fetch: authFetch,
  initGoogleLogin,
  renderGoogleButtons,
  handleGoogleResponse,
  loginLinkedIn
};

const initAll = () => {
  initGoogleLogin();
  checkLinkedInCallback();
};

if (document.readyState === 'complete') {
  initAll();
} else {
  window.addEventListener('load', initAll);
}