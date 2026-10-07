import type {Ledger} from '../types';
export function cashAdjustments(entries:NonNullable<Ledger['extras']>,from:number,to:number){
  let income=0,expense=0;
  for(const entry of entries){
    if(entry.timestamp<from||entry.timestamp>to)continue;
    if(entry.kind==='income')income+=entry.amount;
    else expense+=entry.amount;
  }
  return {income,expense,net:income-expense};
}
