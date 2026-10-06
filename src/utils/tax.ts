import {taxBrackets} from '../data/defaults';
export function cumulativeTax(taxable:number){const n=Math.max(0,taxable);const [,rate,quick]=taxBrackets.find(([limit])=>n<=limit)!;return Math.max(0,n*rate-quick)}
