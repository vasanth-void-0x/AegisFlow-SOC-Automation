import { createContext, useContext, useEffect, useState, type ReactNode } from 'react'
import { api } from '../api/client'
export type AuthUser={id:string;username:string;display_name:string;role:'admin'|'analyst'|'viewer';is_active:boolean}
type AuthState={loading:boolean;enabled:boolean;user:AuthUser|null;login:(u:string,p:string)=>Promise<void>;logout:()=>Promise<void>}
const Context=createContext<AuthState|null>(null)
export function AuthProvider({children}:{children:ReactNode}){const [loading,setLoading]=useState(true),[enabled,setEnabled]=useState(false),[user,setUser]=useState<AuthUser|null>(null);useEffect(()=>{api.authConfig().then(async c=>{setEnabled(c.enabled);if(c.enabled&&c.initialized)setUser(await api.currentUser().catch(()=>null))}).finally(()=>setLoading(false))},[]);return <Context.Provider value={{loading,enabled,user,login:async(u,p)=>setUser(await api.login(u,p)),logout:async()=>{await api.logout();setUser(null)}}}>{children}</Context.Provider>}
export function useAuth(){const value=useContext(Context);if(!value)throw new Error('AuthProvider missing');return value}
