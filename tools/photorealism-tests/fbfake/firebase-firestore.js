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

export function onSnapshot(target, cb, err){
  const isDoc = !!target.id;
  const fire = () => {
    if (isDoc) {
      const v = S.docs.get(target.path);
      try { cb({ exists: () => v !== undefined, data: () => v,
                 metadata: { fromCache: false } }); } catch (e) {}
      return;
    }
    const docs = [...S.docs.entries()]
      .filter(([k]) => k.startsWith(target.path + '/'))
      .map(([k, v]) => ({ id: k.split('/').pop(), data: () => v, ref: { path: k } }));
    try { cb({ docs, metadata: { fromCache: false } }); } catch (e) {}
  };
  S.listeners = S.listeners || [];
  S.listeners.push(fire);
  fire();
  return () => { S.listeners = S.listeners.filter(f => f !== fire); };
}

export async function getDoc(d){
  const v = S.docs.get(d.path);
  return { exists: () => v !== undefined, data: () => v, id: d.id, ref: d };
}

// dotted field paths update one leaf without replacing the whole map
export async function updateDoc(d, patch){
  const cur = S.docs.get(d.path);
  if (cur === undefined) throw { code: 'not-found' };
  const next = { ...cur };
  for (const k in patch) {
    if (k.indexOf('.') < 0) { next[k] = patch[k]; continue; }
    const [head, ...rest] = k.split('.');
    next[head] = { ...(next[head] || {}) };
    let node = next[head];
    while (rest.length > 1) { const seg = rest.shift();
      node[seg] = { ...(node[seg] || {}) }; node = node[seg]; }
    node[rest[0]] = patch[k];
  }
  S.docs.set(d.path, next);
  (S.listeners || []).forEach(f => setTimeout(f, 0));
}
