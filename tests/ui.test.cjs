// Pure UI smoke tests. Requires Node 20+; no npm install or browser needed.
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');
const src = fs.readFileSync(path.join(__dirname,'../frontend/assets/app.js'),'utf8');
const root = {innerHTML:''};
const document = {
  getElementById(id){return id==='app'?root:{innerHTML:'',append(){},querySelector(){return null}}},
  addEventListener(){}, body:{classList:{add(){},remove(){}}}
};
const context = {document,window:{addEventListener(){}},console,setTimeout,clearTimeout,
  URLSearchParams,Intl,Date,Number,Math,history:{},location:{hash:''}};
vm.createContext(context);
vm.runInContext(src.replace(/\s*init\(\);\s*$/,'')+'\nthis.TEST={esc,icon,badge,money,chartSvg,mobileCards,collectionPage,dashboardPage,state,showAuth};',context);
const {esc,icon,badge,money,chartSvg,mobileCards,collectionPage,dashboardPage,state,showAuth} = context.TEST;
state.user={id:1,role:'ADMIN',fullName:'Test Admin',email:'admin@test.example'};

test('user-generated HTML is escaped before rendering',()=>{
  assert.equal(esc('<img src=x onerror="alert(1)">'),'&lt;img src=x onerror=&quot;alert(1)&quot;&gt;');
  assert(!badge('<script>alert(1)</script>').includes('<script>'));
});
test('format Indian currency accurately',()=>{
  assert.match(money(1875000),/18,75,000/);
});
test('dashboard generates KPI, sales and chart markup',()=>{
  const content=dashboardPage({revenue:1875000,completedSales:1,available:2,vehicles:3,upcomingCount:0,pendingSales:1,
    reserved:1,sold:0,inService:0,monthlyRevenue:[{month:'Nov',revenue:1875000}],
    recentSales:[{id:1,vehicleLabel:'2025 Hyundai Creta',customerName:'Alice',invoiceNumber:'NS-123',finalAmount:1875000,status:'PENDING'}],
    upcomingDrives:[],showrooms:[]});
  assert.match(content,/Revenue overview/);
  assert.match(content,/2025 Hyundai Creta/);
  assert.match(content,/18\.75 L/);
  assert.match(content,/Pending/);
});
test('mobile cards expose complete record data and usable actions',()=>{
  const item={id:1,vin:'TESTVIN00001',year:2025,make:'Tata',model:'Nexon',variant:'Creative',showroomName:'Delhi',price:1500000,status:'AVAILABLE'};
  const mobile=mobileCards('vehicles',{items:[item]});
  assert.match(mobile,/TESTVIN00001/);
  assert.match(mobile,/Available/);
  assert.match(mobile,/data-action="edit"/);
  assert.match(mobile,/data-action="delete"/);
});
test('record names cannot insert script tags into tables',()=>{
  const item={id:1,fullName:'<script>attack()</script>',email:'person@example.com',phone:'9990000000',city:'Delhi',createdAt:'2026-11-23'};
  state.page='customers';state.query='';state.filter='';
  const html=collectionPage('customers',{items:[item],total:1,page:1,limit:12,pages:1});
  assert(!html.includes('<script>attack()'));
  assert(html.includes('&lt;script&gt;attack()&lt;/script&gt;'));
});
test('first admin setup prompts for terminal token',()=>{
  showAuth('setup');
  assert.match(root.innerHTML,/Setup token/);
  assert.match(root.innerHTML,/Create workspace/);
  assert.match(root.innerHTML,/demo_data/);
});
