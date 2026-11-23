window.CONFIG = window.CONFIG || {};
(function() {
    var savedApi = null;
    try { savedApi = localStorage.getItem('cravebites_api_base'); } catch(e){}
    var originApi = '';
    try {
        if (typeof window !== 'undefined' && window.location && window.location.protocol.startsWith('http') && !window.location.pathname.includes('/android_asset/')) {
            originApi = window.location.origin + '/api';
        }
    } catch(e){}
    window.CONFIG.API_BASE = savedApi || originApi || 'https://cravebites-j9yh.onrender.com/api';
    window.CONFIG.TOKEN_KEY = 'dabba_customer_token';
})();
var CONFIG = window.CONFIG;
