import { _S as S } from './firebase-app.js';
export function getStorage(){ return {}; }
export function ref(st, path){ return { path }; }
export async function uploadBytes(r, blob){ S.objects.set(r.path, blob); S.log.push('up ' + r.path + ' ' + blob.size); return {}; }
export async function getDownloadURL(r){
  const b = S.objects.get(r.path);
  if (!b) throw { code: 'storage/object-not-found' };
  return URL.createObjectURL(b);
}
export async function deleteObject(r){ S.objects.delete(r.path); S.log.push('del ' + r.path); }
export async function listAll(r){
  const items = [...S.objects.keys()].filter(k => k.startsWith(r.path)).map(path => ({ path }));
  return { items, prefixes: [] };
}
