export const DAY=86400000;
export function yearBounds(year:number){return [new Date(year,0,1).getTime(),new Date(year+1,0,1).getTime()]}
export function duration(ms:number){let s=Math.max(0,Math.floor(ms/1000));const d=Math.floor(s/86400);s%=86400;const h=Math.floor(s/3600);s%=3600;return `${d} 天 ${h} 时 ${Math.floor(s/60)} 分 ${s%60} 秒`}
export function dateInput(t:number){const d=new Date(t);return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}`}
export function range(kind:string,now:number):[number,number]{const d=new Date(now);if(kind==='全部')return [0,now];if(kind==='今年')return [new Date(d.getFullYear(),0,1).getTime(),now];if(kind==='本月')return [new Date(d.getFullYear(),d.getMonth(),1).getTime(),now];d.setHours(0,0,0,0);if(kind==='本周')d.setDate(d.getDate()-(d.getDay()+6)%7);return [d.getTime(),now]}
