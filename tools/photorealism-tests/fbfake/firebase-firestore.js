import { _S as S } from './firebase-app.js';
export function getFirestore(){ return {}; }
export function collection(db, ...p){ return { path: p.join('/') }; }
export function doc(col, id){ return { path: col.path + '/' + id, id }; }
export async function setDoc(d, v){ S.docs.set(d.path, v); S.log.push('doc ' + d.path); (S.listeners||[]).forEach(f => setTimeout(f, 0)); }
export async function getDocs(col){
  const docs = [...S.docs.entries()]
    .filter(([k]) => k.startsWith(col.path + '/'))
    .map(([k, v]) => ({ id: k.split('/').pop(), data: () => v, ref: { path: k } }));
  return { docs };
}
export async function deleteDoc(r){ S.docs.delete(r.path); }
export function serverTimestamp(){ return Date.now(); }

export function onSnapshot(col, cb, err){
  const fire = () => {
    const docs = [...S.docs.entries()]
      .filter(([k]) => k.startsWith(col.path + '/'))
      .map(([k, v]) => ({ id: k.split('/').pop(), data: () => v, ref: { path: k } }));
    try { cb({ docs, metadata: { fromCache: false } }); } catch (e) {}
  };
  S.listeners = S.listeners || [];
  S.listeners.push(fire);
  fire();
  return () => { S.listeners = S.listeners.filter(f => f !== fire); };
}
