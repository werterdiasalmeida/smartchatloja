const API_BASE_URL = window.location.origin + '/api';

const api = {
    async request(endpoint, options = {}) {
        const token = localStorage.getItem('access_token');
        const isFormData = options.body instanceof FormData;
        
        // Se for FormData, NÃO seta Content-Type (o navegador gera o boundary automaticamente)
        const headers = {
            ...(isFormData ? {} : { 'Content-Type': 'application/json' }),
            ...options.headers
        };

        if (token) {
            headers['Authorization'] = `Bearer ${token}`;
        }

        try {
            const url = `${API_BASE_URL}${endpoint}`;
            const response = await fetch(url, {
                ...options,
                headers,
                credentials: 'include',
                mode: 'cors'
            });

            if (response.status === 401) {
                if (endpoint === '/users/me') {
                    localStorage.removeItem('access_token');
                    window.location.href = 'cadastro-usuario.html';
                }
                throw new Error('Não autorizado');
            }

            return response;
        } catch (error) {
            console.error(`Erro na requisição para ${endpoint}:`, error);
            throw error;
        }
    },

    async get(endpoint) {
        return this.request(endpoint);
    },

    async post(endpoint, data) {
        const isFormData = data instanceof FormData;
        return this.request(endpoint, {
            method: 'POST',
            body: isFormData ? data : JSON.stringify(data)  // ✅ Preserva FormData
        });
    },

    async put(endpoint, data) {
        const isFormData = data instanceof FormData;
        return this.request(endpoint, {
            method: 'PUT',
            body: isFormData ? data : JSON.stringify(data)  // ✅ Preserva FormData
        });
    },

    async delete(endpoint) {
        return this.request(endpoint, {
            method: 'DELETE'
        });
    },

    async criarDepositoPix(valor, descricao = "Depósito - Plataforma Ipê Digital") {
        const response = await this.post('/pagamentos/deposito/pix', {
            valor,
            descricao
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Erro ao criar depósito PIX');
        }
        
        return response.json();
    },

    async solicitarSaque(valor, chavePix, tipoChave = "ALEATORIA") {
        const response = await this.post('/pagamentos/saque', {
            valor,
            chave_pix: chavePix,
            tipo_chave: tipoChave
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Erro ao solicitar saque');
        }
        
        return response.json();
    },

    async getHistoricoTransacoes() {
        const response = await this.get('/pagamentos/historico');
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Erro ao buscar histórico');
        }
        
        return response.json();
    }
};

const auth = {
    async login(email, senha) {
        try {
            const response = await api.post('/users/login', { email, senha });
            const data = await response.json();
            localStorage.setItem('access_token', data.access_token);
            return { success: true, data };
        } catch (error) {
            console.error('Erro no login:', error);
            return { success: false, error: error.message };
        }
    },

    async register(userData) {
        try {
            const response = await api.post('/users/register', userData);
            const data = await response.json();
            return await this.login(userData.email, userData.senha);
        } catch (error) {
            console.error('Erro no registro:', error);
            return { success: false, error: error.message };
        }
    },

    async getCurrentUser() {
        const token = localStorage.getItem('access_token');
        if (!token) return null;

        try {
            const response = await api.get('/users/me');
            if (!response.ok) return null;
            return await response.json();
        } catch (error) {
            console.error('Erro ao buscar usuário:', error);
            return null;
        }
    },

    logout() {
        localStorage.removeItem('access_token');
        window.location.href = 'cadastro-usuario.html';
    },

    isAuthenticated() {
        return !!localStorage.getItem('access_token');
    }
};

window.api = api;
window.auth = auth;