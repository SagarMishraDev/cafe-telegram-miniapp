import React,{useEffect,useMemo,useState} from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { api, initTelegram, tgUser, haptic } from './lib/api'
import { Food, Category } from './lib/seedData'
import { useCart } from './context/CartContext'

const VegDot=({veg}:{veg:boolean})=>(<span title={veg?'Veg':'Non-veg'} className={`inline-flex w-4 h-4 border-2 ${veg?'border-green-600':'border-red-600'} rounded-sm items-center justify-center bg-white`}><span className={`w-2 h-2 rounded-full ${veg?'bg-green-600':'bg-red-600'}`}/></span>)
const fmt=(n:number)=>`₹${Number(n).toFixed(0)}`

function FoodCard({f,onOpen}:{f:Food;onOpen:(f:Food)=>void}){
  const {add}=useCart()
  return <motion.div layout initial={{opacity:0,y:16}} animate={{opacity:1,y:0}} className="bg-white rounded-3xl overflow-hidden card-shadow tilt cursor-pointer" onClick={()=>onOpen(f)}>
    <div className="relative h-36 overflow-hidden">
      <img src={f.image_url} alt={f.name} className="w-full h-full object-cover" loading="lazy"/>
      {!f.is_available&&<div className="absolute inset-0 bg-black/60 text-white flex items-center justify-center font-bold">Unavailable</div>}
      <span className="absolute top-2 left-2 glass px-2 py-0.5 rounded-full text-xs font-bold">⭐ {f.rating}</span>
      <span className="absolute top-2 right-2"><VegDot veg={f.is_veg}/></span>
    </div>
    <div className="p-3">
      <h3 className="font-bold leading-tight">{f.name}</h3>
      <p className="text-xs text-stone-500 line-clamp-2 mt-1">{f.description}</p>
      <div className="flex items-center justify-between mt-3">
        <span className="font-extrabold text-lg">{fmt(f.price)}</span>
        <button disabled={!f.is_available} onClick={(e)=>{e.stopPropagation(); add(f); haptic()}} className="bg-espresso text-white px-4 py-1.5 rounded-full text-sm font-bold disabled:opacity-40 active:scale-95 transition">ADD +</button>
      </div>
    </div>
  </motion.div>
}

