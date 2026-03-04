/**
 * request-guard.js — Prevents double-submit and shows loading overlay.
 *
 * Usage:
 *   guardedFetch(url, options)          — drop-in fetch() replacement
 *   guardedAction(key, asyncFn)         — wrap any async action with a key
 *
 * Both prevent concurrent calls with the same key/url, show a loading
 * overlay while in-flight, and guarantee the overlay is removed on
 * success or failure.
 */
(function () {
    'use strict';

    var _inflight = {};

    // ── Overlay ──────────────────────────────────────────────────────────
    var _overlay = null;

    function _ensureOverlay() {
        if (_overlay) return _overlay;
        _overlay = document.createElement('div');
        _overlay.id = 'rg-overlay';
        _overlay.innerHTML =
            '<div style="display:flex;align-items:center;gap:8px;background:#1e293b;color:#fff;' +
            'padding:10px 24px;border-radius:9999px;font-size:14px;font-weight:500;' +
            'box-shadow:0 10px 25px rgba(0,0,0,.25)">' +
            '<svg width="20" height="20" viewBox="0 0 24 24" style="animation:rg-spin .7s linear infinite">' +
            '<circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="3" fill="none" ' +
            'stroke-dasharray="31.4 31.4" stroke-linecap="round"/></svg>' +
            'Processando\u2026</div>';
        _overlay.style.cssText =
            'position:fixed;inset:0;z-index:9999;display:none;align-items:flex-start;' +
            'justify-content:center;padding-top:72px;background:rgba(15,23,42,.18);' +
            'backdrop-filter:blur(2px);transition:opacity .2s';

        var style = document.createElement('style');
        style.textContent = '@keyframes rg-spin{to{transform:rotate(360deg)}}';
        document.head.appendChild(style);
        document.body.appendChild(_overlay);
        return _overlay;
    }

    function _showOverlay() {
        var o = _ensureOverlay();
        o.style.display = 'flex';
        o.style.opacity = '1';
    }

    function _hideOverlay() {
        // Only hide if no requests are in-flight
        for (var k in _inflight) {
            if (_inflight[k]) return;
        }
        if (_overlay) {
            _overlay.style.opacity = '0';
            setTimeout(function () { _overlay.style.display = 'none'; }, 200);
        }
    }

    // ── Public API ───────────────────────────────────────────────────────

    /**
     * Drop-in replacement for fetch() that prevents concurrent duplicate
     * requests to the same URL+method.
     */
    window.guardedFetch = function (url, opts) {
        opts = opts || {};
        var key = (opts.method || 'GET').toUpperCase() + ' ' + url;

        if (_inflight[key]) {
            // Already in-flight — silently ignore
            return Promise.resolve(null);
        }

        _inflight[key] = true;
        _showOverlay();

        return fetch(url, opts)
            .then(function (res) {
                _inflight[key] = false;
                _hideOverlay();
                return res;
            })
            .catch(function (err) {
                _inflight[key] = false;
                _hideOverlay();
                if (typeof showToast === 'function') {
                    showToast('Erro de conexão. Tente novamente.', true);
                }
                throw err;
            });
    };

    /**
     * Wrap any async action with a named key to prevent double-trigger.
     * Returns null if the action is already running.
     *
     *   guardedAction('save-unit', async () => { ... })
     */
    window.guardedAction = function (key, fn) {
        if (_inflight[key]) return Promise.resolve(null);
        _inflight[key] = true;
        _showOverlay();

        return Promise.resolve()
            .then(fn)
            .then(function (result) {
                _inflight[key] = false;
                _hideOverlay();
                return result;
            })
            .catch(function (err) {
                _inflight[key] = false;
                _hideOverlay();
                throw err;
            });
    };
})();
