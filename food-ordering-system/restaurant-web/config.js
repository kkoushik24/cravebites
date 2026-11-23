window.CONFIG = window.CONFIG || {};
(function() {
    var originApi = 'https://cravebites-j9yh.onrender.com/api';
    try {
        if (typeof window !== 'undefined' && window.location && window.location.protocol.startsWith('http')) {
            originApi = window.location.origin + '/api';
        }
    } catch(e){}
    window.CONFIG.API_BASE = originApi;
    window.CONFIG.TOKEN_KEY = 'dabba_restaurant_token';
})();
var CONFIG = window.CONFIG;