function DetailModal({f,close}:{f:Food;close:()=>void}){
  const {add}=useCart()
  const [qty,setQty]=useState(1); const [size,setSize]=useState(f.sizes[0]?.name||''); const [sel,setSel]=useState<string[]>([]); const [note,setNote]=useState('')
  const sizeDelta=f.sizes.find(s=>s.name===size)?.delta||0
  const addons=f.addons.filter(a=>sel.includes(a.name))
  const unit=f.price+sizeDelta+addons.reduce((s,a)=>s+a.price,0)
  return <motion.div initial={{opacity:0}} animate={{opacity:1}} exit={{opacity:0}} className="fixed inset-0 z-50 bg-black/50 flex items-end sm:items-center justify-center" onClick={close}>
    <motion.div initial={{y:60}} animate={{y:0}} onClick={e=>e.stopPropagation()} className="bg-cream w-full max-w-lg max-h-[92vh] overflow-y-auto rounded-t-[2rem] sm:rounded-[2rem]">
      <div className="relative h-64"><img src={f.image_url} className="w-full h-full object-cover floaty" alt={f.name}/><button onClick={close} className="absolute top-3 right-3 bg-white/90 w-9 h-9 rounded-full font-bold">✕</button><span className="absolute bottom-3 left-3"><VegDot veg={f.is_veg}/></span></div>
      <div className="p-5">
        <div className="flex justify-between gap-3"><h2 className="text-2xl font-extrabold">{f.name}</h2><span className="font-bold">⭐ {f.rating}</span></div>
        <p className="text-stone-600 mt-1">{f.description}</p>
        <p className="text-sm text-stone-500 mt-1">⏱ {f.prep_time_mins} mins • {f.category_name||''}</p>
        {f.sizes.length>0&&<><h4 className="font-bold mt-5 mb-2">Choose Size</h4><div className="flex gap-2 flex-wrap">{f.sizes.map(s=>(<button key={s.name} onClick={()=>setSize(s.name)} className={`px-4 py-2 rounded-full border font-semibold ${size===s.name?'bg-espresso text-white':'bg-white'}`}>{s.name}{s.delta?` +₹${s.delta}`:''}</button>))}</div></>}
        {f.addons.length>0&&<><h4 className="font-bold mt-5 mb-2">Add-ons & Extras</h4><div className="space-y-2">{f.addons.map(a=>(<label key={a.name} className="flex justify-between bg-white rounded-2xl px-4 py-3 card-shadow cursor-pointer"><span className="flex gap-2 items-center"><input type="checkbox" checked={sel.includes(a.name)} onChange={e=>setSel(prev=>e.target.checked?[...prev,a.name]:prev.filter(x=>x!==a.name))}/>{a.name}</span><span className="font-semibold">+₹{a.price}</span></label>))}</div></>}
        <h4 className="font-bold mt-5 mb-2">Special Instructions</h4>
        <textarea value={note} onChange={e=>setNote(e.target.value)} placeholder="Less spicy, extra sauce…" className="w-full bg-white rounded-2xl p-3 border" rows={2}/>
        <div className="flex items-center justify-between mt-5 sticky bottom-0 bg-cream py-2">
          <div className="flex items-center gap-3 bg-white rounded-full px-2 py-1 card-shadow"><button onClick={()=>setQty(Math.max(1,qty-1))} className="w-8 h-8 font-bold text-xl">−</button><b>{qty}</b><button onClick={()=>setQty(qty+1)} className="w-8 h-8 font-bold text-xl">+</button></div>
          <button onClick={()=>{add(f,qty,size,sizeDelta,addons,note); haptic(); close()}} className="bg-gradient-to-r from-amber-500 to-orange-600 text-white font-extrabold px-6 py-3 rounded-full shadow-lg active:scale-95 transition">Add • {fmt(unit*qty)}</button>
        </div>
      </div>
    </motion.div></motion.div>
}

const STEPS=['placed','accepted','preparing','ready','completed']
const STEP_LABEL:any={placed:'Order Placed',accepted:'Accepted',preparing:'Preparing',ready:'Ready for Pickup',completed:'Completed',cancelled:'Cancelled'}

