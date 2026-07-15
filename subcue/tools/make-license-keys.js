/*
 * make-license-keys.js — offline license-key mint for Subcue Pro
 * -------------------------------------------------------------
 * Generates an ECDSA P-256 keypair (once) and signs a batch of license keys with it.
 * The PRIVATE key never leaves your machine; only the PUBLIC key is baked into
 * license.js, so keys verify entirely in the buyer's browser — no license server.
 *
 *   node tools/make-license-keys.js [count]     # default 50
 *
 * Outputs (under tools/):
 *   signing-key.json   the keypair — PRIVATE, gitignored. Back it up; guard it.
 *   license-keys.csv   the batch of keys — upload to Payhip / Gumroad / Lemon Squeezy.
 *   public-key.json    the public JWK (reference).
 * It also rewrites the PUBLIC_JWK line inside ../license.js in place.
 *
 * Key format:  SUBC-<base64url( serial[5] || signature[64] )>
 * Signed message: "subcue-pro:v1:" + serialHex
 *
 * If you generate a NEW keypair (delete signing-key.json), every key you previously
 * sold stops verifying. Keep signing-key.json safe and reuse it to mint more keys.
 */
'use strict';
var crypto = require('crypto');
var fs = require('fs');
var path = require('path');

var COUNT = Math.max(1, parseInt(process.argv[2] || '50', 10) || 50);
var HERE = __dirname;
var KEY_FILE = path.join(HERE, 'signing-key.json');
var CSV_FILE = path.join(HERE, 'license-keys.csv');
var PUB_FILE = path.join(HERE, 'public-key.json');
var LICENSE_JS = path.join(HERE, '..', 'license.js');

var PREFIX = 'SUBC';
var MSG_PREFIX = 'subcue-pro:v1:';

function b64url(buf) { return buf.toString('base64').replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, ''); }

var priv, publicJwk;
if (fs.existsSync(KEY_FILE)) {
  var saved = JSON.parse(fs.readFileSync(KEY_FILE, 'utf8'));
  priv = crypto.createPrivateKey({ key: saved.privateJwk, format: 'jwk' });
  publicJwk = saved.publicJwk;
  console.log('Reusing existing signing key (' + KEY_FILE + ').');
} else {
  var pair = crypto.generateKeyPairSync('ec', { namedCurve: 'P-256' });
  priv = pair.privateKey;
  publicJwk = pair.publicKey.export({ format: 'jwk' });
  fs.writeFileSync(KEY_FILE, JSON.stringify({ privateJwk: priv.export({ format: 'jwk' }), publicJwk: publicJwk }, null, 2));
  console.log('Generated a NEW signing key → ' + KEY_FILE + '  (PRIVATE — keep it safe, it is gitignored)');
}

function mint() {
  var serial = crypto.randomBytes(5);
  var msg = Buffer.from(MSG_PREFIX + serial.toString('hex'), 'utf8');
  var sig = crypto.sign('sha256', msg, { key: priv, dsaEncoding: 'ieee-p1363' });
  return PREFIX + '-' + b64url(Buffer.concat([serial, sig]));
}

var keys = [], seen = {};
while (keys.length < COUNT) { var k = mint(); if (seen[k]) continue; seen[k] = 1; keys.push(k); }

fs.writeFileSync(CSV_FILE, keys.join('\n') + '\n');
fs.writeFileSync(PUB_FILE, JSON.stringify(publicJwk, null, 2) + '\n');

var minimalPub = { kty: publicJwk.kty, crv: publicJwk.crv, x: publicJwk.x, y: publicJwk.y };
var src = fs.readFileSync(LICENSE_JS, 'utf8');
var patched = src.replace(/\/\*KEY_START\*\/[\s\S]*?\/\*KEY_END\*\//,
  '/*KEY_START*/' + JSON.stringify(minimalPub) + '/*KEY_END*/');
if (patched === src) console.warn('WARNING: could not find KEY_START/KEY_END markers in license.js — public key NOT updated.');
else { fs.writeFileSync(LICENSE_JS, patched); console.log('Embedded public key into ' + path.relative(path.join(HERE, '..'), LICENSE_JS) + '.'); }

console.log('Minted ' + keys.length + ' license keys → ' + CSV_FILE);
console.log('Sample key: ' + keys[0]);
console.log('\nNext: upload license-keys.csv to your checkout (Payhip → product → License keys → import).');
