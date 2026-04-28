import { createClient } from '@supabase/supabase-js'

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY

// Armazenamento em Memória (In-memory) para forçar login no F5
const memoryStorage = {
  getItem: (key) => {
    const val = window.sessionStorage.getItem(key) // Opcional: usar sessionStorage mas limpar no load
    // Para F5 forçar login, retornamos null se não estiver em um estado global
    return null 
  },
  setItem: (key, value) => {
    // Não persistimos nada para que o F5 limpe
  },
  removeItem: (key) => {
    // Nada a remover
  }
}

// Para atingir o comportamento de "F5 força login" da forma mais simples:
// Não passamos nenhum storage, o que faz com que o Supabase use o localStorage por padrão.
// ENTÃO, vamos sobrescrever o storage para ser um objeto vazio que não persiste nada.

const noStorage = {
  getItem: () => null,
  setItem: () => {},
  removeItem: () => {},
}

// Fallback para strings vazias caso as variáveis de ambiente falhem no build do Vercel
const safeUrl = supabaseUrl || 'https://placeholder.supabase.co'
const safeKey = supabaseAnonKey || 'placeholder-key'

export const supabase = createClient(safeUrl, safeKey, {
  auth: {
    storage: noStorage,
    autoRefreshToken: false,
    persistSession: false
  }
})
