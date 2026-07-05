import React, { createContext, useContext, useEffect, ReactNode } from 'react'
import { Platform, PermissionsAndroid } from 'react-native'
import { useRouter } from 'expo-router'
import axios from 'axios'
import type { FirebaseMessagingTypes } from '@react-native-firebase/messaging'
import { useAuth } from '@/contexts/AuthContext'

const API_URL = process.env.EXPO_PUBLIC_API_URL

interface PushContextType {}

const PushContext = createContext<PushContextType>({})

export const PushProvider = ({ children }: { children: ReactNode }) => {
  const { authState } = useAuth()
  const router = useRouter()

  useEffect(() => {
    if (Platform.OS !== 'android') return
    if (authState.isLoading || !authState.isAuthenticated) return

    let cancelled = false
    const unsubs: (() => void)[] = []

    const openFromMessage = (
      message: FirebaseMessagingTypes.RemoteMessage | null
    ) => {
      const data = message?.data
      if (!data) return
      if (data.event_type === 'new_message' && data.conversation_id) {
        router.push({
          pathname: '/chat/[id]',
          params: { id: String(data.conversation_id) },
        })
      }
    }

    const setup = async () => {
      try {
        if (Number(Platform.Version) >= 33) {
          await PermissionsAndroid.request(
            PermissionsAndroid.PERMISSIONS.POST_NOTIFICATIONS
          )
        }

        const {
          getMessaging,
          getToken,
          onTokenRefresh,
          onMessage,
          onNotificationOpenedApp,
          getInitialNotification,
        } = await import('@react-native-firebase/messaging')

        const messaging = getMessaging()

        const token = await getToken(messaging)
        if (cancelled) return

        await axios.post(`${API_URL}/api/notifications/devices/`, {
          token,
          platform: 'android',
        })

        unsubs.push(
          onTokenRefresh(messaging, async (newToken) => {
            try {
              await axios.post(`${API_URL}/api/notifications/devices/`, {
                token: newToken,
                platform: 'android',
              })
            } catch {}
          })
        )

        unsubs.push(onMessage(messaging, async () => {}))
        unsubs.push(onNotificationOpenedApp(messaging, openFromMessage))

        const initial = await getInitialNotification(messaging)
        if (initial && !cancelled) openFromMessage(initial)
      } catch {}
    }

    setup()

    return () => {
      cancelled = true
      unsubs.forEach((u) => u())
    }
  }, [authState.isAuthenticated, authState.isLoading, router])

  return <PushContext.Provider value={{}}>{children}</PushContext.Provider>
}

export const usePush = () => useContext(PushContext)
