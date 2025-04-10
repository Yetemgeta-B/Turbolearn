// TurboLearn Web Application

// Initialize Vue app
const { createApp, ref, reactive, onMounted, computed, watch } = Vue;

const app = createApp({
    setup() {
        // Auth state
        const isLoggedIn = ref(false);
        const isLoggingIn = ref(false);
        const loginError = ref('');
        const username = ref('');
        const password = ref('');
        const token = ref('');
        
        // App state
        const currentTab = ref('dashboard');
        const darkMode = ref(false);
        const enableNotifications = ref(true);
        const refreshInterval = ref(30);
        
        // Data
        const accounts = ref([]);
        const proxies = ref([]);
        const sessions = ref([]);
        const activeSession = ref(null);
        const selectedSession = ref(null);
        
        // Form data
        const automationParams = reactive({
            browser: 'chrome',
            instances: 1,
            headless: false,
            use_random_proxy: false,
            proxy: '',
            use_fingerprinting: true,
            enable_error_recovery: true
        });
        
        const newProxy = ref('');
        const newUser = reactive({
            username: '',
            password: ''
        });
        
        // Computed properties
        const successRate = computed(() => {
            if (sessions.value.length === 0) return 0;
            
            const completedSessions = sessions.value.filter(s => s.status === 'completed');
            return Math.round((completedSessions.length / sessions.value.length) * 100);
        });
        
        const sessionsToday = computed(() => {
            const today = new Date();
            today.setHours(0, 0, 0, 0);
            
            return sessions.value.filter(s => {
                const sessionDate = new Date(s.created_at);
                return sessionDate >= today;
            }).length;
        });
        
        const isAutomationRunning = computed(() => {
            return activeSession.value && activeSession.value.status === 'running';
        });
        
        // Methods
        
        // Authentication
        const login = async () => {
            if (!username.value || !password.value) return;
            
            isLoggingIn.value = true;
            loginError.value = '';
            
            try {
                const response = await fetch('/api/login', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        username: username.value,
                        password: password.value
                    })
                });
                
                const data = await response.json();
                
                if (data.success) {
                    token.value = data.token;
                    isLoggedIn.value = true;
                    localStorage.setItem('auth_token', data.token);
                    localStorage.setItem('username', username.value);
                    
                    // Load initial data
                    refreshSessions();
                    refreshAccounts();
                    refreshProxies();
                    
                    // Set up auto-refresh
                    startAutoRefresh();
                } else {
                    loginError.value = data.message || 'Login failed';
                }
            } catch (error) {
                loginError.value = 'Cannot connect to server';
                console.error('Login error:', error);
            } finally {
                isLoggingIn.value = false;
            }
        };
        
        const logout = () => {
            token.value = '';
            isLoggedIn.value = false;
            localStorage.removeItem('auth_token');
            localStorage.removeItem('username');
            stopAutoRefresh();
        };
        
        const checkAuthState = () => {
            const savedToken = localStorage.getItem('auth_token');
            const savedUsername = localStorage.getItem('username');
            
            if (savedToken && savedUsername) {
                token.value = savedToken;
                username.value = savedUsername;
                isLoggedIn.value = true;
                
                // Load initial data
                refreshSessions();
                refreshAccounts();
                refreshProxies();
                
                // Set up auto-refresh
                startAutoRefresh();
            }
        };
        
        // Data refresh functions
        const refreshSessions = async () => {
            try {
                const response = await fetch('/api/sessions', {
                    headers: {
                        'Authorization': `Bearer ${token.value}`
                    }
                });
                
                const data = await response.json();
                
                if (data.success) {
                    sessions.value = data.sessions.sort((a, b) => {
                        return new Date(b.created_at) - new Date(a.created_at);
                    });
                    
                    // Update active session if any
                    const runningSession = sessions.value.find(s => s.status === 'running');
                    if (runningSession) {
                        activeSession.value = runningSession;
                    }
                    
                    // Update chart data
                    updateChart();
                }
            } catch (error) {
                console.error('Error refreshing sessions:', error);
            }
        };
        
        const refreshAccounts = async () => {
            try {
                const response = await fetch('/api/accounts', {
                    headers: {
                        'Authorization': `Bearer ${token.value}`
                    }
                });
                
                const data = await response.json();
                
                if (data.success) {
                    accounts.value = data.accounts;
                }
            } catch (error) {
                console.error('Error refreshing accounts:', error);
            }
        };
        
        const refreshProxies = async () => {
            try {
                const response = await fetch('/api/proxies', {
                    headers: {
                        'Authorization': `Bearer ${token.value}`
                    }
                });
                
                const data = await response.json();
                
                if (data.success) {
                    proxies.value = data.proxies;
                }
            } catch (error) {
                console.error('Error refreshing proxies:', error);
            }
        };
        
        // Automation functions
        const startAutomation = async () => {
            try {
                const response = await fetch('/api/start_automation', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${token.value}`
                    },
                    body: JSON.stringify(automationParams)
                });
                
                const data = await response.json();
                
                if (data.success) {
                    // Set the active session
                    const sessionId = data.session_id;
                    
                    // Get session details
                    await getSessionDetails(sessionId);
                    
                    // Start polling for updates
                    pollSessionStatus(sessionId);
                    
                    // Show notification
                    if (enableNotifications.value) {
                        showNotification('Automation Started', 'The automation process has started.');
                    }
                }
            } catch (error) {
                console.error('Error starting automation:', error);
                showNotification('Error', 'Failed to start automation.', 'error');
            }
        };
        
        const getSessionDetails = async (sessionId) => {
            try {
                const response = await fetch(`/api/session/${sessionId}`, {
                    headers: {
                        'Authorization': `Bearer ${token.value}`
                    }
                });
                
                const data = await response.json();
                
                if (data.success) {
                    activeSession.value = data.session;
                }
            } catch (error) {
                console.error('Error getting session details:', error);
            }
        };
        
        const pollSessionStatus = (sessionId) => {
            const interval = setInterval(async () => {
                await getSessionDetails(sessionId);
                
                // Stop polling if session is complete or failed
                if (activeSession.value && 
                    (activeSession.value.status === 'completed' || 
                     activeSession.value.status === 'failed')) {
                    clearInterval(interval);
                    
                    // Refresh the sessions list
                    refreshSessions();
                    
                    // Refresh accounts if successful
                    if (activeSession.value.status === 'completed') {
                        refreshAccounts();
                    }
                    
                    // Show notification
                    if (enableNotifications.value) {
                        const title = activeSession.value.status === 'completed' ? 
                                     'Automation Completed' : 'Automation Failed';
                        const body = activeSession.value.status === 'completed' ?
                                    'Account creation completed successfully.' :
                                    'There was an error during automation.';
                        const type = activeSession.value.status === 'completed' ? 'success' : 'error';
                        
                        showNotification(title, body, type);
                    }
                }
            }, 2000);
        };
        
        // Proxy management
        const addProxy = async () => {
            if (!newProxy.value) return;
            
            try {
                const response = await fetch('/api/proxies', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${token.value}`
                    },
                    body: JSON.stringify({
                        proxy: newProxy.value
                    })
                });
                
                const data = await response.json();
                
                if (data.success) {
                    newProxy.value = '';
                    refreshProxies();
                }
            } catch (error) {
                console.error('Error adding proxy:', error);
            }
        };
        
        const removeProxy = async (index) => {
            const proxyToRemove = proxies.value[index];
            
            try {
                const response = await fetch('/api/proxies', {
                    method: 'DELETE',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${token.value}`
                    },
                    body: JSON.stringify({
                        proxy: proxyToRemove
                    })
                });
                
                const data = await response.json();
                
                if (data.success) {
                    refreshProxies();
                }
            } catch (error) {
                console.error('Error removing proxy:', error);
            }
        };
        
        // User management
        const addUser = async () => {
            if (!newUser.username || !newUser.password) return;
            
            try {
                const response = await fetch('/api/users', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${token.value}`
                    },
                    body: JSON.stringify({
                        username: newUser.username,
                        password: newUser.password
                    })
                });
                
                const data = await response.json();
                
                if (data.success) {
                    newUser.username = '';
                    newUser.password = '';
                    showNotification('User Added', 'New user has been created successfully.', 'success');
                }
            } catch (error) {
                console.error('Error adding user:', error);
                showNotification('Error', 'Failed to add user.', 'error');
            }
        };
        
        // UI helpers
        const formatDate = (dateString) => {
            if (!dateString) return 'N/A';
            
            const date = new Date(dateString);
            return new Intl.DateTimeFormat('en-US', {
                year: 'numeric',
                month: 'short',
                day: 'numeric',
                hour: '2-digit',
                minute: '2-digit'
            }).format(date);
        };
        
        const getStatusBadgeClass = (status) => {
            const baseClass = 'badge';
            
            switch(status) {
                case 'running':
                    return `${baseClass} badge-running`;
                case 'completed':
                    return `${baseClass} badge-completed`;
                case 'failed':
                    return `${baseClass} badge-failed`;
                case 'initializing':
                    return `${baseClass} badge-initializing`;
                default:
                    return `${baseClass} bg-secondary`;
            }
        };
        
        const viewSession = (session) => {
            selectedSession.value = session;
            
            // Bootstrap modal
            const modal = new bootstrap.Modal(document.getElementById('sessionModal'));
            modal.show();
        };
        
        const revealPassword = (event, password) => {
            const target = event.target;
            const passwordSpan = target.previousElementSibling;
            
            if (passwordSpan.textContent === '••••••••') {
                passwordSpan.textContent = password;
                target.classList.remove('bi-eye');
                target.classList.add('bi-eye-slash');
            } else {
                passwordSpan.textContent = '••••••••';
                target.classList.remove('bi-eye-slash');
                target.classList.add('bi-eye');
            }
        };
        
        const copyAccountData = (account) => {
            const text = `Email: ${account.email}
Password: ${account.password}
First Name: ${account.first_name}
Last Name: ${account.last_name}`;
            
            navigator.clipboard.writeText(text)
                .then(() => {
                    showNotification('Copied', 'Account data copied to clipboard', 'success');
                })
                .catch(err => {
                    console.error('Failed to copy text: ', err);
                });
        };
        
        const exportAccounts = () => {
            if (accounts.value.length === 0) {
                showNotification('No Accounts', 'There are no accounts to export', 'warning');
                return;
            }
            
            const csv = [
                ['First Name', 'Last Name', 'Email', 'Password', 'Created At'].join(','),
                ...accounts.value.map(account => {
                    return [
                        `"${account.first_name}"`,
                        `"${account.last_name}"`,
                        `"${account.email}"`,
                        `"${account.password}"`,
                        `"${formatDate(account.created_at)}"`
                    ].join(',');
                })
            ].join('\n');
            
            const blob = new Blob([csv], { type: 'text/csv' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `turbolearn_accounts_${new Date().toISOString().split('T')[0]}.csv`;
            a.click();
            URL.revokeObjectURL(url);
        };
        
        const exportSessionAccounts = () => {
            if (!selectedSession.value || !selectedSession.value.result || selectedSession.value.result.length === 0) {
                return;
            }
            
            const csv = [
                ['First Name', 'Last Name', 'Email', 'Password', 'Created At'].join(','),
                ...selectedSession.value.result.map(account => {
                    return [
                        `"${account.first_name}"`,
                        `"${account.last_name}"`,
                        `"${account.email}"`,
                        `"${account.password}"`,
                        `"${formatDate(account.created_at)}"`
                    ].join(',');
                })
            ].join('\n');
            
            const blob = new Blob([csv], { type: 'text/csv' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `turbolearn_session_${selectedSession.value.id.substring(0, 8)}.csv`;
            a.click();
            URL.revokeObjectURL(url);
        };
        
        // Notifications
        const showNotification = (title, message, type = 'info') => {
            // Browser notification
            if (enableNotifications.value && "Notification" in window) {
                if (Notification.permission === "granted") {
                    new Notification(title, {
                        body: message,
                        icon: '/static/img/logo.png'
                    });
                } else if (Notification.permission !== "denied") {
                    Notification.requestPermission().then(permission => {
                        if (permission === "granted") {
                            new Notification(title, {
                                body: message,
                                icon: '/static/img/logo.png'
                            });
                        }
                    });
                }
            }
            
            // You could also implement an in-app toast notification here
        };
        
        // Auto-refresh
        let refreshTimer = null;
        
        const startAutoRefresh = () => {
            stopAutoRefresh(); // Clear any existing timer
            
            refreshTimer = setInterval(() => {
                if (isLoggedIn.value) {
                    refreshSessions();
                    
                    // Refresh accounts less frequently
                    if (Math.random() < 0.3) {
                        refreshAccounts();
                    }
                }
            }, refreshInterval.value * 1000);
        };
        
        const stopAutoRefresh = () => {
            if (refreshTimer) {
                clearInterval(refreshTimer);
                refreshTimer = null;
            }
        };
        
        // Chart
        let statsChart = null;
        
        const initChart = () => {
            const ctx = document.getElementById('statsChart');
            if (!ctx) return;
            
            statsChart = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: [],
                    datasets: [{
                        label: 'Accounts Created',
                        data: [],
                        borderColor: '#3a7ebf',
                        backgroundColor: 'rgba(58, 126, 191, 0.2)',
                        tension: 0.3,
                        fill: true
                    }]
                },
                options: {
                    responsive: true,
                    plugins: {
                        legend: {
                            position: 'top',
                        },
                        title: {
                            display: false
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            precision: 0
                        }
                    }
                }
            });
        };
        
        const updateChart = () => {
            if (!statsChart) {
                initChart();
                if (!statsChart) return;
            }
            
            // Group sessions by day
            const sessionsByDay = {};
            sessions.value.forEach(session => {
                if (session.status === 'completed' && session.result) {
                    const date = new Date(session.created_at);
                    const day = date.toISOString().split('T')[0];
                    
                    if (!sessionsByDay[day]) {
                        sessionsByDay[day] = 0;
                    }
                    
                    sessionsByDay[day] += session.result.length;
                }
            });
            
            // Sort by date
            const sortedDays = Object.keys(sessionsByDay).sort();
            
            // Limit to last 7 days
            const recentDays = sortedDays.slice(-7);
            
            // Format labels
            const labels = recentDays.map(day => {
                const date = new Date(day);
                return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
            });
            
            // Update chart
            statsChart.data.labels = labels;
            statsChart.data.datasets[0].data = recentDays.map(day => sessionsByDay[day]);
            statsChart.update();
        };
        
        // Dark mode toggle
        watch(darkMode, (newValue) => {
            if (newValue) {
                document.body.classList.add('dark-mode');
                localStorage.setItem('darkMode', 'true');
            } else {
                document.body.classList.remove('dark-mode');
                localStorage.setItem('darkMode', 'false');
            }
        });
        
        // Watch refresh interval changes
        watch(refreshInterval, (newValue) => {
            localStorage.setItem('refreshInterval', newValue.toString());
            startAutoRefresh();
        });
        
        // Watch notifications setting
        watch(enableNotifications, (newValue) => {
            localStorage.setItem('enableNotifications', newValue.toString());
            
            if (newValue && "Notification" in window && Notification.permission !== "granted" && Notification.permission !== "denied") {
                Notification.requestPermission();
            }
        });
        
        // Lifecycle hooks
        onMounted(() => {
            // Load settings from localStorage
            const savedDarkMode = localStorage.getItem('darkMode');
            if (savedDarkMode) {
                darkMode.value = savedDarkMode === 'true';
            } else {
                // Check if user prefers dark mode
                darkMode.value = window.matchMedia('(prefers-color-scheme: dark)').matches;
            }
            
            const savedRefreshInterval = localStorage.getItem('refreshInterval');
            if (savedRefreshInterval) {
                refreshInterval.value = parseInt(savedRefreshInterval);
            }
            
            const savedEnableNotifications = localStorage.getItem('enableNotifications');
            if (savedEnableNotifications) {
                enableNotifications.value = savedEnableNotifications === 'true';
            }
            
            // Apply dark mode
            if (darkMode.value) {
                document.body.classList.add('dark-mode');
            }
            
            // Initialize chart
            initChart();
            
            // Check authentication state
            checkAuthState();
            
            // Request notification permission if enabled
            if (enableNotifications.value && "Notification" in window && Notification.permission !== "granted" && Notification.permission !== "denied") {
                Notification.requestPermission();
            }
        });
        
        return {
            // Auth
            isLoggedIn,
            isLoggingIn,
            loginError,
            username,
            password,
            login,
            logout,
            
            // App State
            currentTab,
            darkMode,
            enableNotifications,
            refreshInterval,
            
            // Data
            accounts,
            proxies,
            sessions,
            activeSession,
            selectedSession,
            
            // Computed
            successRate,
            sessionsToday,
            isAutomationRunning,
            
            // Form data
            automationParams,
            newProxy,
            newUser,
            
            // Methods
            startAutomation,
            refreshSessions,
            refreshAccounts,
            addProxy,
            removeProxy,
            addUser,
            formatDate,
            getStatusBadgeClass,
            viewSession,
            revealPassword,
            copyAccountData,
            exportAccounts,
            exportSessionAccounts
        };
    }
});

// Mount the app
app.mount('#app'); 