window.CONFIG = window.CONFIG || {};
(function() {
    var defaultApi = 'http://127.0.0.1:5000/api';
    try {
        if (typeof window !== 'undefined' && window.location && window.location.protocol.startsWith('http')) {
            if (window.location.hostname !== '127.0.0.1' && window.location.hostname !== 'localhost') {
                defaultApi = window.location.origin + '/api';
            }
        }
    } catch(e){}
    window.CONFIG.API_BASE = defaultApi;
    window.CONFIG.TOKEN_KEY = 'dabba_restaurant_token';
})();
var CONFIG = window.CONFIG;
