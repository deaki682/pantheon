/* node license.test.js — offline license sign/verify roundtrip (ECDSA P-256). */
'use strict';
var crypto = require('crypto');
var fs = require('fs');
var path = require('path');
var L = require('./license.js');

var pass = 0, fail = 0;
function ok(cond, msg) { if (cond) { pass++; } else { fail++; console.error('FAIL: ' + msg); } }
async function okAsync(p, msg) { try { ok(await p, msg); } catch (e) { fail++; console.error('FAIL(err): ' + msg + ' — ' + e.message); } }

var PREFIX = 'ALGN';
var MSG_PREFIX = 'allergen-matrix-pro:v1:';

function b64url(buf) {
  return buf.toString('base64').replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
}
// Mint a key with a given private key (mirrors tools/make-license-keys.js).
function mint(priv) {
  var serial = crypto.randomBytes(5);
  var msg = Buffer.from(MSG_PREFIX + serial.toString('hex'), 'utf8');
  var sig = crypto.sign('sha256', msg, { key: priv, dsaEncoding: 'ieee-p1363' });
  return PREFIX + '-' + b64url(Buffer.concat([serial, sig]));
}

(async function () {
  // 1) Ephemeral keypair: full sign→verify roundtrip through license.js's verify(),
  //    injecting the matching public JWK. Proves the crypto path end to end.
  var pair = crypto.generateKeyPairSync('ec', { namedCurve: 'P-256' });
  var pub = pair.publicKey.export({ format: 'jwk' });
  var goodKey = mint(pair.privateKey);
  await okAsync(L.verify(goodKey, pub).then(function (r) { return r.valid === true; }), 'freshly-minted key verifies');

  // 2) A key from a DIFFERENT keypair must be rejected against pub.
  var other = crypto.generateKeyPairSync('ec', { namedCurve: 'P-256' });
  var foreignKey = mint(other.privateKey);
  await okAsync(L.verify(foreignKey, pub).then(function (r) { return r.valid === false; }), 'key from another keypair is rejected');

  // 3) Tampered payload (flip a char) must fail.
  var tampered = goodKey.slice(0, -1) + (goodKey.slice(-1) === 'A' ? 'B' : 'A');
  await okAsync(L.verify(tampered, pub).then(function (r) { return r.valid === false; }), 'tampered key is rejected');

  // 4) Whitespace / case tolerance on the prefix; payload survives trimming.
  await okAsync(L.verify('  ' + goodKey + '  ', pub).then(function (r) { return r.valid === true; }), 'surrounding whitespace tolerated');
  await okAsync(L.verify(goodKey.replace(/^ALGN/, 'algn'), pub).then(function (r) { return r.valid === true; }), 'lowercase prefix tolerated');

  // 5) Garbage inputs are rejected cleanly (no throw).
  await okAsync(L.verify('', pub).then(function (r) { return r.valid === false; }), 'empty string rejected');
  await okAsync(L.verify('hello world', pub).then(function (r) { return r.valid === false; }), 'non-key text rejected');
  await okAsync(L.verify('ALGN-short', pub).then(function (r) { return r.valid === false; }), 'too-short payload rejected');

  // 6) The EMBEDDED public key verifies a key from the committed keypair, IF present.
  //    (Uses tools/signing-key.json when available — i.e. right after minting locally.)
  var keyFile = path.join(__dirname, 'tools', 'signing-key.json');
  if (fs.existsSync(keyFile)) {
    var sk = JSON.parse(fs.readFileSync(keyFile, 'utf8'));
    var embeddedPriv = crypto.createPrivateKey({ key: sk.privateJwk, format: 'jwk' });
    var realKey = mint(embeddedPriv);
    await okAsync(L.verify(realKey).then(function (r) { return r.valid === true; }), 'embedded public key verifies a real minted key');
  } else {
    console.log('(skipped embedded-key check — tools/signing-key.json not present)');
  }

  console.log('\n' + pass + ' passed, ' + fail + ' failed');
  process.exit(fail ? 1 : 0);
})();
