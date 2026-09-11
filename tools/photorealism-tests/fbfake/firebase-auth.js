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
