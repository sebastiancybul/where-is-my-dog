import React, { createContext, useContext, useEffect, ReactNode } from 'react'
import { Platform, PermissionsAndroid } from 'react-native'
import axios from 'axios'
import { useAuth } from '@/contexts/AuthContext'

const API_URL = process.env.EXPO_PUBLIC_API_URL

interface PushContextType {}

const PushContext = createContext<PushContextType>({})

export const PushProvider = ({ children }: { children: ReactNode }) => {
  const { authState } = useAuth()

  useEffect(() => {
    if (Platform.OS !== 'android') return
    if (authState.isLoading || !authState.isAuthenticated) return

    let cancelled = false
    let unsubscribe: (() => void) | undefined

    const register = async () => {
      try {
        if (Number(Platform.Version) >= 33) {
          await PermissionsAndroid.request(
            PermissionsAndroid.PERMISSIONS.POST_NOTIFICATIONS
          )
        }

        const { getMessaging, getToken, onTokenRefresh } = await import(
          '@react-native-firebase/messaging'
        )

        const messaging = getMessaging()

        const token = await getToken(messaging)
        if (cancelled) return

        await axios.post(`${API_URL}/api/notifications/devices/`, {
          token,
          platform: 'android',
        })

        unsubscribe = onTokenRefresh(messaging, async (newToken) => {
          try {
            await axios.post(`${API_URL}/api/notifications/devices/`, {
              token: newToken,
              platform: 'android',
            })
          } catch {}
        })
      } catch {}
    }

    register()

    return () => {
      cancelled = true
      unsubscribe?.()
    }
  }, [authState.isAuthenticated, authState.isLoading])

  return <PushContext.Provider value={{}}>{children}</PushContext.Provider>
}

export const usePush = () => useContext(PushContext)
