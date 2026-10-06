import type {Ledger} from '../types';
import {validate} from '../utils/ledger';
const KEY='time-ledger-v1';
export function read():Ledger|null{const raw=localStorage.getItem(KEY);if(!raw)return null;return validate(JSON.parse(raw))}
export function save(l:Ledger){validate(l);localStorage.setItem(KEY,JSON.stringify(l))}
export function reset(){localStorage.removeItem(KEY)}
