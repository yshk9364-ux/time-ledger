export type Status = 'working' | 'unemployed' | 'paused';
export type Expense = {name:string; fixed?:number; ratio?:number; fallbackRatio:number; necessary:boolean};
export type Profile = {id:string; effectiveFrom:number; expenses:Expense[]; socialMode:'auto'|'manual'|'off'; socialRatio:number; socialFixed:number; fundMode:'auto'|'manual'|'off'; fundRatio:number; fundFixed:number; deduction:number; netOverride?:number; schedule:'double'|'single'|'alternate'|'custom'; hours:number; days:number};
export type Period = {id:string; type:Status; startAt:number; endAt:number|null; targetSalary:number; actualSalary:number; expenseReferenceIncome:number; company:string; jobTitle:string; countOpportunity:boolean};
export type Ledger = {extras?:{id:string;timestamp:number;amount:number;note:string}[];version:1; initialSalary:number; birthday:string; referenceAge:number; savings?:number; periods:Period[]; profiles:Profile[]; events:{id:string; timestamp:number; type:string; payload:unknown}[]};
