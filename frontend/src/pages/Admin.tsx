import React,{useEffect,useState} from 'react'
import { adminApi } from '../lib/api'
const API=adminApi.base
export default function Admin(){
  const [tok,setTok]=useState(localStorage.getItem('bb_admin_token')||'')
  const [user,setUser]=useState('admin'); const [pass,setPass]=useState(''); const [err,setErr]=useState('')
  const [tab,setTab]=useState('dashboard'); const [dash,setDash]=useState<any>(null); const [orders,setOrders]=useState<any[]>([])
  const [menu,setMenu]=useState<any[]>([]); const [cats,setCats]=useState<any[]>([]); const [coupons,setCoupons]=useState<any[]>([])
  const [tables,setTables]=useState<any[]>([]); const [inv,setInv]=useState<any[]>([]); const [report,setReport]=useState<any[]>([]); const [settings,setSettings]=useState<any>({})
  const [foodForm,setFoodForm]=useState<any>({category_id:1,name:'',description:'',price:199,image_url:'',is_veg:true,is_available:true,rating:4.5})
  const [catForm,setCatForm]=useState(''); const [couponForm,setCouponForm]=useState<any>({code:'',type:'percent',value:10,min_order:0})
  const call=async(p:string,o:any={})=>adminApi.call(p,o,tok)
  const load=async()=>{
    if(!tok) return
    try{
      const [d,o,m,c,cp,tb,iv,rp,st]=await Promise.all([call('/api/admin/dashboard'),call('/api/admin/orders'),fetch(`${API}/api/menu`).then(r=>r.json()),fetch(`${API}/api/categories`).then(r=>r.json()),call('/api/admin/coupons'),call('/api/admin/tables'),call('/api/admin/inventory'),call('/api/admin/reports/sales'),call('/api/admin/settings')])
      setDash(d); setOrders(o); setMenu(m); setCats(c); setCoupons(cp); setTables(tb); setInv(iv); setReport(rp); setSettings(st)
    }catch(e:any){ setErr('Session expired or backend unreachable. Login again.'); }
  }
  useEffect(()=>{ load() },[tok])
  const login=async()=>{ try{ const r=await fetch(`${API}/api/admin/login`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({username:user,password:pass})}); if(!r.ok) throw new Error('bad'); const d=await r.json(); localStorage.setItem('bb_admin_token',d.access_token); setTok(d.access_token); setErr('') }catch{ setErr('Invalid credentials (default: admin / admin123 — change in production)') } }
  const saveSetting=async(k:string,v:string)=>{ await call('/api/admin/settings',{method:'POST',body:JSON.stringify({key:k,value:v})}); load() }
  if(!tok) return <div className="min-h-screen bg-espresso flex items-center justify-center p-4"><div className="bg-white rounded-[2rem] p-8 w-full max-w-sm shadow-2xl">
    <div className="text-4xl text-center">☕</div><h1 className="text-2xl font-extrabold text-center mt-2">Cafe Admin</h1><p className="text-center text-stone-500 text-sm">Brew & Bite Cafe Dashboard</p>
    {err&&<p className="bg-red-50 text-red-700 text-sm rounded-xl p-3 mt-4">{err}</p>}
    <input value={user} onChange={e=>setUser(e.target.value)} placeholder="Username" className="w-full border rounded-2xl px-4 py-3 mt-5"/>
    <input type="password" value={pass} onChange={e=>setPass(e.target.value)} placeholder="Password" className="w-full border rounded-2xl px-4 py-3 mt-3"/>
    <button onClick={login} className="w-full bg-espresso text-white font-bold py-3 rounded-full mt-4">Login →</button>
    <p className="text-xs text-stone-400 mt-3 text-center">Default demo login: admin / admin123<br/>Backend must be running at {API}</p>
    <a href="/" className="block text-center mt-3 text-sm underline">← Back to Mini App</a></div></div>

  return <div className="min-h-screen bg-cream">
    <header className="bg-espresso text-white px-5 py-4 flex justify-between items-center sticky top-0 z-10"><b className="text-lg">☕ Brew & Bite — Admin</b><div className="flex gap-2"><a href="/" className="bg-white/10 px-3 py-1.5 rounded-full text-sm">View App</a><button onClick={()=>{localStorage.removeItem('bb_admin_token'); setTok('')}} className="bg-white/10 px-3 py-1.5 rounded-full text-sm">Logout</button></div></header>
    <div className="flex gap-2 px-4 py-3 overflow-x-auto no-scrollbar">{['dashboard','orders','food','categories','coupons','tables','inventory','reports','settings'].map(t=>(<button key={t} onClick={()=>setTab(t)} className={`px-4 py-2 rounded-full font-bold capitalize whitespace-nowrap ${tab===t?'bg-espresso text-white':'bg-white'}`}>{t}</button>))}</div>
    <main className="p-4 max-w-5xl mx-auto">
    {err&&<p className="bg-amber-50 text-amber-800 rounded-xl p-3 mb-3 text-sm">{err}</p>}
    {tab==='dashboard'&&dash&&<div>
      <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
        {[['Total Orders',dash.total_orders],['Today Orders',dash.today_orders],['Total Revenue','₹'+dash.total_revenue],['Pending',dash.pending_orders],['Completed',dash.completed_orders]].map(([l,v]:any)=>(<div key={l} className="bg-white rounded-3xl p-5 card-shadow"><div className="text-stone-500 text-sm font-semibold">{l}</div><div className="text-3xl font-extrabold mt-1">{v}</div></div>))}
      </div>
      <h3 className="font-extrabold text-xl mt-6">🔥 Popular Items</h3><div className="bg-white rounded-3xl p-4 mt-2 card-shadow">{dash.popular_items?.length? dash.popular_items.map((p:any)=>(<div key={p.name} className="flex justify-between py-2 border-b last:border-0"><span>{p.name}</span><b>{p.qty} sold</b></div>)):<p className="text-stone-500">No sales yet</p>}</div>
      <h3 className="font-extrabold text-xl mt-6">🧾 Recent Transactions</h3><div className="bg-white rounded-3xl p-4 mt-2 card-shadow">{dash.recent_transactions?.map((t:any)=>(<div key={t.id} className="flex justify-between py-2 border-b last:border-0 text-sm"><span>{t.txn_ref} • {t.provider}</span><b>₹{t.amount} • {t.status}</b></div>))}</div>
    </div>}
    {tab==='orders'&&<div className="space-y-3">{orders.map(o=>(<div key={o.id} className="bg-white rounded-3xl p-4 card-shadow flex flex-wrap gap-3 justify-between items-center"><div><b>{o.order_code}</b> — {o.customer_name} ({o.phone||'-'})<div className="text-sm text-stone-600">{o.items.map((i:any)=>`${i.name}×${i.quantity}`).join(', ')} • ₹{o.total} • {o.order_type} {o.table_number?`T${o.table_number}`:''} • {o.payment_method}/{o.payment_status}</div></div>
      <select value={o.status} onChange={async e=>{ await call(`/api/admin/orders/${o.id}/status`,{method:'PATCH',body:JSON.stringify({status:e.target.value})}); load() }} className="border rounded-full px-3 py-2 font-bold">{['placed','accepted','preparing','ready','completed','cancelled'].map(s=><option key={s}>{s}</option>)}</select>
      <button onClick={()=>{ const w=window.open('','_blank'); w?.document.write(`<pre>BREW & BITE CAFE\n${o.order_code}\n${o.items.map((i:any)=>`${i.name} x${i.quantity}  ₹${i.line_total}`).join('\n')}\nTotal: ₹${o.total}</pre>`); w?.print() }} className="bg-cream px-3 py-2 rounded-full font-bold text-sm">🖨 Receipt</button></div>))}</div>}
    {tab==='food'&&<div>
      <div className="bg-white rounded-3xl p-4 card-shadow grid md:grid-cols-3 gap-3">
        <input value={foodForm.name} onChange={e=>setFoodForm({...foodForm,name:e.target.value})} placeholder="Food name" className="border rounded-xl px-3 py-2"/>
        <input type="number" value={foodForm.price} onChange={e=>setFoodForm({...foodForm,price:Number(e.target.value)})} placeholder="Price" className="border rounded-xl px-3 py-2"/>
        <select value={foodForm.category_id} onChange={e=>setFoodForm({...foodForm,category_id:Number(e.target.value)})} className="border rounded-xl px-3 py-2">{cats.map(c=><option key={c.id} value={c.id}>{c.name}</option>)}</select>
        <input value={foodForm.image_url} onChange={e=>setFoodForm({...foodForm,image_url:e.target.value})} placeholder="Image URL (Unsplash/Cloudinary)" className="border rounded-xl px-3 py-2 md:col-span-2"/>
        <label className="flex items-center gap-2 font-semibold"><input type="checkbox" checked={foodForm.is_veg} onChange={e=>setFoodForm({...foodForm,is_veg:e.target.checked})}/> Veg</label>
        <input value={foodForm.description} onChange={e=>setFoodForm({...foodForm,description:e.target.value})} placeholder="Description" className="border rounded-xl px-3 py-2 md:col-span-2"/>
        <button onClick={async()=>{ await call('/api/admin/items',{method:'POST',body:JSON.stringify({...foodForm,sizes:[],addons:[]})}); load() }} className="bg-espresso text-white rounded-full py-2 font-bold">+ Add Item</button>
      </div>
      <div className="grid md:grid-cols-2 gap-3 mt-4">{menu.map(f=>(<div key={f.id} className="bg-white rounded-3xl p-3 card-shadow flex gap-3 items-center"><img src={f.image_url} className="w-16 h-16 rounded-2xl object-cover" alt=""/><div className="flex-1"><b>{f.name}</b><div className="text-sm text-stone-500">₹{f.price} • {f.is_available?'Available':'Unavailable'}</div></div>
        <button onClick={async()=>{ await call(`/api/admin/items/${f.id}/availability`,{method:'PATCH'}); load() }} className="bg-cream px-3 py-2 rounded-full text-sm font-bold">{f.is_available?'Disable':'Enable'}</button>
        <button onClick={async()=>{ if(confirm('Delete '+f.name+'?')){ await call(`/api/admin/items/${f.id}`,{method:'DELETE'}); load() } }} className="text-red-600 font-bold px-2">Delete</button></div>))}</div>
    </div>}
    {tab==='categories'&&<div><div className="flex gap-2"><input value={catForm} onChange={e=>setCatForm(e.target.value)} placeholder="New category name" className="border rounded-full px-4 py-2 flex-1 bg-white"/><button onClick={async()=>{ await call('/api/admin/categories',{method:'POST',body:JSON.stringify({name:catForm,slug:catForm.toLowerCase().replace(/\s+/g,'-')})}); setCatForm(''); load() }} className="bg-espresso text-white px-5 rounded-full font-bold">Add</button></div>
      <div className="grid grid-cols-2 md:grid-cols-3 gap-3 mt-4">{cats.map(c=>(<div key={c.id} className="bg-white rounded-3xl p-4 card-shadow flex justify-between items-center"><span className="font-bold">{c.icon} {c.name}</span><button onClick={async()=>{ if(confirm('Delete category?')){ await call(`/api/admin/categories/${c.id}`,{method:'DELETE'}); load() } }} className="text-red-600 font-bold text-sm">Delete</button></div>))}</div></div>}
    {tab==='coupons'&&<div><div className="bg-white rounded-3xl p-4 card-shadow flex flex-wrap gap-2"><input value={couponForm.code} onChange={e=>setCouponForm({...couponForm,code:e.target.value.toUpperCase()})} placeholder="CODE" className="border rounded-xl px-3 py-2"/><input type="number" value={couponForm.value} onChange={e=>setCouponForm({...couponForm,value:Number(e.target.value)})} placeholder="Value" className="border rounded-xl px-3 py-2 w-24"/><select value={couponForm.type} onChange={e=>setCouponForm({...couponForm,type:e.target.value})} className="border rounded-xl px-3 py-2"><option value="percent">% off</option><option value="flat">Flat ₹</option></select><input type="number" value={couponForm.min_order} onChange={e=>setCouponForm({...couponForm,min_order:Number(e.target.value)})} placeholder="Min order" className="border rounded-xl px-3 py-2 w-28"/><button onClick={async()=>{ await call('/api/admin/coupons',{method:'POST',body:JSON.stringify(couponForm)}); load() }} className="bg-espresso text-white px-5 rounded-full font-bold">Add Coupon</button></div>
      <div className="mt-4 space-y-2">{coupons.map(c=>(<div key={c.id} className="bg-white rounded-2xl p-4 card-shadow flex justify-between"><span><b>{c.code}</b> — {c.type==='percent'?c.value+'% off':'₹'+c.value+' off'} (min ₹{c.min_order})</span><button onClick={async()=>{ await call(`/api/admin/coupons/${c.id}`,{method:'DELETE'}); load() }} className="text-red-600 font-bold">Delete</button></div>))}</div></div>}
    {tab==='tables'&&<div className="grid grid-cols-2 md:grid-cols-4 gap-3">{tables.map(t=>(<div key={t.id} className="bg-white rounded-3xl p-5 card-shadow text-center"><div className="text-3xl">🪑</div><b>Table {t.number}</b><div className="text-sm text-stone-500">Seats {t.capacity}</div><button onClick={async()=>{ await call(`/api/admin/tables/${t.id}`,{method:'DELETE'}); load() }} className="text-red-600 text-sm font-bold mt-2">Remove</button></div>))}
      <button onClick={async()=>{ const n=String(tables.length+1); await call('/api/admin/tables',{method:'POST',body:JSON.stringify({number:n,capacity:4})}); load() }} className="bg-espresso text-white rounded-3xl font-bold">+ Add Table</button></div>}
    {tab==='inventory'&&<div className="bg-white rounded-3xl p-4 card-shadow">{inv.map(i=>(<div key={i.id} className="flex justify-between py-3 border-b last:border-0"><span className="font-semibold">{i.name}</span><span className={i.quantity<=i.low_stock_threshold?'text-red-600 font-bold':''}>{i.quantity} {i.unit}{i.quantity<=i.low_stock_threshold?' ⚠ low stock':''}</span></div>))}</div>}
    {tab==='reports'&&<div className="bg-white rounded-3xl p-4 card-shadow"><h3 className="font-extrabold mb-3">📊 Sales Report (by day)</h3>{report.length===0?<p className="text-stone-500">No sales data yet.</p>:report.map(r=>(<div key={r.date} className="flex justify-between py-2 border-b last:border-0"><span>{r.date}</span><span>{r.orders} orders</span><b>₹{r.revenue}</b></div>))}</div>}
    {tab==='settings'&&<div className="bg-white rounded-3xl p-5 card-shadow space-y-4 max-w-xl">{[['cafe_name','Cafe Name'],['cafe_tagline','Tagline'],['cafe_phone','Phone'],['cafe_address','Address'],['business_hours','Business Hours'],['gst_percent','GST %']].map(([k,l])=>(<div key={k} className="flex gap-2 items-center"><label className="w-32 font-bold text-sm">{l}</label><input defaultValue={settings[k]||''} id={'set-'+k} className="border rounded-xl px-3 py-2 flex-1"/><button onClick={()=>saveSetting(k,(document.getElementById('set-'+k) as HTMLInputElement).value)} className="bg-espresso text-white px-4 py-2 rounded-full font-bold text-sm">Save</button></div>))}<p className="text-xs text-stone-400">GST % is used in server-side order calculation for every order.</p></div>}
    </main>
  </div>
}