export default function App(){
  const [tab,setTab]=useState<'home'|'menu'|'orders'|'profile'|'cart'|'checkout'>('home')
  const [cats,setCats]=useState<Category[]>([]); const [foods,setFoods]=useState<Food[]>([]); const [loading,setLoading]=useState(true)
  const [search,setSearch]=useState(''); const [catId,setCatId]=useState(0); const [vegOnly,setVegOnly]=useState(false)
  const [detail,setDetail]=useState<Food|null>(null); const [settings,setSettings]=useState<any>({})
  const [orders,setOrders]=useState<any[]>([]); const [tables,setTables]=useState<any[]>([])
  const [coupon,setCoupon]=useState(''); const [discount,setDiscount]=useState(0); const [couponMsg,setCouponMsg]=useState('')
  const [form,setForm]=useState({name:'',phone:'',type:'takeaway',table:'',instructions:'',payment:'cash'})
  const [placed,setPlaced]=useState<any>(null)
  const cart=useCart()
  const gstPct=Number(settings.gst_percent||5)
  const taxable=cart.subtotal-discount; const gst=Math.round(taxable*gstPct)/100*1; const gstAmt=Math.round(taxable*gstPct*100/100)/1 // computed below properly
  const gstVal=Math.round((taxable*gstPct/100)*100)/100; const total=Math.round((taxable+gstVal)*100)/100

  const load=async()=>{ setLoading(true); const [c,m,s,t]=await Promise.all([api.categories(),api.menu(search,catId,vegOnly),api.settings(),api.tables()]); setCats(c); setFoods(m); setSettings(s); setTables(t); setLoading(false) }
  useEffect(()=>{ initTelegram(); load() },[])
  useEffect(()=>{ const id=setTimeout(load,250); return ()=>clearTimeout(id) },[search,catId,vegOnly])
  useEffect(()=>{ if(tab==='orders'){ api.myOrders().then(setOrders); const iv=setInterval(()=>api.myOrders().then(setOrders),15000); return ()=>clearInterval(iv) } },[tab])
  const featured=foods.filter(f=>f.is_featured); const popular=foods.filter(f=>f.is_popular)
  const user=tgUser()

  const applyCoupon=async()=>{ const r=await api.validateCoupon(coupon,cart.subtotal); setDiscount(r.valid?r.discount:0); setCouponMsg(r.message||'') }
  const placeOrder=async()=>{
    if(!form.name.trim()){ alert('Please enter your name'); return }
    if(form.type==='dine-in'&&!form.table){ alert('Please select a table'); return }
    if(form.payment==='razorpay'){ const key=(import.meta as any).env?.VITE_RAZORPAY_KEY_ID; if(!key){ alert('Online payment is not configured yet — please choose Cash / Pay at Cafe, or UPI at counter.'); return } }
    const payload={customer_name:form.name,phone:form.phone,order_type:form.type,table_number:form.table,instructions:form.instructions,payment_method:form.payment,coupon_code:discount?coupon:'',items:cart.items.map((i:any)=>({food_item_id:i.food.id,quantity:i.qty,size:i.size,addons:i.addons,instructions:i.instructions}))}
    const o=await api.createOrder(payload); setPlaced(o); cart.clear(); setDiscount(0); haptic()
  }

  return <div className="max-w-lg mx-auto min-h-screen pb-28 relative">
    {/* Header */}
    <header className="sticky top-0 z-40 glass px-4 py-3 flex items-center justify-between">
      <div className="flex items-center gap-2"><span className="text-3xl">☕</span><div><div className="font-extrabold leading-none">{settings.cafe_name||'Brew & Bite Cafe'}</div><div className="text-[11px] text-stone-500">{settings.business_hours||'9 AM – 11 PM'} • {settings.cafe_address||''}</div></div></div>
      <button onClick={()=>setTab('cart')} className="relative bg-espresso text-white px-4 py-2 rounded-full font-bold">🛒 Cart{cart.count>0&&<span className="absolute -top-2 -right-2 bg-amber-500 text-white text-xs w-6 h-6 rounded-full flex items-center justify-center border-2 border-cream">{cart.count}</span>}</button>
    </header>

    {(tab==='home'||tab==='menu')&&<>
      {/* Hero */}
      <section className="mx-4 mt-4 rounded-[2rem] bg-gradient-to-br from-espresso via-coffee to-amber-900 text-white p-5 relative overflow-hidden card-shadow">
        <div className="relative z-10">
          <p className="text-amber-300 font-bold text-sm">👋 Welcome{user.first_name?`, ${user.first_name}`:''}</p>
          <h1 className="text-3xl font-extrabold leading-tight mt-1">Good vibes,<br/>great bites.</h1>
          <p className="text-white/80 text-sm mt-2 max-w-[220px]">{settings.cafe_tagline||'Burgers, pizza, coffee & shakes — made fresh, ordered in seconds inside Telegram.'}</p>
          <button onClick={()=>setTab('menu')} className="mt-4 bg-amber-500 text-espresso font-extrabold px-5 py-2.5 rounded-full shadow-lg active:scale-95 transition">Explore Our Menu →</button>
        </div>
        {featured[0]&&<div className="absolute -right-4 top-6 w-40 h-40 [perspective:600px]"><img src={featured[0].image_url} alt="" className="w-40 h-40 object-cover rounded-full border-4 border-white/30 shadow-2xl dish3d"/></div>}
      </section>
      {/* Offers */}
      <section className="mx-4 mt-4 flex gap-3 overflow-x-auto no-scrollbar">
        <div className="min-w-[240px] bg-gradient-to-r from-orange-500 to-amber-500 text-white rounded-3xl p-4 card-shadow"><b className="text-lg">🎉 WELCOME10</b><p className="text-sm text-white/90">10% OFF up to ₹150 on your order</p></div>
        <div className="min-w-[240px] bg-gradient-to-r from-emerald-600 to-teal-500 text-white rounded-3xl p-4 card-shadow"><b className="text-lg">💸 FIRST50</b><p className="text-sm text-white/90">Flat ₹50 OFF above ₹299</p></div>
      </section>
      {/* Search */}
      <div className="mx-4 mt-4 flex gap-2">
        <input value={search} onChange={e=>setSearch(e.target.value)} placeholder="🔍 Search burgers, coffee, momos…" className="flex-1 bg-white rounded-full px-4 py-3 card-shadow outline-none"/>
        <button onClick={()=>setVegOnly(!vegOnly)} className={`px-4 rounded-full font-bold card-shadow ${vegOnly?'bg-green-600 text-white':'bg-white'}`}>Veg</button>
      </div>
      {/* Categories */}
      <div className="flex gap-2 overflow-x-auto no-scrollbar px-4 mt-4">
        <button onClick={()=>setCatId(0)} className={`whitespace-nowrap px-4 py-2 rounded-full font-bold ${catId===0?'bg-espresso text-white':'bg-white'}`}>All</button>
        {cats.map(c=>(<button key={c.id} onClick={()=>setCatId(c.id)} className={`whitespace-nowrap px-4 py-2 rounded-full font-bold ${catId===c.id?'bg-espresso text-white':'bg-white'}`}>{c.icon} {c.name}</button>))}
      </div>
      {tab==='home'&&!catId&&!search&&<>
        <h2 className="px-4 mt-6 text-xl font-extrabold">⭐ Featured Today</h2>
        <div className="flex gap-4 overflow-x-auto no-scrollbar px-4 mt-3 pb-2">{featured.map(f=>(<div key={f.id} onClick={()=>setDetail(f)} className="min-w-[220px] cursor-pointer"><div className="relative"><img src={f.image_url} className="w-[220px] h-[150px] object-cover rounded-[1.6rem] card-shadow floaty" alt={f.name}/><span className="absolute bottom-2 left-2 glass px-2 py-0.5 rounded-full text-xs font-bold">⭐ {f.rating}</span></div><div className="font-bold mt-2 px-1">{f.name}</div><div className="px-1 text-amber-700 font-extrabold">{fmt(f.price)}</div></div>))}</div>
        <h2 className="px-4 mt-4 text-xl font-extrabold">🔥 Popular Dishes</h2>
        <div className="grid grid-cols-2 gap-4 px-4 mt-3">{popular.slice(0,4).map(f=><FoodCard key={f.id} f={f} onOpen={setDetail}/>)}</div>
        <h2 className="px-4 mt-6 text-xl font-extrabold">🍽️ Browse Categories</h2>
        <div className="grid grid-cols-3 gap-3 px-4 mt-3">{cats.map(c=>(<button key={c.id} onClick={()=>{setCatId(c.id); setTab('menu')}} className="bg-white rounded-3xl py-4 card-shadow font-bold active:scale-95 transition"><div className="text-3xl">{c.icon}</div><div className="text-sm mt-1">{c.name}</div></button>))}</div>
      </>}
      <h2 className="px-4 mt-6 text-xl font-extrabold">{tab==='menu'||catId||search?'🍴 Menu':'🍴 All Dishes'}</h2>
      {loading? <div className="grid grid-cols-2 gap-4 px-4 mt-3">{[1,2,3,4].map(i=><div key={i} className="h-56 rounded-3xl skeleton"/>)}</div>
      : foods.length===0? <p className="px-4 mt-4 text-stone-500">No dishes found. Try another search.</p>
      : <div className="grid grid-cols-2 gap-4 px-4 mt-3">{foods.map(f=><FoodCard key={f.id} f={f} onOpen={setDetail}/>)}</div>}
    </>}

    {tab==='cart'&&<div className="px-4 mt-4">
      <h2 className="text-2xl font-extrabold">🛒 Your Cart</h2>
      {cart.items.length===0? <div className="text-center py-16"><div className="text-6xl">🛒</div><p className="font-bold mt-3">Your cart is empty</p><p className="text-stone-500 text-sm">Add something delicious from the menu.</p><button onClick={()=>setTab('menu')} className="mt-4 bg-espresso text-white px-6 py-3 rounded-full font-bold">Browse Menu</button></div>
      :<>{cart.items.map((i:any)=>(<div key={i.key} className="bg-white rounded-3xl p-3 mt-3 card-shadow flex gap-3">
          <img src={i.food.image_url} className="w-20 h-20 rounded-2xl object-cover" alt=""/>
          <div className="flex-1"><div className="flex justify-between"><b>{i.food.name}</b><button onClick={()=>cart.remove(i.key)} className="text-red-500 font-bold">✕</button></div>
          <div className="text-xs text-stone-500">{i.size||'Regular'}{i.addons.length?` • ${i.addons.map((a:any)=>a.name).join(', ')}`:''}</div>
          {i.instructions&&<div className="text-xs italic text-stone-500">“{i.instructions}”</div>}
          <div className="flex justify-between items-center mt-2"><div className="flex items-center gap-2 bg-cream rounded-full px-2 py-0.5"><button onClick={()=>cart.updateQty(i.key,i.qty-1)} className="font-bold text-lg px-1">−</button><b>{i.qty}</b><button onClick={()=>cart.updateQty(i.key,i.qty+1)} className="font-bold text-lg px-1">+</button></div><b>{fmt(i.unit*i.qty)}</b></div></div>
        </div>))}
        <div className="bg-white rounded-3xl p-4 mt-4 card-shadow">
          <div className="flex gap-2"><input value={coupon} onChange={e=>setCoupon(e.target.value)} placeholder="Coupon code (WELCOME10)" className="flex-1 border rounded-full px-4 py-2 uppercase"/><button onClick={applyCoupon} className="bg-espresso text-white px-4 rounded-full font-bold">Apply</button></div>
          {couponMsg&&<p className="text-sm mt-2 text-emerald-700 font-semibold">{couponMsg}</p>}
          <div className="space-y-1 mt-3 text-sm"><div className="flex justify-between"><span>Subtotal</span><b>{fmt(cart.subtotal)}</b></div>
          {discount>0&&<div className="flex justify-between text-emerald-700"><span>Discount</span><b>−{fmt(discount)}</b></div>}
          <div className="flex justify-between"><span>GST ({gstPct}%)</span><b>{fmt(gstVal)}</b></div>
          <div className="flex justify-between text-lg font-extrabold border-t pt-2"><span>Total</span><span>{fmt(total)}</span></div></div>
        </div>
        <button onClick={()=>setTab('checkout')} className="w-full mt-4 bg-gradient-to-r from-amber-500 to-orange-600 text-white font-extrabold py-4 rounded-full shadow-lg">Proceed to Checkout →</button>
      </>}
    </div>}

    {tab==='checkout'&&<div className="px-4 mt-4">
      <h2 className="text-2xl font-extrabold">✅ Checkout</h2>
      {placed? <div className="text-center py-10 bg-white rounded-[2rem] mt-4 card-shadow px-6"><div className="text-6xl">🎉</div><h3 className="text-2xl font-extrabold mt-3">Order Confirmed!</h3><p className="mt-2">Order ID: <b>{placed.order_code}</b></p><p className="text-stone-600">Total: <b>{fmt(placed.total)}</b> • Ready in ~{placed.eta_mins||25} mins</p><p className="text-sm text-stone-500 mt-2">A confirmation has been sent on Telegram. Track your order live in My Orders.</p><button onClick={()=>{setPlaced(null); setTab('orders')}} className="mt-5 bg-espresso text-white px-6 py-3 rounded-full font-bold">Track My Order →</button></div>
      :<div className="bg-white rounded-[2rem] p-5 mt-4 card-shadow space-y-4">
        <input value={form.name} onChange={e=>setForm({...form,name:e.target.value})} placeholder="Your name *" className="w-full border rounded-2xl px-4 py-3"/>
        <input value={form.phone} onChange={e=>setForm({...form,phone:e.target.value})} placeholder="Mobile number" className="w-full border rounded-2xl px-4 py-3"/>
        <div className="flex gap-2">{['takeaway','dine-in'].map(t=>(<button key={t} onClick={()=>setForm({...form,type:t})} className={`flex-1 py-3 rounded-2xl font-bold border ${form.type===t?'bg-espresso text-white':'bg-cream'}`}>{t==='dine-in'?'🍽️ Dine-In':'🥡 Takeaway'}</button>))}</div>
        {form.type==='dine-in'&&<select value={form.table} onChange={e=>setForm({...form,table:e.target.value})} className="w-full border rounded-2xl px-4 py-3"><option value="">Select table…</option>{tables.map(t=>(<option key={t.id} value={t.number}>Table {t.number} (seats {t.capacity})</option>))}</select>}
        <textarea value={form.instructions} onChange={e=>setForm({...form,instructions:e.target.value})} placeholder="Special instructions (optional)" className="w-full border rounded-2xl px-4 py-3" rows={2}/>
        <h4 className="font-bold">Payment Method</h4>
        <div className="space-y-2">{[['upi','📱 UPI (pay at counter / on pickup)'],['razorpay','💳 Razorpay — Card / UPI Online'],['cash','💵 Cash at Counter'],['pay_at_cafe','🏪 Pay at Cafe']].map(([v,l])=>(<label key={v} className={`flex gap-2 items-center border rounded-2xl px-4 py-3 cursor-pointer ${form.payment===v?'border-amber-500 bg-amber-50':''}`}><input type="radio" checked={form.payment===v} onChange={()=>setForm({...form,payment:v})}/>{l}</label>))}</div>
        <div className="text-sm space-y-1 border-t pt-3"><div className="flex justify-between"><span>Subtotal</span><b>{fmt(cart.subtotal)}</b></div>{discount>0&&<div className="flex justify-between text-emerald-700"><span>Discount</span><b>−{fmt(discount)}</b></div>}<div className="flex justify-between"><span>GST ({gstPct}%)</span><b>{fmt(gstVal)}</b></div><div className="flex justify-between text-lg font-extrabold"><span>To Pay</span><span>{fmt(total)}</span></div></div>
        <button onClick={placeOrder} disabled={cart.items.length===0} className="w-full bg-gradient-to-r from-amber-500 to-orange-600 text-white font-extrabold py-4 rounded-full shadow-lg disabled:opacity-40">Place Order • {fmt(total)}</button>
      </div>}
    </div>}

    {tab==='orders'&&<div className="px-4 mt-4">
      <h2 className="text-2xl font-extrabold">📦 My Orders</h2>
      {orders.length===0? <p className="text-stone-500 mt-6 text-center py-10">No orders yet. Your delicious history will appear here.</p>
      : orders.map(o=>(<div key={o.id} className="bg-white rounded-[1.6rem] p-4 mt-3 card-shadow">
        <div className="flex justify-between"><b>{o.order_code}</b><span className={`px-3 py-1 rounded-full text-xs font-bold ${o.status==='cancelled'?'bg-red-100 text-red-700':'bg-amber-100 text-amber-800'}`}>{STEP_LABEL[o.status]||o.status}</span></div>
        <div className="text-sm text-stone-600 mt-1">{(o.items||[]).map((i:any)=>`${i.name} ×${i.quantity}`).join(', ')}</div>
        <div className="text-sm mt-1">Total: <b>{fmt(o.total)}</b> • {o.order_type}{o.table_number?` • Table ${o.table_number}`:''} • {o.payment_status}</div>
        {o.status!=='cancelled'&&<div className="flex items-center mt-4">{STEPS.map((s,idx)=>{ const cur=STEPS.indexOf(o.status); return <React.Fragment key={s}><div className="flex flex-col items-center"><div className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold ${idx<=cur?'bg-emerald-500 text-white':'bg-stone-200'}`}>{idx<=cur?'✓':idx+1}</div><span className="text-[9px] mt-1 w-12 text-center">{STEP_LABEL[s]}</span></div>{idx<STEPS.length-1&&<div className={`flex-1 h-1 mb-4 ${idx<cur?'bg-emerald-500':'bg-stone-200'}`}/>}</React.Fragment> })}</div>}
        <p className="text-xs text-stone-400 mt-2">Auto-refreshes every 15s • ETA ~{o.eta_mins||25} mins</p>
      </div>))}
    </div>}

    {tab==='profile'&&<div className="px-4 mt-4">
      <h2 className="text-2xl font-extrabold">👤 Profile</h2>
      <div className="bg-white rounded-[2rem] p-5 mt-4 card-shadow">
        <div className="flex items-center gap-3"><div className="w-14 h-14 rounded-full bg-espresso text-white flex items-center justify-center text-2xl font-bold">{(user.first_name||'G')[0]}</div><div><b className="text-lg">{user.first_name||'Guest'}</b><div className="text-stone-500 text-sm">@{user.username||'guest'} • via Telegram</div></div></div>
        <div className="mt-5 space-y-2 text-sm"><p>☕ <b>{settings.cafe_name||'Brew & Bite Cafe'}</b></p><p>📍 {settings.cafe_address||''}</p><p>📞 {settings.cafe_phone||''}</p><p>🕘 Open: {settings.business_hours||''}</p></div>
        <button onClick={()=>setTab('orders')} className="mt-5 w-full bg-cream py-3 rounded-2xl font-bold">📦 My Orders</button>
        <a href="/admin" className="block text-center mt-3 text-sm text-stone-500 underline">Cafe Admin Login →</a>
      </div>
      <p className="text-center text-xs text-stone-400 mt-6">Made fresh inside Telegram • Brew & Bite Cafe</p>
    </div>}

    {/* Floating cart */}
    {cart.count>0&&tab!=='cart'&&tab!=='checkout'&&<motion.button initial={{scale:0}} animate={{scale:1}} onClick={()=>setTab('cart')} className="fixed bottom-24 right-4 z-40 bg-espresso text-white pl-4 pr-5 py-3 rounded-full shadow-2xl font-bold flex items-center gap-2">🛒 {cart.count} item{cart.count>1?'s':''} • {fmt(cart.subtotal)}</motion.button>}

    {/* Bottom nav */}
    <nav className="fixed bottom-0 left-1/2 -translate-x-1/2 w-full max-w-lg z-40 glass border-t flex justify-around py-2">
      {[['home','🏠','Home'],['menu','🍽️','Menu'],['orders','📦','My Orders'],['profile','👤','Profile']].map(([t,ic,l])=>(<button key={t} onClick={()=>setTab(t as any)} className={`flex flex-col items-center px-4 py-1 rounded-2xl ${tab===t?'bg-espresso text-white':''}`}><span className="text-xl">{ic}</span><span className="text-[11px] font-bold">{l}</span></button>))}
    </nav>

    <AnimatePresence>{detail&&<DetailModal f={detail} close={()=>setDetail(null)}/>}</AnimatePresence>
  </div>
}
