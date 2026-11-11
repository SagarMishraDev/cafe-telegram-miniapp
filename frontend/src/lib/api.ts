// API client: talks to FastAPI backend (VITE_API_URL). If backend is unreachable
// (e.g. static preview), falls back to bundled seed data mirroring the backend seed
// so every screen stays fully clickable; orders then simulate locally.
import { FOODS, CATEGORIES, COUPONS, TABLES, calcDiscount, Food } from './seedData'
export const API_URL = (import.meta as any).env?.VITE_API_URL || 'http://localhost:8000'
declare global { interface Window { Telegram?: any } }
export const tg = () => window.Telegram?.WebApp
export function initTelegram(){
  const w=tg(); if(w){ try{ w.ready(); w.expand() }catch{} }
  return w
}
export function tgUser(){
  const u=tg()?.initDataUnsafe?.user
  return u ? { first_name:u.first_name, username:u.username||'', id:u.id } : { first_name:'Guest', username:'dev_guest', id:0 }
}
export function haptic(){ try{ tg()?.HapticFeedback?.impactOccurred('light') }catch{} }
let token = localStorage.getItem('bb_token')||''
let authInFlight: Promise<string>|null = null
export function ensureAuth(): Promise<string>{
  if(token) return Promise.resolve(token)
  // Dedupe concurrent auth calls (React double effects, parallel requests):
  // they all share one in-flight /api/auth/telegram request.
  if(!authInFlight){
    authInFlight=(async()=>{
      try{
        const r=await fetch(`${API_URL}/api/auth/telegram`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({initData: tg()?.initData||''})})
        if(r.ok){ const d=await r.json(); token=d.access_token; localStorage.setItem('bb_token',token) }
      }catch{}
      authInFlight=null
      return token
    })()
  }
  return authInFlight
}
function clearToken(){
  token=''
  try{ localStorage.removeItem('bb_token') }catch{}
}
async function rawReq(path:string, opts:any, t:string){
  return fetch(`${API_URL}${path}`,{...opts,headers:{'Content-Type':'application/json',...(t?{Authorization:`Bearer ${t}`}:{}),...(tg()?.initData?{'X-Init-Data':tg().initData}:{}) ,...(opts.headers||{})}})
}
async function req(path:string, opts:any={}){
  let t=await ensureAuth()
  let r=await rawReq(path,opts,t)
  if(r.status===401){
    // Stored token expired/was rejected: drop it, re-authenticate once,
    // and retry the request once — otherwise this client stays logged-out
    // (and silently stuck on stale local data) forever.
    clearToken()
    t=await ensureAuth()
    r=await rawReq(path,opts,t)
  }
  if(!r.ok) throw new Error(await r.text())
  return r.json()
}
export const api={
  async categories(){ try{ return await req('/api/categories') }catch{ return CATEGORIES } },
  async menu(search='',cat=0,veg=false):Promise<Food[]>{ try{ return await req(`/api/menu?search=${encodeURIComponent(search)}&category_id=${cat}&veg_only=${veg}`) }catch{ return FOODS.filter(f=>(!cat||f.category_id===cat)&&(!veg||f.is_veg)&&(!search||f.name.toLowerCase().includes(search.toLowerCase()))) } },
  async tables(){ try{ return await req('/api/tables') }catch{ return TABLES } },
  async settings(){ try{ return await req('/api/settings') }catch{ return {cafe_name:'Brew & Bite Cafe',cafe_tagline:'Good vibes, great bites',business_hours:'9:00 AM – 11:00 PM',cafe_phone:'+91 98765 43210',cafe_address:'MG Road, Jaipur',gst_percent:'5'} } },
  async validateCoupon(code:string, subtotal:number){ try{ return await req('/api/coupons/validate',{method:'POST',body:JSON.stringify({code,subtotal})}) }catch{ const d=calcDiscount(code,subtotal); return {valid:d>0,discount:d,message:d>0?`Saved ₹${d}`:'Coupon not valid for this amount'} } },
  async createOrder(payload:any){
    try{ return await req('/api/orders',{method:'POST',body:JSON.stringify(payload)}) }
    catch{
      // local simulation for offline preview
      const subtotal=payload.items.reduce((s:number,it:any)=>{ const f=FOODS.find(x=>x.id===it.food_item_id)!; const sd=f.sizes.find(z=>z.name===it.size)?.delta||0; const ad=(it.addons||[]).reduce((a:number,x:any)=>a+(f.addons.find(z=>z.name===(x.name||x))?.price||0),0); return s+(f.price+sd+ad)*it.quantity },0)
      const discount=calcDiscount(payload.coupon_code||'',subtotal); const gst=Math.round((subtotal-discount)*0.05*100)/100
      const order={id:Date.now(),order_code:'BB'+Math.random().toString(16).slice(2,10).toUpperCase(),...payload,status:'placed',payment_status:payload.payment_method==='cash'?'pay_at_cafe':'pending',subtotal,discount,gst_amount:gst,total:Math.round((subtotal-discount+gst)*100)/100,eta_mins:25,created_at:new Date().toISOString(),items:payload.items.map((it:any)=>{const f=FOODS.find(x=>x.id===it.food_item_id)!;return{name:f.name,price:f.price,quantity:it.quantity,size:it.size||'',line_total:f.price*it.quantity}})}
      const prev=JSON.parse(localStorage.getItem('bb_local_orders')||'[]'); prev.unshift(order); localStorage.setItem('bb_local_orders',JSON.stringify(prev)); return order
    }
  },
  async myOrders(){
    try{
      const r=await req('/api/orders/my')
      const server=Array.isArray(r)?r:[]
      const local=JSON.parse(localStorage.getItem('bb_local_orders')||'[]')
      // Merge by order_code with the SERVER version always winning for
      // shared codes: a stale local copy must never freeze the status of
      // an order the server knows about. Local-only orders (created while
      // the backend was genuinely unreachable) still show.
      const byCode=new Map<string,any>()
      for(const o of local){ if(o&&o.order_code) byCode.set(o.order_code,o) }
      for(const o of server){ if(o&&o.order_code) byCode.set(o.order_code,o) }
      const merged=[...byCode.values()]
      merged.sort((a,b)=>String(b.created_at||'').localeCompare(String(a.created_at||'')))
      return merged
    }catch{ return JSON.parse(localStorage.getItem('bb_local_orders')||'[]') }
  },
}
export const adminApi={
  base: API_URL,
  async call(path:string, opts:any={}, tok:string){
    const r=await fetch(`${API_URL}${path}`,{...opts,headers:{'Content-Type':'application/json',Authorization:`Bearer ${tok}`}})
    if(!r.ok) throw new Error(await r.text()); return r.json()
  }
}
