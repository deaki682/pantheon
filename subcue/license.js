/*
 * Subcue — offline license verification
 * -------------------------------------
 * Pro keys are signed OFFLINE by the seller's private key (tools/make-license-keys.js).
 * Only the PUBLIC key is embedded here, so a pasted key verifies with Web Crypto
 * (ECDSA P-256 / SHA-256) entirely in the browser — no license server, no network,
 * no per-check cost. Works in the browser and under Node (both expose crypto.subtle).
 *
 * Key format:  SUBC-<base64url( serial[5 bytes] || signature[64 bytes] )>
 * Signed message: "subcue-pro:v1:" + serialHex
 *
 * The public key below is rewritten by make-license-keys.js.
 */
(function (root) {
  'use strict';

  var PUBLIC_JWK = /*KEY_START*/{"kty":"EC","crv":"P-256","x":"uHInGQZFALIvI0BjgYDaimagc7n6jlIbh4XBDO1XSqA","y":"96zZlzlE1xvH_N8v4DQS-9G8TNzbo7hQQnbvMZESCdU"}/*KEY_END*/;
  var PREFIX = 'SUBC';
  var MSG_PREFIX = 'subcue-pro:v1:';

  function subtle() {
    var c = (typeof crypto !== 'undefined' && crypto) ||
            (typeof globalThis !== 'undefined' && globalThis.crypto) || null;
    return c && c.subtle ? c.subtle : null;
  }
  function b64urlToBytes(s) {
    s = String(s).replace(/-/g, '+').replace(/_/g, '/');
    while (s.length % 4) s += '=';
    var bin = (typeof atob === 'function') ? atob(s) : Buffer.from(s, 'base64').toString('binary');
    var out = new Uint8Array(bin.length);
    for (var i = 0; i < bin.length; i++) out[i] = bin.charCodeAt(i);
    return out;
  }
  function toHex(bytes) {
    var h = '';
    for (var i = 0; i < bytes.length; i++) h += ('0' + bytes[i].toString(16)).slice(-2);
    return h;
  }
  function clean(raw) { return String(raw == null ? '' : raw).trim().replace(/\s+/g, ''); }

  function verify(raw, jwkOverride) {
    var key = clean(raw), s = subtle();
    if (!s) return Promise.resolve({ valid: false, reason: 'Web Crypto unavailable in this environment.' });
    if (key.slice(0, PREFIX.length + 1).toUpperCase() !== PREFIX + '-') {
      return Promise.resolve({ valid: false, reason: 'Not a valid key format.' });
    }
    var bytes;
    try { bytes = b64urlToBytes(key.slice(PREFIX.length + 1)); } catch (e) { bytes = null; }
    if (!bytes || bytes.length !== 69) return Promise.resolve({ valid: false, reason: 'Key is malformed or incomplete.' });
    var serialHex = toHex(bytes.slice(0, 5)), sig = bytes.slice(5);
    var msg = new Uint8Array(MSG_PREFIX.length + serialHex.length);
    for (var i = 0; i < MSG_PREFIX.length; i++) msg[i] = MSG_PREFIX.charCodeAt(i);
    for (var j = 0; j < serialHex.length; j++) msg[MSG_PREFIX.length + j] = serialHex.charCodeAt(j);
    return s.importKey('jwk', jwkOverride || PUBLIC_JWK, { name: 'ECDSA', namedCurve: 'P-256' }, false, ['verify'])
      .then(function (pub) { return s.verify({ name: 'ECDSA', hash: 'SHA-256' }, pub, sig, msg); })
      .then(function (okv) { return okv ? { valid: true, serial: serialHex } : { valid: false, reason: 'Key signature did not verify.' }; })
      .catch(function () { return { valid: false, reason: 'Could not verify this key.' }; });
  }

  var api = { verify: verify, PREFIX: PREFIX, MSG_PREFIX: MSG_PREFIX };
  root.SubcueLicense = api;
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
})(typeof globalThis !== 'undefined' ? globalThis : this);
