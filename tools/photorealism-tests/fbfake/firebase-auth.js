import { _S as S } from './firebase-app.js';
export function getAuth(){ return { get currentUser(){ return S.user; } }; }
export const browserLocalPersistence = 'local';
export async function setPersistence(){ }
export function onAuthStateChanged(a, cb){ S.cbs.push(cb); cb(S.user); return () => {}; }
export async function getRedirectResult(){ return null; }
export class GoogleAuthProvider { static credential(t){ return {t}; } }
export class OAuthProvider { constructor(id){ this.id = id; } addScope(){} credential(o){ return o; } }
export async function signInWithPopup(){ throw { code: 'auth/popup-blocked' }; }
export async function signInWithRedirect(){ }
export async function signInWithCredential(){ }
export async function signOut(){ S.user = null; S.cbs.forEach(c => c(null)); }
export async function deleteUser(){ S.user = null; S.cbs.forEach(c => c(null)); }

// a tiny email/password backend: enough to exercise every branch
export async function createUserWithEmailAndPassword(a, em, pw){
  S.users = S.users || {};
  if (!/.+@.+\..+/.test(em)) throw { code: 'auth/invalid-email' };
  if ((pw || '').length < 6) throw { code: 'auth/weak-password' };
  if (S.users[em]) throw { code: 'auth/email-already-in-use' };
  S.users[em] = pw;
  S.user = { uid: 'u-' + em, email: em };
  S.cbs.forEach(c => c(S.user));
  return { user: S.user };
}
export async function signInWithEmailAndPassword(a, em, pw){
  S.users = S.users || {};
  if (!/.+@.+\..+/.test(em)) throw { code: 'auth/invalid-email' };
  if (S.users[em] !== pw) throw { code: 'auth/invalid-credential' };
  S.user = { uid: 'u-' + em, email: em };
  S.cbs.forEach(c => c(S.user));
  return { user: S.user };
}
export async function sendPasswordResetEmail(a, em){
  if (!/.+@.+\..+/.test(em)) throw { code: 'auth/invalid-email' };
  S.reset = em;
}
