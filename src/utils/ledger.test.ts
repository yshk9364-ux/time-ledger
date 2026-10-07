import {test} from 'node:test';
import assert from 'node:assert/strict';
import {defaults} from '../data/defaults';
import {expenses} from './expense';
import {calculate,validate} from './ledger';
import type {Ledger,Period} from '../types';
const t=(s:string)=>new Date(s+'T00:00:00').getTime();
const period=(start:string,end:string|null,type:Period['type']='unemployed'):Period=>({id:crypto.randomUUID(),startAt:t(start),endAt:end?t(end):null,type,targetSalary:6000,actualSalary:6000,expenseReferenceIncome:6000,company:'',jobTitle:'',countOpportunity:false});
const book=(periods:Period[]):Ledger=>({version:1,initialSalary:6000,birthday:'',referenceAge:80,periods,profiles:[defaults(0)],events:[]});
test('only salary produces complete finite estimates',()=>{const v=expenses(6000,defaults(0));assert.equal(v.rows.length,8);assert.ok(v.total>0&&Number.isFinite(v.remaining));assert.ok(v.rows.every(r=>r.source==='默认估算'))});
test('fixed rent wins over both ratios',()=>{const p=defaults(0);p.expenses[0].fixed=1500;p.expenses[0].ratio=.9;assert.equal(expenses(6000,p).rows[0].amount,1500)});
test('reopening ten days later reconstructs elapsed costs from timestamps',()=>{const l=book([period('2026-01-01',null)]);const restored=validate(JSON.parse(JSON.stringify(l)));const v=calculate(restored,0,t('2026-01-11'));assert.equal(v.days.unemployed,10);assert.ok(Math.abs(v.opportunity-72000*10/365)<.001);assert.ok(v.cost>0);assert.deepEqual(v,calculate(l,0,t('2026-01-11')))});
test('working and then leaving never cancels old opportunity cost',()=>{const l=book([period('2026-01-01','2026-02-01'),period('2026-02-01','2026-03-01','working'),period('2026-03-01',null)]);const early=calculate(l,0,t('2026-02-01'));const work=calculate(l,0,t('2026-03-01'));assert.equal(early.opportunity,work.opportunity);assert.ok(work.income>0);assert.ok(calculate(l,0,t('2026-04-01')).opportunity>work.opportunity)});
test('year boundaries and leap year use real year lengths',()=>{const l=book([period('2026-12-20',null)]);const a=calculate(l,0,t('2027-01-20'));assert.ok(Math.abs(a.opportunity-72000*31/365)<.001);const leap=calculate(book([period('2024-01-01',null)]),0,t('2025-01-01'));assert.ok(Math.abs(leap.opportunity-72000)<.001)});
test('new rent version does not rewrite old living cost',()=>{const l=book([period('2026-01-01',null)]);l.profiles[0].expenses[0].fixed=1500;const old=calculate(l,0,t('2027-01-01'));const next=defaults(t('2027-01-01'));next.expenses[0].fixed=2000;l.profiles.push(next);assert.deepEqual(old,calculate(l,0,t('2027-01-01')));assert.ok(calculate(l,t('2027-01-01'),t('2028-01-01')).cost>old.cost)});

test('extra income changes displayed balance without erasing opportunity history',async()=>{
  const {cashAdjustments}=await import('./cashflow');
  const l=book([period('2026-01-01',null)]);
  const before=calculate(l,0,t('2026-01-11'));
  l.extras=[{id:'old-expense',timestamp:t('2026-01-10'),amount:20,note:'旧版支出'},{id:'part-time',timestamp:t('2026-01-10'),amount:150,note:'兼职',kind:'income'},{id:'next-month',timestamp:t('2026-02-01'),amount:100,note:'其他收入',kind:'income'}];
  const restored=validate(JSON.parse(JSON.stringify(l)));
  assert.deepEqual(cashAdjustments(restored.extras!,t('2026-01-10'),t('2026-01-11')),{income:150,expense:20,net:130});
  assert.equal(calculate(restored,0,t('2026-01-11')).opportunity,before.opportunity);
  assert.equal(cashAdjustments(restored.extras!.filter(e=>e.id!=='part-time'),t('2026-01-10'),t('2026-01-11')).net,-20);
});
