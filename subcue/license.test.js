/* node license.test.js — offline license sign/verify roundtrip (ECDSA P-256). */
'use strict';
var crypto = require('crypto');
var fs = require('fs');
var path = require('path');
var L = require('./license.js');

var pass = 0, fail = 0;
function ok(cond, msg) { if (cond) pass++; else { fail++; console.error('FAIL: ' + msg); } }
async function okAsync(p, msg) { try { ok(await p, msg); } catch (e) { fail++; console.error('FAIL(err): ' + msg + ' — ' + e.message); } }

var PREFIX = 'SUBC', MSG_PREFIX = 'subcue-pro:v1:';
function b64url(buf) { return buf.toString('base64').replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, ''); }
function mint(priv) {
  var serial = crypto.randomBytes(5);
  var sig = crypto.sign('sha256', Buffer.from(MSG_PREFIX + serial.toString('hex'), 'utf8'), { key: priv, dsaEncoding: 'ieee-p1363' });
  return PREFIX + '-' + b64url(Buffer.concat([serial, sig]));
}

(async function () {
  var pair = crypto.generateKeyPairSync('ec', { namedCurve: 'P-256' });
  var pub = pair.publicKey.export({ format: 'jwk' });
  var goodKey = mint(pair.privateKey);
  await okAsync(L.verify(goodKey, pub).then(function (r) { return r.valid === true; }), 'freshly-minted key verifies');

  var other = crypto.generateKeyPairSync('ec', { namedCurve: 'P-256' });
  await okAsync(L.verify(mint(other.privateKey), pub).then(function (r) { return r.valid === false; }), 'foreign key rejected');

  var tampered = goodKey.slice(0, -1) + (goodKey.slice(-1) === 'A' ? 'B' : 'A');
  await okAsync(L.verify(tampered, pub).then(function (r) { return r.valid === false; }), 'tampered key rejected');

  await okAsync(L.verify('  ' + goodKey + '  ', pub).then(function (r) { return r.valid === true; }), 'whitespace tolerated');
  await okAsync(L.verify(goodKey.replace(/^SUBC/, 'subc'), pub).then(function (r) { return r.valid === true; }), 'lowercase prefix tolerated');
  await okAsync(L.verify('', pub).then(function (r) { return r.valid === false; }), 'empty rejected');
  await okAsync(L.verify('SUBC-short', pub).then(function (r) { return r.valid === false; }), 'short payload rejected');

  var keyFile = path.join(__dirname, 'tools', 'signing-key.json');
  if (fs.existsSync(keyFile)) {
    var sk = JSON.parse(fs.readFileSync(keyFile, 'utf8'));
    var embeddedPriv = crypto.createPrivateKey({ key: sk.privateJwk, format: 'jwk' });
    await okAsync(L.verify(mint(embeddedPriv)).then(function (r) { return r.valid === true; }), 'embedded public key verifies a real minted key');
  } else {
    console.log('(skipped embedded-key check — tools/signing-key.json not present)');
  }

  console.log('\n' + pass + ' passed, ' + fail + ' failed');
  process.exit(fail ? 1 : 0);
})();
