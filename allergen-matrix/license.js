/*
 * Menu Allergen Matrix Builder — offline license verification
 * -----------------------------------------------------------
 * Pro keys are signed OFFLINE by the seller's private key (see tools/make-license-keys.js).
 * This file embeds only the PUBLIC key, so a pasted key is verified with Web Crypto
 * (ECDSA P-256 / SHA-256) entirely in the browser — no license server, no network call,
 * no per-check cost. Works in the browser and under Node (both expose crypto.subtle).
 *
 * Key format:  ALGN-<base64url( serial[5 bytes] || signature[64 bytes] )>
 * Signed message: "allergen-matrix-pro:v1:" + serialHex
 *
 * The public key below is regenerated (and this line rewritten) by make-license-keys.js.
 */
(function (root) {
  'use strict';

  var PUBLIC_JWK = /*KEY_START*/{"kty":"EC","crv":"P-256","x":"30p2Ue_4Ww-ffwkb9bj3xWIaDarXpicVd9sUTAHwLQo","y":"WhoLynueoDa80FW0t718NXCoSyfFa8T9TIPgfkT-Vbw"}/*KEY_END*/;
  var PREFIX = 'ALGN';
  var MSG_PREFIX = 'allergen-matrix-pro:v1:';

  function subtle() {
    var c = (typeof crypto !== 'undefined' && crypto) ||
            (typeof globalThis !== 'undefined' && globalThis.crypto) || null;
    return c && c.subtle ? c.subtle : null;
  }

  function b64urlToBytes(s) {
    s = String(s).replace(/-/g, '+').replace(/_/g, '/');
    while (s.length % 4) s += '=';
    var bin = (typeof atob === 'function')
      ? atob(s)
      : Buffer.from(s, 'base64').toString('binary');
    var out = new Uint8Array(bin.length);
    for (var i = 0; i < bin.length; i++) out[i] = bin.charCodeAt(i);
    return out;
  }

  function toHex(bytes) {
    var h = '';
    for (var i = 0; i < bytes.length; i++) h += ('0' + bytes[i].toString(16)).slice(-2);
    return h;
  }

  // Normalize user input: uppercase, strip spaces; the payload part is case-sensitive
  // base64url so we only trim/space-clean, we don't uppercase the payload.
  function clean(raw) {
    return String(raw == null ? '' : raw).trim().replace(/\s+/g, '');
  }

  // Returns a Promise<{valid:boolean, serial?:string, reason?:string}>.
  // jwkOverride lets tests inject a matching key without touching the embedded one.
  function verify(raw, jwkOverride) {
    var key = clean(raw);
    var s = subtle();
    if (!s) return Promise.resolve({ valid: false, reason: 'Web Crypto unavailable in this environment.' });
    if (key.slice(0, PREFIX.length + 1).toUpperCase() !== PREFIX + '-') {
      return Promise.resolve({ valid: false, reason: 'Not a valid key format.' });
    }
    var payloadB64 = key.slice(PREFIX.length + 1);
    var bytes;
    try { bytes = b64urlToBytes(payloadB64); } catch (e) { bytes = null; }
    if (!bytes || bytes.length !== 69) {
      return Promise.resolve({ valid: false, reason: 'Key is malformed or incomplete.' });
    }
    var serial = bytes.slice(0, 5);
    var sig = bytes.slice(5); // 64 bytes, raw r||s
    var serialHex = toHex(serial);
    var msg = new Uint8Array(MSG_PREFIX.length + serialHex.length);
    for (var i = 0; i < MSG_PREFIX.length; i++) msg[i] = MSG_PREFIX.charCodeAt(i);
    for (var j = 0; j < serialHex.length; j++) msg[MSG_PREFIX.length + j] = serialHex.charCodeAt(j);

    return s.importKey('jwk', jwkOverride || PUBLIC_JWK, { name: 'ECDSA', namedCurve: 'P-256' }, false, ['verify'])
      .then(function (pub) {
        return s.verify({ name: 'ECDSA', hash: 'SHA-256' }, pub, sig, msg);
      })
      .then(function (ok) {
        return ok ? { valid: true, serial: serialHex } : { valid: false, reason: 'Key signature did not verify.' };
      })
      .catch(function () {
        return { valid: false, reason: 'Could not verify this key.' };
      });
  }

  var api = { verify: verify, PREFIX: PREFIX, MSG_PREFIX: MSG_PREFIX, _b64urlToBytes: b64urlToBytes, _toHex: toHex };
  root.AllergenLicense = api;
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
})(typeof globalThis !== 'undefined' ? globalThis : this);
