window.CONFIG = window.CONFIG || {};
(function() {
    var savedApi = null;
    try { savedApi = localStorage.getItem('cravebites_rider_api_base'); } catch(e){}
    var originApi = '';
    try {
        if (typeof window !== 'undefined' && window.location && window.location.protocol.startsWith('http') && !window.location.pathname.includes('/android_asset/')) {
            originApi = window.location.origin + '/api';
        }
    } catch(e){}
    window.CONFIG.API_BASE = savedApi || originApi || window.CONFIG.API_BASE || 'https://late-proudly-agenda-monsters.trycloudflare.com/api';
    window.CONFIG.TOKEN_KEY = 'dabba_delivery_token';
})();
var CONFIG = window.CONFIG;
