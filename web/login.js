        window.addEventListener('DOMContentLoaded', () => {
            checkExistingAuth();
            
            document.body.style.opacity = '1';
            setTimeout(() => {
                document.getElementById('loginWindow').classList.add('show');
            }, 60);

            updateLoginButtonState();
            document.getElementById('username').addEventListener('input', updateLoginButtonState);
            document.getElementById('password').addEventListener('input', updateLoginButtonState);
        });

        function updateLoginButtonState() {
            const username = document.getElementById('username').value.trim();
            const password = document.getElementById('password').value;
            const loginBtn = document.getElementById('loginBtn');
            
            if (username && password) {
                loginBtn.disabled = false;
            } else {
                loginBtn.disabled = true;
            }
        }        async function checkExistingAuth() {
            const token = localStorage.getItem('jwt_token');
            const expiry = localStorage.getItem('jwt_expiry');

            if (token && expiry && Date.now() < parseInt(expiry)) {
                try {
                    const baseURL = window.location.origin;
                    const res = await fetch(`${baseURL}/api/user/get_self`, {
                        headers: { 'Authorization': `Bearer ${token}` }
                    });
                    
                    if (res.ok) {
                        window.location.href = '/';
                        return;
                    }
                } catch (err) {
                }
            }
            
            if (token) {
                localStorage.removeItem('jwt_token');
                localStorage.removeItem('jwt_expiry');
            }
        }

        const baseURL = window.location.origin;
        document.getElementById('loginBtn').addEventListener('click', async function () {
            const username = document.getElementById('username').value.trim();
            const password = document.getElementById('password').value;
            const errorDiv = document.getElementById('loginError');
            const passwordInput = document.getElementById('password');
            errorDiv.classList.remove('visible');
            passwordInput.classList.remove('shake');
            if (!username || !password) {
                errorDiv.textContent = "Please enter username and password.";
                errorDiv.classList.add('visible');
                passwordInput.value = '';
                passwordInput.classList.add('shake');
                setTimeout(() => passwordInput.classList.remove('shake'), 600);
                return;
            }
            try {
                const res = await fetch(`${baseURL}/api/user/login`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ username, password })
                });
                if (!res.ok) throw new Error();
                const data = await res.json();
                if (data.token) {
                    const token = data.token;
                    localStorage.setItem('jwt_token', token);
                    const expiry = Date.now() + 24 * 60 * 60 * 1000;
                    localStorage.setItem('jwt_expiry', expiry);

                    try {
                        const res = await fetch(`${baseURL}/api/user/get_self`, {
                            headers: { 'Authorization': `Bearer ${token}` }
                        });
                        if (!res.ok) throw new Error('Failed to load background');
                        const user = await res.json();
                        let settings = {};
                        try {
                            settings = JSON.parse(user.settings || '{}');
                        } catch (e) {}

                        if (settings.background) {
                            const bgPath = settings.background.replace('web/', '');
                            const newBg = `url('web/${bgPath}')`;
                            const html = document.documentElement;
                            const bgFadeOverlay = document.getElementById('bg-fade-overlay');
                            bgFadeOverlay.style.backgroundImage = newBg;
                            bgFadeOverlay.style.opacity = '0';
                            bgFadeOverlay.style.transition = 'none';
                            void bgFadeOverlay.offsetWidth;
                            bgFadeOverlay.style.transition = 'opacity 0.4s cubic-bezier(0.4,0,0.2,1)';
                            bgFadeOverlay.style.opacity = '1';
                            setTimeout(() => {
                                html.style.backgroundImage = newBg;
                                bgFadeOverlay.style.opacity = '0';
                            }, 400);
                        }
                    } catch (err) {}

                    const win = document.getElementById('loginWindow');
                    win.classList.add('login-fade-out');
                    setTimeout(() => {
                        window.location.href = '/';
                    }, 500);
                } else {
                    throw new Error();
                }
            } catch {
                errorDiv.textContent = "Invalid username or password.";
                errorDiv.classList.add('visible');
                passwordInput.value = '';
                passwordInput.classList.add('shake');
                setTimeout(() => passwordInput.classList.remove('shake'), 600);
            }
        });

        document.getElementById('password').addEventListener('keydown', function(e) {
            if (e.key === 'Enter') {
                document.getElementById('loginBtn').click();
            }
        });
        document.getElementById('username').addEventListener('keydown', function(e) {
            if (e.key === 'Enter') {
                document.getElementById('loginBtn').click();
            }
        });