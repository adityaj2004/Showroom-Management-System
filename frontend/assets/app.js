/* Northstar UI — zero build step, no browser storage of session tokens. */
const root = document.getElementById('app');
const toastRegion = document.getElementById('toast-region');
const state = {user:null, csrf:null, page:'dashboard', data:null, query:'', filter:'', showroomFilter:'', pageNo:1, loading:false, modal:null, sidebar:false, pending:false};
const ICONS = {
  grid:'<rect x="3" y="3" width="7" height="7" rx="1.5"/><rect x="14" y="3" width="7" height="7" rx="1.5"/><rect x="3" y="14" width="7" height="7" rx="1.5"/><rect x="14" y="14" width="7" height="7" rx="1.5"/>',
  car:'<path d="M5 17H3v-5l2-6h14l2 6v5h-2"/><path d="M5 17h14M5 17v2h3v-2m8 0v2h3v-2M4 12h16"/><circle cx="7" cy="14" r="1"/><circle cx="17" cy="14" r="1"/>',
  users:'<path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M20 21v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75"/>',
  receipt:'<path d="M4 3v18l4-2 4 2 4-2 4 2V3l-4 2-4-2-4 2-4-2Z"/><path d="M8 10h8M8 14h5"/>',
  calendar:'<rect x="3" y="5" width="18" height="16" rx="2"/><path d="M16 3v4M8 3v4M3 10h18M8 14h.01M12 14h.01"/>',
  building:'<rect x="4" y="3" width="16" height="18" rx="2"/><path d="M9 21v-5h6v5M8 8h.01M12 8h.01M16 8h.01M8 12h.01M12 12h.01M16 12h.01"/>',
  shield:'<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10Z"/><path d="m9 12 2 2 4-4"/>',
  settings:'<circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06-1.8 1.8-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.52V20h-2.5v-.1a1.65 1.65 0 0 0-1.08-1.57 1.65 1.65 0 0 0-1.82.33l-.06.06-1.8-1.8.06-.06A1.65 1.65 0 0 0 8.23 15a1.65 1.65 0 0 0-1.52-1H6v-2.5h.71A1.65 1.65 0 0 0 8.23 10a1.65 1.65 0 0 0-.33-1.82l-.06-.06 1.8-1.8.06.06A1.65 1.65 0 0 0 11.52 7a1.65 1.65 0 0 0 1-1.52V5h2.5v.48A1.65 1.65 0 0 0 16 7a1.65 1.65 0 0 0 1.82-.33l.06-.06 1.8 1.8-.06.06A1.65 1.65 0 0 0 19.4 10a1.65 1.65 0 0 0 1.52 1H21v2.5h-.08A1.65 1.65 0 0 0 19.4 15Z"/>',
  search:'<circle cx="11" cy="11" r="7"/><path d="m20 20-4-4"/>',
  plus:'<path d="M12 5v14M5 12h14"/>',
  arrow:'<path d="M5 12h14M13 6l6 6-6 6"/>',
  chevron:'<path d="m9 18 6-6-6-6"/>',
  down:'<path d="m6 9 6 6 6-6"/>',
  up:'<path d="m6 15 6-6 6 6"/>',
  bell:'<path d="M18 8a6 6 0 0 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9M10 21h4"/>',
  logout:'<path d="M10 17l5-5-5-5M15 12H3M12 3h6a3 3 0 0 1 3 3v12a3 3 0 0 1-3 3h-6"/>',
  edit:'<path d="m15 5 4 4M4 20l4.5-1 11-11a2.83 2.83 0 0 0-4-4l-11 11L4 20Z"/>',
  trash:'<path d="M3 6h18M8 6V4h8v2m3 0-1 15H6L5 6M10 10v7M14 10v7"/>',
  check:'<path d="m4 12 5 5L20 6"/>',
  x:'<path d="M18 6 6 18M6 6l12 12"/>',
  clock:'<circle cx="12" cy="12" r="9"/><path d="M12 7v5l4 2"/>',
  trend:'<path d="m3 17 6-6 4 4 8-8M15 7h6v6"/>',
  money:'<rect x="2" y="5" width="20" height="14" rx="2"/><circle cx="12" cy="12" r="3"/><path d="M6 9h.01M18 15h.01"/>',
  filter:'<path d="M4 7h16M7 12h10M10 17h4"/>',
  menu:'<path d="M4 6h16M4 12h16M4 18h16"/>',
  more:'<circle cx="5" cy="12" r="1"/><circle cx="12" cy="12" r="1"/><circle cx="19" cy="12" r="1"/>',
  location:'<path d="M20 10c0 5-8 12-8 12S4 15 4 10a8 8 0 1 1 16 0Z"/><circle cx="12" cy="10" r="2"/>',
  alert:'<circle cx="12" cy="12" r="9"/><path d="M12 8v4M12 16h.01"/>',
  download:'<path d="M12 3v12m-4-4 4 4 4-4M4 17v4h16v-4"/>',
  sparkles:'<path d="m12 3 2 6 6 2-6 2-2 6-2-6-6-2 6-2 2-6ZM19 18l1 2 2 1-2 1-1 2-1-2-2-1 2-1 1-2Z"/>',
  chart:'<path d="M4 20V4M4 20h16M8 16l4-6 4 3 4-8"/>',
  activity:'<path d="M3 12h4l3-8 4 16 3-8h4"/>',
  lock:'<rect x="4" y="10" width="16" height="11" rx="2"/><path d="M8 10V7a4 4 0 0 1 8 0v3"/>'
};
const icon = (name,size=18) => `<svg class="ic" width="${size}" height="${size}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${ICONS[name]||ICONS.grid}</svg>`;
const esc = v => String(v ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const money = v => new Intl.NumberFormat('en-IN',{style:'currency',currency:'INR',maximumFractionDigits:0}).format(Number(v)||0);
const compactMoney = v => { const n=Number(v)||0; return n>=1e7?`₹${(n/1e7).toFixed(2)} Cr`:n>=1e5?`₹${(n/1e5).toFixed(2)} L`:money(n); };
const when = d => d ? new Date(d).toLocaleString('en-IN',{day:'2-digit',month:'short',year:'numeric',hour:'numeric',minute:'2-digit'}):'—';
const shortDate = d => d ? new Date(d).toLocaleDateString('en-IN',{day:'2-digit',month:'short',year:'numeric'}):'—';
const initials = s => String(s||'N').split(/\s+/).slice(0,2).map(v=>v[0]).join('').toUpperCase();
const titleCase = s => String(s||'').replaceAll('_',' ').toLowerCase().replace(/\b\w/g,c=>c.toUpperCase());
const badge = s => `<span class="badge ${String(s||'').toLowerCase().replaceAll('_','-').replace(/[^a-z0-9-]/g,'')}"><span class="badge-dot"></span>${esc(titleCase(s))}</span>`;
const btn = (label, action, variant='primary', extra='') => `<button type="button" class="btn btn-${variant}" data-action="${esc(action)}" ${extra}>${label}</button>`;
const canManage = () => ['ADMIN','MANAGER'].includes(state.user?.role);
const isAdmin = () => state.user?.role === 'ADMIN';
const NAV = [
  ['dashboard','Overview','grid'],['vehicles','Inventory','car'],['customers','Customers','users'],
  ['sales','Sales & orders','receipt'],['test-drives','Test drives','calendar'],
  ['showrooms','Showrooms','building'],['users','Team members','shield'],['audit','Activity log','activity'],
];
const NAMES = {dashboard:'Dashboard',vehicles:'Vehicle inventory',customers:'Customers',sales:'Sales & orders',
  'test-drives':'Test drives',showrooms:'Showrooms',users:'Team members',audit:'Activity log',profile:'My profile'};
const DESCS = {vehicles:'Manage vehicles and availability across locations.',customers:'Everything you need to know about your customers.',
  sales:'Track deals from reservation through final approval.',
  'test-drives':'Coordinate appointments, visits and customer feedback.',
  showrooms:'Your dealership locations in one place.', users:'Manage your team and their access permissions.',
  audit:'A record of business changes and important actions.'};
const asLocalInput = date => {const d=new Date(date);return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}T${String(d.getHours()).padStart(2,'0')}:${String(d.getMinutes()).padStart(2,'0')}`};
const nowInput = () => {const d=new Date(Date.now()+24*60*60*1000);d.setMinutes(0,0,0);return asLocalInput(d);};
const todayInput = () => new Date().toLocaleDateString('en-CA');

async function api(url, method='GET', body=undefined){
  const res = await fetch(url,{method,credentials:'same-origin',headers:{...((body!==undefined)?{'Content-Type':'application/json'}:{}),...(!['GET','HEAD'].includes(method)&&state.csrf?{'X-CSRF-Token':state.csrf}:{})},body:body===undefined?undefined:JSON.stringify(body)});
  let content={}; try{content=await res.json()}catch{}
  if(!res.ok){
    if(res.status===401&&state.user){state.user=null;state.csrf=null;showAuth('login');}
    let e=new Error(content.message||`Request failed (${res.status})`);
    e.fields=content.errors; throw e;
  }
  return content;
}
function notify(message,type='success'){
  const id=String(Date.now())+String(Math.random());
  const el=document.createElement('div');el.className=`toast ${type}`;el.dataset.id=id;
  el.innerHTML=`${icon(type==='success'?'check':'alert',17)}<span>${esc(message)}</span>`;
  toastRegion.append(el); setTimeout(()=>el.remove(),4800);
}
function displayError(e){let message=e.message||'Something went wrong';if(e.fields?.length) message+=`: ${e.fields.map(x=>`${x.field}: ${x.message}`).join('; ')}`;notify(message,'error');}

function brand(){return `<span class="brand-mark"><span>N</span><span class="brand-star">✦</span></span><span class="brand-text">northstar<small>SHOWROOM OS</small></span>`}
function showAuth(mode='login'){
  state.page='auth'; state.data=null;
  const setup=mode==='setup'; const register=mode==='register';
  root.innerHTML=`<main class="auth-shell"><section class="auth-aside">
    <div class="auth-brand">${brand()}</div>
    <div class="auth-showcase"><div class="auth-overline">YOUR SHOWROOM. SIMPLIFIED.</div>
      <h1>Better decisions.<br><em>Every day.</em></h1>
      <p>One seamless workspace for your vehicles, customers, sales and team. Everything moving in the right direction.</p>
      <div class="auth-mock"><div class="mock-top"><span class="mock-pill"></span><span>Monthly performance</span><span>↗</span></div>
        <div class="mock-value">₹ 84.6 L <span>+18.2% this month</span></div>
        <svg viewBox="0 0 420 130" preserveAspectRatio="none" role="img" aria-label="Decorative rising performance chart"><defs><linearGradient id="authfill" x1="0" y1="0" x2="0" y2="1"><stop stop-color="#8b91ff" stop-opacity=".55"/><stop offset="1" stop-color="#8b91ff" stop-opacity="0"/></linearGradient></defs><path fill="url(#authfill)" d="M0 116 C40 100 50 110 90 81S145 103 181 75 223 61 265 62 316 18 355 30 396 8 420 13 V130H0Z"/><path fill="none" stroke="#a4a8ff" stroke-width="3.5" d="M0 116 C40 100 50 110 90 81S145 103 181 75 223 61 265 62 316 18 355 30 396 8 420 13"/></svg>
      </div>
    </div>
    <div class="auth-foot">Thoughtfully built for ambitious automotive teams. <span>© 2026 Northstar</span></div>
  </section><section class="auth-main"><div class="auth-mobile-brand">${brand()}</div><div class="auth-form-wrap">
    <div class="auth-eyebrow">${setup?'INITIAL WORKSPACE SETUP':register?'JOIN YOUR WORKSPACE':'WELCOME BACK'}</div>
    <h2>${setup?'Create your workspace':register?'Create an account':'Sign in to Northstar'}</h2>
    <p class="auth-desc">${setup?'This one-time step creates your secure administrator account.':register?'A team account gives you access to your showroom.':'Enter your credentials to access your workspace.'}</p>
    <form id="auth-form" data-mode="${mode}">
      ${setup?`<label>Setup token <input name="token" type="text" required placeholder="Paste the code from your terminal" autocomplete="off"></label>`:''}
      ${setup||register?`<label>Full name <input name="full_name" required minlength="2" maxlength="120" placeholder="e.g. Alex Morgan" autocomplete="name"></label>`:''}
      <label>Work email <input type="email" name="email" required placeholder="you@company.com" autocomplete="email"></label>
      <label>Password <input name="password" type="password" required ${setup||register?'minlength="12"':''} placeholder="${setup?'Create a strong password':'Enter your password'}" autocomplete="${setup||register?'new-password':'current-password'}"></label>
      ${setup?`<label class="check-label"><input type="checkbox" name="demo_data" checked><span>Start with realistic demo data to explore the app</span></label>`:''}
      ${setup||register?'<p class="password-hint">Use at least 12 characters, including uppercase, lowercase and a number.</p>':''}
      <button class="btn btn-primary auth-submit" type="submit">${setup?'Create workspace':register?'Create account':'Sign in'} ${icon('arrow',18)}</button>
    </form>
    ${!setup?`<div class="auth-helper">${register?'Already have an account? <a href="#/login">Sign in</a>':state.registrationEnabled?'New to the team? <a href="#/register">Create an account</a>':'Access is managed by your administrator.'}</div>`:''}
    <div class="auth-security">${icon('lock',16)} Your workspace is protected with secure sessions and role-based access.</div>
  </div></section></main>`;
}
async function init(){
  try{
    const me=await api('/api/auth/me');state.user=me.user;state.csrf=me.csrfToken;
    let page=location.hash.replace('#/','')||'dashboard';
    await go(page,false);
  }catch{
    try{const setup=await api('/api/setup-status');state.registrationEnabled=setup.registrationEnabled;showAuth(setup.needsSetup?'setup':'login');}
    catch{root.innerHTML='<div class="fatal-error">Unable to reach the server. Refresh the page or check the server terminal.</div>'}
  }
}
function sidebarMarkup(){
  return `<aside class="sidebar ${state.sidebar?'open':''}" id="sidebar"><div class="sidebar-brand">${brand()}<button class="mobile-close icon-button" data-action="close-menu" aria-label="Close navigation">${icon('x')}</button></div>
  <div class="nav-label">WORKSPACE</div><nav class="sidebar-nav" aria-label="Main navigation">${NAV.filter(([page])=>(page!=='users'||canManage())&&(page!=='audit'||isAdmin())).map(([page,label,ico])=>
    `<a href="#/${page}" class="nav-link ${state.page===page?'active':''}">${icon(ico,19)}<span>${label}</span>${state.page===page?'<span class="nav-active-bar"></span>':''}</a>`).join('')}</nav>
  <div class="sidebar-bottom"><div class="help-card"><div class="help-icon">${icon('sparkles')}</div><b>Keep business moving</b><p>Everything your showroom needs, all in one place.</p></div>
  <a href="#/profile" class="sidebar-profile"><span class="avatar">${esc(initials(state.user.fullName))}</span><span class="profile-copy"><b>${esc(state.user.fullName)}</b><small>${esc(titleCase(state.user.role))}</small></span>${icon('chevron',16)}</a><button class="sidebar-signout" data-action="sign-out">${icon('logout',16)} Sign out</button></div></aside>`;
}
function shell(content){
  root.innerHTML=`<div class="app-shell">${sidebarMarkup()}${state.sidebar?'<button class="nav-overlay" data-action="close-menu" aria-label="Close navigation"></button>':''}
  <div class="main-shell"><header class="topbar"><div class="topbar-start"><button class="icon-button mobile-menu" data-action="open-menu" aria-label="Open navigation">${icon('menu',22)}</button><div class="breadcrumbs"><span>Workspace</span>${icon('chevron',14)}<b>${esc(NAMES[state.page]||'Dashboard')}</b></div></div>
  <div class="topbar-end"><div class="topbar-date">${new Date().toLocaleDateString('en-IN',{weekday:'short',month:'short',day:'numeric',year:'numeric'})}</div>
  <span class="topbar-sep"></span><button class="topbar-avatar" data-action="profile" title="My profile">${esc(initials(state.user.fullName))}</button></div></header>
  <main class="page-area" id="page-content">${content}</main></div></div><div id="modal-root"></div>`;
}
function pageHead(title,sub,action='',actionText=''){
  return `<div class="page-head"><div><div class="eyebrow">SHOWROOM OPERATIONS</div><h1>${esc(title)}</h1><p>${esc(sub)}</p></div>${action?`<div class="page-head-actions">${btn(`${icon('plus',17)} ${esc(actionText)}`,action)}</div>`:''}</div>`;
}
function statusFilter(items,selected){return `<select id="status-filter" aria-label="Filter by status"><option value="">All statuses</option>${items.map(s=>`<option value="${s}" ${selected===s?'selected':''}>${esc(titleCase(s))}</option>`).join('')}</select>`;}
function tools(filters=''){
  return `<div class="table-toolbar"><div class="search-field">${icon('search',18)}<input aria-label="Search records" id="table-search" value="${esc(state.query)}" placeholder="Search records..."></div><div class="toolbar-right">${filters||''}${state.page==='vehicles'?`<select id="showroom-filter" aria-label="Filter by showroom"><option value="">All locations</option>${(state.showrooms||[]).map(sh=>`<option value="${sh.id}" ${String(state.showroomFilter)===String(sh.id)?'selected':''}>${esc(sh.name)}</option>`).join('')}</select>`:''}<button class="btn btn-ghost icon-text" type="button" data-action="refresh">${icon('filter',16)} Refresh</button></div></div>`;
}
function table(columns, rows, emptyText='No records found',emptyAction=''){
  return `<div class="table-outer"><div class="table-scroll"><table><thead><tr>${columns.map(c=>`<th>${esc(c)}</th>`).join('')}</tr></thead><tbody>${rows||`<tr><td colspan="${columns.length}"><div class="empty-table">${icon('search',24)}<b>${esc(emptyText)}</b><span>Try a different search or add a new record.</span>${emptyAction?btn('Add a record',emptyAction,'secondary'):''}</div></td></tr>`}</tbody></table></div></div>`;
}
function paging(data){
  return `<div class="table-pagination"><span>Showing ${data.total?((data.page-1)*data.limit+1):0}–${Math.min(data.total,data.page*data.limit)} of ${data.total} records</span><div class="pagination-buttons"><button class="btn btn-ghost" data-action="prev-page" ${data.page<=1?'disabled':''}>Previous</button><span>Page ${data.page} of ${data.pages}</span><button class="btn btn-ghost" data-action="next-page" ${data.page>=data.pages?'disabled':''}>Next</button></div></div>`;
}
function mobileCards(section, data){
  const items=data.items||[];
  if(!items.length)return `<div class="mobile-card-empty">No matching records found</div>`;
  const details={
    vehicles:v=>({title:`${v.year} ${v.make} ${v.model}`,sub:v.variant||v.vin,lines:[['VIN',v.vin],['Location',v.showroomName],['Listing price',money(v.price)]],status:v.status,edit:canManage(),del:canManage()}),
    customers:v=>({title:v.fullName,sub:v.email||'Customer',lines:[['Phone',v.phone],['City',v.city||'—']],edit:true,del:canManage()}),
    sales:v=>({title:v.invoiceNumber,sub:v.vehicleLabel,lines:[['Customer',v.customerName],['Final amount',money(v.finalAmount)]],status:v.status,edit:v.status==='PENDING',del:isAdmin()&&v.status!=='COMPLETED',actions:v.status==='PENDING'&&canManage()?['sale-complete','sale-cancel']:[]}),
    'test-drives':v=>({title:v.customerName,sub:v.vehicleLabel,lines:[['Scheduled',when(v.scheduledAt)],['Salesperson',v.salespersonName]],status:v.status,edit:v.status==='SCHEDULED',del:canManage(),actions:v.status==='SCHEDULED'?['drive-complete','drive-noshow']:[]}),
    showrooms:v=>({title:v.name,sub:v.city,lines:[['Address',v.address],['Contact',v.phone||'—']],edit:isAdmin(),del:isAdmin()}),
    users:v=>({title:v.fullName,sub:v.email,lines:[['Role',titleCase(v.role)],['Contact',v.phone||'—']],status:v.active?'ACTIVE':'INACTIVE',edit:isAdmin(),del:isAdmin()&&v.id!==state.user.id}),
    audit:v=>({title:titleCase(v.action),sub:v.target,lines:[['User ID',v.userId||'System'],['When',when(v.createdAt)]],edit:false,del:false})
  };
  return `<div class="mobile-cards">${items.map(item=>{
    const d=details[section]?.(item);if(!d)return '';
    const actions=(d.actions||[]).map(a=>`<button class="mobile-quick" data-action="${a}" data-id="${item.id}">${icon(a.endsWith('complete')?'check':'x',14)} ${a.endsWith('complete')?'Complete':a.endsWith('cancel')?'Cancel':'No-show'}</button>`).join('');
    return `<article class="mobile-record"><div class="mobile-record-head"><div class="mobile-record-name"><strong>${esc(d.title)}</strong><small>${esc(d.sub)}</small></div>${d.status?badge(d.status):''}</div><dl>${d.lines.map(([label,value])=>`<div><dt>${esc(label)}</dt><dd>${esc(value)}</dd></div>`).join('')}</dl>${d.edit||d.del||actions?`<div class="mobile-record-actions">${actions}${d.edit?`<button data-action="edit" data-id="${item.id}">${icon('edit',14)} Edit</button>`:''}${d.del?`<button data-action="delete" data-id="${item.id}" class="mobile-delete">${icon('trash',14)} Delete</button>`:''}</div>`:''}</article>`
  }).join('')}</div>`;
}
function tablePanel(data, columns, rows, statuses=[], empty='No records found', emptyAction=''){
  return `<section class="panel table-panel">${tools(statuses.length?statusFilter(statuses,state.filter):'')}${table(columns,rows,empty,emptyAction)}${mobileCards(state.page,data)}${paging(data)}</section>`;
}
const personCell=(name,sub,id)=>`<div class="person-cell"><span class="avatar small tone-${(Number(id)||0)%5}">${esc(initials(name))}</span><span><b>${esc(name)}</b><small>${esc(sub||'')}</small></span></div>`;
const vehicleName=(v)=>`${esc(v.year)} ${esc(v.make)} ${esc(v.model)}`;
const rowActions = (item, editable, deletable)=>`<div class="row-actions">${editable?`<button class="mini-icon" title="Edit record" data-action="edit" data-id="${item.id}">${icon('edit',15)}</button>`:''}${deletable?`<button class="mini-icon danger-icon" title="Delete record" data-action="delete" data-id="${item.id}">${icon('trash',15)}</button>`:''}${!editable&&!deletable?'<span class="subdued">—</span>':''}</div>`;

function chartSvg(months){
  const vals=months.map(x=>Number(x.revenue)||0),max=Math.max(...vals,1)*1.24;
  const coords=vals.map((v,i)=>[50+i*104,180-(v/max)*140]);
  const line=coords.map(([x,y],i)=>`${i?'L':'M'} ${x} ${y.toFixed(2)}`).join(' ');
  const area=`${line} L ${coords.at(-1)[0]} 185 L ${coords[0][0]} 185 Z`;
  return `<svg viewBox="0 0 630 218" class="revenue-chart" role="img" aria-label="Revenue trend in the last six months"><defs><linearGradient id="revenue-fill" x1="0" x2="0" y1="0" y2="1"><stop offset="0" stop-color="#6477e5" stop-opacity=".23"/><stop offset="1" stop-color="#6477e5" stop-opacity="0"/></linearGradient></defs>
    ${[40,85,130,175].map(y=>`<line x1="50" y1="${y}" x2="575" y2="${y}" stroke="#e9ecf3" stroke-dasharray="4 5"/>`).join('')}
    <path d="${area}" fill="url(#revenue-fill)"/><path d="${line}" fill="none" stroke="#5b6bdc" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round"/>
    ${coords.map(([x,y])=>`<circle cx="${x}" cy="${y}" r="5" fill="#fff" stroke="#5b6bdc" stroke-width="3"/>`).join('')}
    ${months.map((m,i)=>`<text x="${50+i*104}" y="212" text-anchor="middle" fill="#929bae" font-size="12">${esc(m.month)}</text>`).join('')}
    <text x="42" y="44" text-anchor="end" fill="#a3aabb" font-size="11">${Math.round(max/1e5)}L</text><text x="42" y="178" text-anchor="end" fill="#a3aabb" font-size="11">0</text></svg>`;
}
function metric(label,value,ico,color,subtitle){return `<div class="metric-card"><div class="metric-top"><span>${esc(label)}</span><span class="metric-icon ${color}">${icon(ico,19)}</span></div><div class="metric-value">${esc(value)}</div><div class="metric-foot">${subtitle}</div></div>`;}
function dashboardPage(d){
  const first=state.user.fullName.split(' ')[0], hour=new Date().getHours();const greeting=hour<12?'Good morning':hour<17?'Good afternoon':'Good evening';
  const cards=metric('Total revenue',compactMoney(d.revenue),'money','purple',`<span class="good-text">${icon('trend',14)} ${d.completedSales} completed sales</span>`) +
    metric('Vehicles available',d.available,'car','blue',`<span>${d.vehicles} vehicles in your network</span>`) +
    metric('Upcoming test drives',d.upcomingCount,'calendar','amber','<span>Scheduled appointments</span>') +
    metric('Pending approvals',d.pendingSales,'clock','rose','<span>Sales awaiting a decision</span>');
  return `<div class="dashboard-page"><div class="hero-welcome"><div><div class="eyebrow">YOUR BUSINESS, AT A GLANCE</div><h1>${greeting}, ${esc(first)} <span class="wave">✳</span></h1><p>Here's what's happening across your showrooms today.</p></div><div class="hero-actions">${btn(`${icon('plus',17)} Add a vehicle`,'new-vehicle','secondary')}${btn(`${icon('plus',17)} New sale`,'new-sale')}</div></div>
    <div class="metrics-grid">${cards}</div>
    <div class="dashboard-grid"><section class="panel revenue-panel"><div class="panel-heading"><div><div class="panel-kicker">PERFORMANCE</div><h2>Revenue overview</h2><p>Completed sales · Last 6 months</p></div><div class="chart-total">${compactMoney(d.revenue)}<small>Total recorded</small></div></div>${chartSvg(d.monthlyRevenue)}</section>
    <section class="panel stock-panel"><div class="panel-heading"><div><div class="panel-kicker">STOCK HEALTH</div><h2>Inventory breakdown</h2><p>Across all showroom locations</p></div></div>
    <div class="inventory-ring-wrap"><div class="inventory-ring" style="--p:${d.vehicles?(100*d.available/d.vehicles):0}%"><div><strong>${d.vehicles}</strong><small>Total vehicles</small></div></div>
    <div class="inventory-legend">${[['AVAILABLE',d.available,'green'],['RESERVED',d.reserved,'yellow'],['SOLD',d.sold,'purple'],['IN_SERVICE',d.inService,'gray']].map(([s,n,c])=>`<div><span><i class="legend-dot ${c}"></i>${titleCase(s)}</span><strong>${n}</strong></div>`).join('')}</div></div></section></div>
    <div class="dashboard-grid lower-grid"><section class="panel"><div class="panel-heading"><div><div class="panel-kicker">LATEST ACTIVITY</div><h2>Recent sales</h2><p>Keep an eye on deal progress</p></div><a class="view-link" href="#/sales">View all ${icon('arrow',15)}</a></div>
    <div class="dashboard-list">${d.recentSales.length?d.recentSales.map(s=>`<div class="dashboard-list-row"><span class="list-symbol">${icon('receipt',19)}</span><div class="dash-record"><strong>${esc(s.vehicleLabel)}</strong><small>${esc(s.customerName)} · ${esc(s.invoiceNumber)}</small></div><div class="dash-trailing"><strong>${money(s.finalAmount)}</strong>${badge(s.status)}</div></div>`).join(''):'<div class="list-empty">No sales yet. Create your first sale to get started.</div>'}</div></section>
    <section class="panel"><div class="panel-heading"><div><div class="panel-kicker">UPCOMING</div><h2>Test drive schedule</h2><p>What's on the calendar next</p></div><a class="view-link" href="#/test-drives">View all ${icon('arrow',15)}</a></div>
    <div class="dashboard-list">${d.upcomingDrives.length?d.upcomingDrives.map(t=>`<div class="dashboard-list-row"><span class="date-token"><b>${new Date(t.scheduledAt).toLocaleString('en-IN',{day:'2-digit'})}</b><small>${new Date(t.scheduledAt).toLocaleString('en-IN',{month:'short'})}</small></span><div class="dash-record"><strong>${esc(t.customerName)}</strong><small>${esc(t.vehicleLabel)}</small></div><span class="schedule-time">${new Date(t.scheduledAt).toLocaleTimeString('en-IN',{hour:'numeric',minute:'2-digit'})}</span></div>`).join(''):'<div class="list-empty">No upcoming test drives. Your calendar is clear.</div>'}</div></section></div>
    <section class="panel location-panel"><div class="panel-heading"><div><div class="panel-kicker">YOUR NETWORK</div><h2>Showroom performance</h2><p>Available vehicles at each location</p></div><a class="view-link" href="#/showrooms">All locations ${icon('arrow',15)}</a></div>
    <div class="location-grid">${d.showrooms.length?d.showrooms.map(sh=>`<div class="location-mini"><div class="location-line"><span class="location-icon">${icon('building',19)}</span><span><strong>${esc(sh.name)}</strong><small>${esc(sh.city)}</small></span></div><div class="location-count"><b>${sh.available}</b><span>/ ${sh.total} available</span></div><div class="progress-line"><span style="width:${sh.total?Math.min(100,sh.available/sh.total*100):0}%"></span></div></div>`).join(''):'<div class="list-empty">Add a showroom to see location insights.</div>'}</div></section>
    </div>`;
}
function collectionPage(section,d){
  const permissions={vehicles:canManage(),customers:true,sales:true,'test-drives':true,showrooms:isAdmin(),users:isAdmin()};
  const singular={vehicles:'vehicle',customers:'customer',sales:'sale','test-drives':'test drive',showrooms:'showroom',users:'team member'}[section];
  const action='new-'+section;
  const extra=section==='users'?'<p class="info-note">Managers can view staff. Only administrators can change access or create accounts.</p>':'';
  const meta=`<div class="collection-summary"><span class="summary-number">${d.total}</span><span>${section==='vehicles'?'vehicles in inventory':section==='test-drives'?'appointments':section==='users'?'team members':section==='showrooms'?'locations':section==='sales'?'transactions':'customers'}</span></div>`;
  let columns=[],rows='',statuses=[];
  if(section==='vehicles'){
    columns=['VEHICLE','VIN','LOCATION','PRICE','STATUS','ACTIONS'];statuses=['AVAILABLE','RESERVED','SOLD','IN_SERVICE'];
    rows=d.items.map(v=>`<tr><td><div class="vehicle-cell"><span class="car-tile">${icon('car',22)}</span><span><b>${vehicleName(v)}</b><small>${esc(v.variant||`${v.fuelType||'Vehicle'} · ${v.year}`)}</small></span></div></td><td class="mono-cell">${esc(v.vin)}</td><td>${esc(v.showroomName)}</td><td class="money-cell">${money(v.price)}</td><td>${badge(v.status)}</td><td>${rowActions(v,canManage(),canManage())}</td></tr>`).join('');
  } else if(section==='customers'){
    columns=['CUSTOMER','PHONE','CITY','JOINED','ACTIONS'];
    rows=d.items.map(c=>`<tr><td>${personCell(c.fullName,c.email||'No email',c.id)}</td><td>${esc(c.phone)}</td><td>${esc(c.city||'—')}</td><td>${shortDate(c.createdAt)}</td><td>${rowActions(c,true,canManage())}</td></tr>`).join('');
  } else if(section==='sales'){
    columns=['INVOICE','VEHICLE','CUSTOMER','AMOUNT','STATUS','ACTIONS'];statuses=['PENDING','COMPLETED','CANCELLED'];
    rows=d.items.map(s=>`<tr><td><b class="invoice-num">${esc(s.invoiceNumber)}</b><div class="cell-subtext">${shortDate(s.saleDate)}</div></td><td><b>${esc(s.vehicleLabel)}</b><div class="cell-subtext">${esc(titleCase(s.paymentMethod))}</div></td><td>${esc(s.customerName)}</td><td class="money-cell">${money(s.finalAmount)}</td><td>${badge(s.status)}</td><td><div class="row-actions">${s.status==='PENDING'&&canManage()?`<button class="quick-icon approve" title="Complete sale" data-action="sale-complete" data-id="${s.id}">${icon('check',16)}</button><button class="quick-icon cancel" title="Cancel sale" data-action="sale-cancel" data-id="${s.id}">${icon('x',16)}</button>`:''}${rowActions(s,s.status==='PENDING',isAdmin()&&s.status!=='COMPLETED')}</div></td></tr>`).join('');
  } else if(section==='test-drives'){
    columns=['CUSTOMER','VEHICLE','SCHEDULE','STATUS','ACTIONS'];statuses=['SCHEDULED','COMPLETED','NO_SHOW','CANCELLED'];
    rows=d.items.map(t=>`<tr><td>${personCell(t.customerName,t.salespersonName,t.id)}</td><td>${esc(t.vehicleLabel)}</td><td><span class="date-cell">${icon('calendar',15)} ${when(t.scheduledAt)}</span></td><td>${badge(t.status)}</td><td><div class="row-actions">${t.status==='SCHEDULED'?`<button class="quick-icon approve" title="Mark completed" data-action="drive-complete" data-id="${t.id}">${icon('check',16)}</button><button class="quick-icon cancel" title="Mark no-show" data-action="drive-noshow" data-id="${t.id}">${icon('x',16)}</button>`:''}${rowActions(t,t.status==='SCHEDULED',canManage())}</div></td></tr>`).join('');
  } else if(section==='showrooms'){
    columns=['SHOWROOM','LOCATION','PHONE','ACTIONS'];
    rows=d.items.map(sh=>`<tr><td><div class="showroom-cell"><span class="building-tile">${icon('building',20)}</span><b>${esc(sh.name)}</b></div></td><td><b>${esc(sh.city)}</b><div class="cell-subtext">${esc(sh.address)}</div></td><td>${esc(sh.phone||'—')}</td><td>${rowActions(sh,isAdmin(),isAdmin())}</td></tr>`).join('');
  } else if(section==='users'){
    columns=['TEAM MEMBER','PHONE','ROLE','ACCESS','ACTIONS'];
    rows=d.items.map(u=>`<tr><td>${personCell(u.fullName,u.email,u.id)}</td><td>${esc(u.phone||'—')}</td><td>${badge(u.role)}</td><td>${badge(u.active?'ACTIVE':'INACTIVE')}</td><td>${rowActions(u,isAdmin(),isAdmin()&&u.id!==state.user.id)}</td></tr>`).join('');
  }
  return pageHead(NAMES[section],DESCS[section],permissions[section]?action:'',`Add ${singular}`)+meta+extra+tablePanel(d,columns,rows,statuses,`No ${singular}s found`,permissions[section]?action:'');
}
function auditPage(d){return pageHead('Activity log',DESCS.audit)+`<div class="collection-summary"><span class="summary-number">${d.total}</span><span>recorded activities</span></div>`+tablePanel(d,['ACTION','RECORD','USER ID','WHEN'],d.items.map(a=>`<tr><td><b>${esc(titleCase(a.action))}</b></td><td class="mono-cell">${esc(a.target)}</td><td>${esc(a.userId||'System')}</td><td>${when(a.createdAt)}</td></tr>`).join(''));}
function profilePage(){return pageHead('My profile','Your account details and security settings.')+`<div class="profile-layout"><section class="panel profile-card"><div class="profile-banner"><div class="profile-large-avatar">${esc(initials(state.user.fullName))}</div></div><h2>${esc(state.user.fullName)}</h2><p>${esc(state.user.email)}</p><div class="profile-tag">${icon('shield',16)} ${esc(titleCase(state.user.role))} account</div><div class="profile-divider"></div><div class="profile-row"><span>Status</span>${badge('ACTIVE')}</div><div class="profile-row"><span>Phone</span><b>${esc(state.user.phone||'Not added')}</b></div><div class="profile-row"><span>Member since</span><b>${shortDate(state.user.createdAt)}</b></div></section>
  <section class="panel security-card"><div class="panel-heading"><div><div class="panel-kicker">SECURITY</div><h2>Change password</h2><p>Choose a new password to keep your account secure.</p></div><span class="security-icon">${icon('lock',21)}</span></div><form id="password-form" class="profile-form"><label>Current password <input type="password" required name="current_password" autocomplete="current-password"></label><label>New password <input type="password" required minlength="12" name="new_password" autocomplete="new-password"></label><p class="password-hint">Minimum 12 characters including an uppercase letter, lowercase letter and number.</p><button type="submit" class="btn btn-primary">${icon('check',17)} Update password</button></form><div class="session-notice">${icon('shield',17)} All existing sessions are revoked when you change your password.</div></section></div>`;}

async function go(next,history=true){
  if(!state.user){showAuth('login');return}
  const page=['dashboard','vehicles','customers','sales','test-drives','showrooms','users','audit','profile'].includes(next)?next:'dashboard';
  if((page==='users'&&!canManage())||(page==='audit'&&!isAdmin())){notify('You do not have access to this page','error');return go('dashboard')}
  const changed=state.page!==page;
  state.page=page;state.sidebar=false;
  if(changed){state.query='';state.filter='';state.showroomFilter='';state.pageNo=1}
  if(history&&location.hash!==`#/${page}`)location.hash=`/${page}`;
  shell(`<div class="loading-panel"><div class="spinner"></div><span>Loading ${esc(NAMES[page])}…</span></div>`);
  const requestPage=page;
  try{
    if(page==='profile'){state.data=null;shell(profilePage());return}
    const params=new URLSearchParams();
    if(page!=='dashboard'){params.set('page',state.pageNo);params.set('limit','12');if(state.query)params.set('q',state.query);if(state.filter)params.set('status',state.filter);if(page==='vehicles'&&state.showroomFilter)params.set('showroomId',state.showroomFilter)}
    const request=api(page==='dashboard'?'/api/dashboard':`/api/${page}?${params}`);
    const [data,locations]=await Promise.all([request,page==='vehicles'?api('/api/showrooms?limit=100'):Promise.resolve(null)]);
    if(state.page!==requestPage)return;
    if(locations)state.showrooms=locations.items;
    state.data=data;
    shell(page==='dashboard'?dashboardPage(data):page==='audit'?auditPage(data):collectionPage(page,data));
    const search=document.getElementById('table-search');
    if(search && state.searchFocus){search.focus();search.setSelectionRange(search.value.length,search.value.length);state.searchFocus=false;}
  }catch(e){if(!state.user)return;displayError(e);shell(`<section class="panel error-panel">${icon('alert',30)}<h2>Could not load this page</h2><p>${esc(e.message)}</p>${btn('Try again','refresh','secondary')}</section>`)}
}

