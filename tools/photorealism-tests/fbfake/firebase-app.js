const S = (globalThis.__FAKE ||= { objects:new Map(), docs:new Map(), cbs:[], user:null, log:[] });
export function initializeApp(cfg){ S.cfg = cfg; return { options: cfg }; }
export { S as _S };
