import CryptoJS from 'crypto-js'

// Generate a random encryption key for the session
// In a production app, you might want to derive this from user input
const getEncryptionKey = (): string => {
  let key = sessionStorage.getItem('encryption_key')
  if (!key) {
    key = CryptoJS.lib.WordArray.random(256/8).toString()
    sessionStorage.setItem('encryption_key', key)
  }
  return key
}

export const encryptApiKey = (apiKey: string): string => {
  const key = getEncryptionKey()
  return CryptoJS.AES.encrypt(apiKey, key).toString()
}

export const decryptApiKey = (encryptedKey: string): string => {
  try {
    const key = getEncryptionKey()
    const bytes = CryptoJS.AES.decrypt(encryptedKey, key)
    return bytes.toString(CryptoJS.enc.Utf8)
  } catch (error) {
    console.error('Failed to decrypt API key:', error)
    return ''
  }
}

export const clearEncryptionKey = (): void => {
  sessionStorage.removeItem('encryption_key')
}

// API key management
export interface StoredApiKey {
  provider: 'openai' | 'anthropic' | 'gemini'
  encrypted_key: string
  created_at: string
}

export const storeApiKey = (provider: 'openai' | 'anthropic' | 'gemini', apiKey: string): void => {
  const encrypted = encryptApiKey(apiKey)
  const stored: StoredApiKey = {
    provider,
    encrypted_key: encrypted,
    created_at: new Date().toISOString()
  }
  
  localStorage.setItem(`api_key_${provider}`, JSON.stringify(stored))
}

export const getApiKey = (provider: 'openai' | 'anthropic' | 'gemini'): string | null => {
  try {
    const stored = localStorage.getItem(`api_key_${provider}`)
    if (!stored) return null
    
    const parsed: StoredApiKey = JSON.parse(stored)
    return decryptApiKey(parsed.encrypted_key)
  } catch (error) {
    console.error(`Failed to retrieve API key for ${provider}:`, error)
    return null
  }
}

export const removeApiKey = (provider: 'openai' | 'anthropic' | 'gemini'): void => {
  localStorage.removeItem(`api_key_${provider}`)
}

export const getAllApiKeys = (): Record<string, string> => {
  const keys: Record<string, string> = {}
  
  const providers: ('openai' | 'anthropic' | 'gemini')[] = ['openai', 'anthropic', 'gemini']
  
  providers.forEach(provider => {
    const key = getApiKey(provider)
    if (key) {
      keys[provider] = key
    }
  })
  
  return keys
}

export const hasApiKey = (provider: 'openai' | 'anthropic' | 'gemini'): boolean => {
  return getApiKey(provider) !== null
}

export const clearAllApiKeys = (): void => {
  const providers: ('openai' | 'anthropic' | 'gemini')[] = ['openai', 'anthropic', 'gemini']
  providers.forEach(removeApiKey)
  clearEncryptionKey()
} 