const defs={
 vehicles:{title:'Vehicle',fields:[
  ['vin','VIN / Registration ID','text',true,'e.g. MHG12345678901234'],['make','Manufacturer','text',true,'e.g. Hyundai'],
  ['model','Model','text',true,'e.g. Creta'],['variant','Variant','text',false,'e.g. SX(O)'],
  ['year','Year','number',true,'2025'],['color','Colour','text',false,'Titan Grey'],
  ['fuel_type','Fuel type','select',false,'',['Petrol','Diesel','Hybrid','Electric','CNG']],
  ['transmission','Transmission','select',false,'',['Manual','Automatic','AMT','CVT','DCT']],
  ['price','Listing price (₹)','number',true,'1500000'],['mileage','Mileage (km)','number',false,'0'],
  ['showroom_id','Showroom','select',true,'',[]],['status','Availability','select',true,'',['AVAILABLE','IN_SERVICE']],
  ['description','Description / notes','textarea',false,'Optional vehicle details']
 ]},
 customers:{title:'Customer',fields:[
  ['full_name','Full name','text',true,'Customer name'],['phone','Phone number','tel',true,'e.g. 9810012345'],
  ['email','Email address','email',false,'name@example.com'],['city','City','text',false,'New Delhi'],
  ['address','Address','text',false,'Street address'],['notes','Notes','textarea',false,'Internal notes']
 ]},
 sales:{title:'Sale',fields:[
  ['vehicle_id','Vehicle','select',true,'',[]],['customer_id','Customer','select',true,'',[]],
  ['salesperson_id','Salesperson','select',false,'',[]],['sale_price','Sale price (₹)','number',true,'1850000'],
  ['discount','Discount (₹)','number',false,'0'],['payment_method','Payment method','select',true,'',['UPI','CASH','CARD','BANK_TRANSFER','FINANCE']],
  ['sale_date','Sale date','date',true,''],['notes','Internal notes','textarea',false,'Optional deal details']
 ]},
 'test-drives':{title:'Test drive',fields:[
  ['vehicle_id','Vehicle','select',true,'',[]],['customer_id','Customer','select',true,'',[]],
  ['salesperson_id','Salesperson','select',false,'',[]],['scheduled_at','Appointment date and time','datetime-local',true,''],
  ['feedback','Notes / feedback','textarea',false,'Optional notes']
 ]},
 showrooms:{title:'Showroom',fields:[
  ['name','Showroom name','text',true,'e.g. Northstar South Delhi'],['city','City','text',true,'New Delhi'],
  ['address','Street address','text',true,'Full showroom address'],['phone','Phone number','tel',false,'Contact number']
 ]},
 users:{title:'Team member',fields:[
  ['full_name','Full name','text',true,'Staff member name'],['email','Email address','email',true,'name@company.com'],
  ['phone','Phone number','tel',false,'Optional'],['role','Access role','select',true,'',['SALES','MANAGER','ADMIN']],
  ['active','Account status','select',true,'',['true','false']],
  ['password','Password (leave blank to keep existing)','password',false,'Minimum 12 characters']
 ]}
};
const getOriginal=(item,field)=>{
  if(!item)return '';
  let key=field.replace(/_([a-z])/g,(_,c)=>c.toUpperCase());
  const v=item[key];
  if(field==='scheduled_at' && v) return asLocalInput(v);
  return v===undefined||v===null?'':String(v);
};
function fieldHtml(f,item){
  const [key,label,type,required,placeholder,choices] = f;
  let value=getOriginal(item,key);
  if(key==='status' && item?.status && !choices.includes(item.status)) choices.push(item.status);
  if(key==='status'&&!item)value='AVAILABLE';
  if(key==='active'&&!item)value='true';
  if(key==='discount'&&!item)value='0';
  if(key==='sale_date'&&!item)value=todayInput();
  if(key==='scheduled_at'&&!item)value=nowInput();
  if(key==='password' && !item) label; // still mandatory when creating
  const isReq=required||(key==='password'&&!item);
  const attr=`name="${esc(key)}" id="field-${esc(key)}" ${isReq?'required':''}`;
  let widget='';
  if(type==='select'){
    widget=`<select ${attr}><option value="">Select ${esc(label.toLowerCase())}</option>${(choices||[]).map(entry=>{
      const opt=typeof entry==='string'?{value:entry,label:titleCase(entry)}:entry;
      return `<option value="${esc(opt.value)}" ${value===String(opt.value)?'selected':''}>${esc(opt.label)}</option>`;
    }).join('')}</select>`;
  }else if(type==='textarea'){
    widget=`<textarea ${attr} rows="3" maxlength="1000" placeholder="${esc(placeholder)}">${esc(value)}</textarea>`;
  }else{
    widget=`<input ${attr} type="${type}" value="${esc(value)}" placeholder="${esc(placeholder)}" ${type==='number'?`min="0" step="${['price','sale_price','discount'].includes(key)?'0.01':'1'}"`:''} ${type==='password'?'autocomplete="new-password" minlength="12"':''}>`;
  }
  return `<label class="form-field ${type==='textarea'?'full':''}" for="field-${esc(key)}"><span>${esc(label)} ${isReq?'<i>*</i>':''}</span>${widget}</label>`;
}
async function openForm(section,item=null){
  const def=defs[section];if(!def)return;
  state.modal={type:'form',section,id:item?.id??null};
  const fields=def.fields.map(f=>[...f]);
  try{
    const resources=await Promise.all([
      ['sales','test-drives'].includes(section)?api('/api/vehicles?limit=100&status=AVAILABLE'):null,
      ['sales','test-drives'].includes(section)?api('/api/customers?limit=100'):null,
      ['sales','test-drives'].includes(section)?api('/api/users?limit=100').catch(()=>({items:[state.user]})):null,
      section==='vehicles'?api('/api/showrooms?limit=100'):null,
    ]);
    const [available,customers,staff,showrooms]=resources;
    const byKey=Object.fromEntries(fields.map(f=>[f[0],f]));
    if(available){
      const vehicles=[...available.items];
      if(item && item.vehicleId&&!vehicles.some(v=>v.id===item.vehicleId)){
        const match=await api(`/api/vehicles/${item.vehicleId}`);
        if(match)vehicles.unshift(match);
      }
      byKey.vehicle_id[5]=vehicles.map(v=>({value:v.id,label:`${v.year} ${v.make} ${v.model} · ${v.vin} (${titleCase(v.status)})`}));
    }
    if(customers)byKey.customer_id[5]=customers.items.map(c=>({value:c.id,label:`${c.fullName} · ${c.phone}`}));
    if(staff)byKey.salesperson_id[5]=[{value:'',label:'Assign to me'},...staff.items.filter(u=>u.active).map(u=>({value:u.id,label:u.fullName}))];
    if(showrooms)byKey.showroom_id[5]=showrooms.items.map(sh=>({value:sh.id,label:`${sh.name} · ${sh.city}`}));
    if(state.modal?.section!==section || state.modal?.id!==(item?.id??null)) return;
    if(section==='users'&&item)byKey.password[1]='New password (optional)';
    const dialog=`<div class="modal-backdrop"><section class="modal-dialog" role="dialog" aria-modal="true" aria-labelledby="modal-title"><div class="modal-header"><div><span class="modal-overline">${item?'EDIT RECORD':'CREATE NEW'}</span><h2 id="modal-title">${item?'Edit':'Add'} ${esc(def.title.toLowerCase())}</h2></div><button class="icon-button" data-action="close-modal" aria-label="Close modal">${icon('x',21)}</button></div>
    <form id="entity-form" data-section="${section}" data-id="${item?.id??''}"><div class="modal-body"><div class="form-grid">${fields.map(f=>fieldHtml(f,item)).join('')}</div>${section==='sales'?'<p class="form-hint">Creating a sale automatically reserves its vehicle until approval or cancellation.</p>':''}</div><div class="modal-footer"><button type="button" class="btn btn-ghost" data-action="close-modal">Cancel</button><button class="btn btn-primary" type="submit">${icon('check',17)} ${item?'Save changes':'Create '+def.title.toLowerCase()}</button></div></form></section></div>`;
    document.getElementById('modal-root').innerHTML=dialog;
    document.body.classList.add('modal-open');
    document.querySelector('#entity-form input:not([type="hidden"]), #entity-form select')?.focus();
  }catch(e){state.modal=null;displayError(e)}
}
function closeModal(){state.modal=null;document.body.classList.remove('modal-open');const el=document.getElementById('modal-root');if(el)el.innerHTML='';}
function confirmation(title,message,action,id,feedback=false){
  state.modal={type:'confirm',action,id};
  document.getElementById('modal-root').innerHTML=`<div class="modal-backdrop"><section class="modal-dialog modal-confirm" role="alertdialog" aria-modal="true" aria-labelledby="confirm-title"><div class="modal-header"><span class="confirm-icon">${icon(action==='delete'?'trash':'alert',22)}</span><button class="icon-button" data-action="close-modal" aria-label="Close modal">${icon('x',20)}</button></div>
  <div class="confirm-body"><h2 id="confirm-title">${esc(title)}</h2><p>${esc(message)}</p>${feedback?'<label class="form-field full" for="confirm-feedback"><span>Feedback / notes (optional)</span><textarea id="confirm-feedback" rows="3" maxlength="1000" placeholder="Add any notes..."></textarea></label>':''}</div>
  <div class="modal-footer"><button class="btn btn-ghost" data-action="close-modal">Go back</button><button class="btn ${action==='delete'?'btn-danger':'btn-primary'}" data-action="confirm-action">${action==='delete'?'Delete record':'Confirm action'}</button></div></section></div>`;
  document.body.classList.add('modal-open');
}
async function executeConfirmed(){
  if(!state.modal || state.pending)return;
  const {action,id}=state.modal,section=state.page;
  let method='PATCH',url='',payload={},done='Updated successfully';
  if(action==='delete'){method='DELETE';url=`/api/${section}/${id}`;done='Record deleted successfully';}
  else if(action.startsWith('sale-')){url=`/api/sales/${id}/status`;payload={status:action==='sale-complete'?'COMPLETED':'CANCELLED'};done=`Sale ${action==='sale-complete'?'completed':'cancelled'} successfully`}
  else if(action.startsWith('drive-')){url=`/api/test-drives/${id}/status`;payload={status:action==='drive-complete'?'COMPLETED':action==='drive-noshow'?'NO_SHOW':'CANCELLED',feedback:document.getElementById('confirm-feedback')?.value||null};done='Test drive updated'}
  else return;
  state.pending=true;
  try{await api(url,method,method==='DELETE'?undefined:payload);closeModal();notify(done);await go(state.page,false)}
  catch(e){displayError(e)}finally{state.pending=false}
}
async function submitEntity(form){
  if(state.pending)return;
  const section=form.dataset.section,id=form.dataset.id;
  const body=Object.fromEntries(new FormData(form).entries());
  const numeric=['year','price','mileage','showroom_id','vehicle_id','customer_id','salesperson_id','sale_price','discount'];
  for(const k of numeric){if(k in body && body[k]!=='')body[k]=Number(body[k]);}
  for(const k of Object.keys(body)){if(body[k]==='' && !['status','payment_method'].includes(k))body[k]=null;}
  if(section==='users'){body.active=body.active==='true';if(id && !body.password)delete body.password;}
  if(section==='test-drives' && body.scheduled_at)body.scheduled_at=new Date(body.scheduled_at).toISOString();
  if(section==='vehicles' && !body.mileage)body.mileage=0;
  if(section==='sales'){if(!body.discount)body.discount=0;if(!body.sale_date)body.sale_date=todayInput();}
  state.pending=true;
  const saveButton=form.querySelector('[type=submit]');if(saveButton){saveButton.disabled=true;saveButton.textContent='Saving…'}
  try{
    await api(`/api/${section}${id?`/${id}`:''}`,id?'PUT':'POST',body);
    closeModal();notify(`${defs[section].title} ${id?'updated':'created'} successfully`);await go(state.page,false);
  }catch(e){displayError(e)}finally{state.pending=false;if(saveButton){saveButton.disabled=false;saveButton.textContent='Save changes'}}
}
async function submitAuth(form){
  if(state.pending)return;
  state.pending=true;const submit=form.querySelector('[type=submit]');submit.disabled=true;
  const mode=form.dataset.mode;
  const payload=Object.fromEntries(new FormData(form).entries());
  if(mode==='setup')payload.demo_data=!!form.querySelector('[name=demo_data]:checked');
  try{
    const uri=mode==='setup'?'/api/auth/bootstrap':mode==='register'?'/api/auth/register':'/api/auth/login';
    const data=await api(uri,'POST',payload);
    state.user=data.user;state.csrf=data.csrfToken;notify('Welcome to your workspace');
    state.page='auth';await go('dashboard');
  }catch(e){displayError(e)}finally{state.pending=false;submit.disabled=false}
}
async function submitPassword(form){
  const data=Object.fromEntries(new FormData(form).entries());
  if(data.current_password===data.new_password){notify('Choose a password that is different from the current one','error');return;}
  try{
    const changed=await api('/api/auth/change-password','PUT',data);
    state.user=changed.user;state.csrf=changed.csrfToken;
    notify('Password updated; all other sessions were signed out');form.reset();
  }catch(e){displayError(e)}
}

