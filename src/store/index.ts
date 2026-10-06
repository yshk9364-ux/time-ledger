import type {Ledger} from '../types';
import {validate} from '../utils/ledger';
const KEY='time-ledger-v1';
export const online= !['localhost','127.0.0.1',''].includes(location.hostname);
export const apiRoot=new URL('./api/',location.href).pathname;
let cached:Ledger|null=null;let revision=0;
export async function request(path:string,options:RequestInit={}){const response=await fetch(apiRoot+path,{...options,credentials:'same-origin',headers:{'Content-Type':'application/json',...options.headers}});const data=await response.json();if(!response.ok)throw Error(data.error||'服务器连接失败');return data}
export async function loadOnline(){const result=await request('ledger');cached=result.data?validate(result.data):null;revision=result.revision}
export function read():Ledger|null{if(online)return cached;const raw=localStorage.getItem(KEY);return raw?validate(JSON.parse(raw)):null}
export function readLocal():Ledger|null{try{const raw=localStorage.getItem(KEY);return raw?validate(JSON.parse(raw)):null}catch{return null}}
export async function save(l:Ledger){validate(l);if(online){const expected=revision;const response=await request('ledger',{method:'PUT',body:JSON.stringify({data:l,revision:expected})});cached=l;revision=response.revision}else localStorage.setItem(KEY,JSON.stringify(l))}
export function reset(){if(!online)localStorage.removeItem(KEY)}
