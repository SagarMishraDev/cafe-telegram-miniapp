import React,{createContext,useContext,useEffect,useState} from 'react'
import { Food } from '../lib/seedData'
export interface CartItem { key:string; food:Food; qty:number; size:string; sizeDelta:number; addons:{name:string;price:number}[]; instructions:string; unit:number }
const Ctx=createContext<any>(null)
export const useCart=()=>useContext(Ctx)
export function CartProvider({children}:{children:React.ReactNode}){
  const [items,setItems]=useState<CartItem[]>(()=>{ try{return JSON.parse(localStorage.getItem('bb_cart')||'[]')}catch{return[]} })
  useEffect(()=>{ localStorage.setItem('bb_cart',JSON.stringify(items)) },[items])
  const add=(food:Food,qty=1,size='',sizeDelta=0,addons:any[]=[],instructions='')=>{
    const unit=food.price+sizeDelta+addons.reduce((s,a)=>s+a.price,0)
    const key=`${food.id}-${size}-${addons.map(a=>a.name).join(',')}-${instructions}`
    setItems(prev=>{ const ex=prev.find(i=>i.key===key); if(ex) return prev.map(i=>i.key===key?{...i,qty:i.qty+qty}:i); return [...prev,{key,food,qty,size,sizeDelta,addons,instructions,unit}] })
  }
  const updateQty=(key:string,qty:number)=> setItems(prev=> qty<=0? prev.filter(i=>i.key!==key) : prev.map(i=>i.key===key?{...i,qty}:i))
  const remove=(key:string)=> setItems(prev=>prev.filter(i=>i.key!==key))
  const clear=()=>setItems([])
  const count=items.reduce((s,i)=>s+i.qty,0); const subtotal=items.reduce((s,i)=>s+i.unit*i.qty,0)
  return <Ctx.Provider value={{items,add,updateQty,remove,clear,count,subtotal}}>{children}</Ctx.Provider>
}