let debounce;
document.addEventListener('input',e=>{
  if(e.target.id==='table-search'){
    state.query=e.target.value;state.pageNo=1;state.searchFocus=true;
    clearTimeout(debounce);debounce=setTimeout(()=>go(state.page,false),340);
  }
});
document.addEventListener('change',e=>{
  if(e.target.id==='status-filter'){state.filter=e.target.value;state.pageNo=1;go(state.page,false);}
  if(e.target.id==='showroom-filter'){state.showroomFilter=e.target.value;state.pageNo=1;go(state.page,false);}
});
document.addEventListener('submit',async e=>{
  if(!['auth-form','entity-form','password-form'].includes(e.target.id))return;
  e.preventDefault();
  if(e.target.id==='auth-form')return submitAuth(e.target);
  if(e.target.id==='entity-form')return submitEntity(e.target);
  if(e.target.id==='password-form')return submitPassword(e.target);
});
document.addEventListener('click',async e=>{
  const control=e.target.closest('[data-action]');if(!control)return;
  e.preventDefault();
  const action=control.dataset.action;
  if(action==='open-menu'){state.sidebar=true;shell(document.getElementById('page-content')?.innerHTML||'');return}
  if(action==='close-menu'){state.sidebar=false;shell(document.getElementById('page-content')?.innerHTML||'');return}
  if(action==='close-modal'){closeModal();return}
  if(action==='confirm-action'){executeConfirmed();return}
  if(action==='profile'){go('profile');return}
  if(action==='refresh'){go(state.page,false);return}
  if(action==='prev-page'){state.pageNo=Math.max(1,state.pageNo-1);go(state.page,false);return}
  if(action==='next-page'){state.pageNo++;go(state.page,false);return}
  if(action.startsWith('new-')){
    const section=action==='new-vehicle'?'vehicles':action==='new-sale'?'sales':action.slice(4);
    openForm(section);return;
  }
  if(action==='edit'){
    const item=state.data?.items?.find(i=>i.id===Number(control.dataset.id));
    if(item)openForm(state.page,item);return;
  }
  if(action==='delete'){
    const item=state.data?.items?.find(i=>i.id===Number(control.dataset.id));
    if(item)confirmation(`Delete this ${defs[state.page]?.title.toLowerCase()||'record'}?`,'This will permanently remove the record. Linked activity may prevent deletion.','delete',item.id);
    return;
  }
  const statusText={
    'sale-complete':['Complete this sale?','This confirms the transaction and marks the vehicle as sold.'],
    'sale-cancel':['Cancel this sale?','The pending deal will be cancelled and the vehicle released back to inventory.'],
    'drive-complete':['Complete test drive?','Mark this appointment as successfully completed.'],
    'drive-noshow':['Mark as no-show?','The customer will be marked as not having attended this appointment.']
  };
  if(statusText[action]){
    const [title,msg]=statusText[action];confirmation(title,msg,action,Number(control.dataset.id),action.startsWith('drive-'));
  }
  if(action==='sign-out'){
    try{await api('/api/auth/logout','POST');}catch{}
    state.user=null;state.csrf=null;history.replaceState(null,'','#/login');showAuth('login');notify('Signed out successfully');
  }
});
document.addEventListener('keydown',e=>{
  if(e.key==='Escape'&&state.modal)closeModal();
});
window.addEventListener('hashchange',()=>{
  const newPage=location.hash.replace('#/','')||'dashboard';
  if(newPage==='login'&&!state.user){showAuth('login');return}
  if(newPage==='register'&&!state.user&&state.registrationEnabled){showAuth('register');return}
  if(state.user&&newPage!==state.page)go(newPage,false);
});
init();
