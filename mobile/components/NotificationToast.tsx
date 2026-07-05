import React, { useCallback, useEffect, useRef, useState } from 'react'
import { Animated, Platform, Pressable, StatusBar, Text, View } from 'react-native'
import { useRouter } from 'expo-router'
import { Ionicons } from '@expo/vector-icons'
import { useNotifications } from '@/contexts/NotificationContext'
import { INBOX_EVENT_TYPES, InboxNotification } from '@/types/notifications'

const DISMISS_MS = 4000

const topOffset =
  (Platform.OS === 'android' ? StatusBar.currentHeight ?? 24 : 50) + 8

const NotificationToast = () => {
  const { subscribe } = useNotifications()
  const router = useRouter()
  const [current, setCurrent] = useState<InboxNotification | null>(null)
  const translateY = useRef(new Animated.Value(-200)).current
  const hideTimer = useRef<ReturnType<typeof setTimeout> | null>(null)

  const hide = useCallback(() => {
    if (hideTimer.current) {
      clearTimeout(hideTimer.current)
      hideTimer.current = null
    }
    Animated.timing(translateY, {
      toValue: -200,
      duration: 250,
      useNativeDriver: true,
    }).start(() => setCurrent(null))
  }, [translateY])

  useEffect(() => {
    const show = (notification: InboxNotification) => {
      if (hideTimer.current) clearTimeout(hideTimer.current)
      setCurrent(notification)
      translateY.setValue(-200)
      Animated.timing(translateY, {
        toValue: 0,
        duration: 250,
        useNativeDriver: true,
      }).start()
      hideTimer.current = setTimeout(hide, DISMISS_MS)
    }

    const unsubs = INBOX_EVENT_TYPES.map((event) => subscribe(event, show))
    return () => {
      unsubs.forEach((u) => u())
      if (hideTimer.current) clearTimeout(hideTimer.current)
    }
  }, [subscribe, translateY, hide])

  const onPress = () => {
    const data = current?.data
    hide()
    if (!data) return
    if (data.conversation_id) {
      router.push({
        pathname: '/chat/[id]',
        params: { id: String(data.conversation_id) },
      })
    } else if (data.listing_id) {
      router.push({
        pathname: '/listing/[id]',
        params: { id: String(data.listing_id) },
      })
    }
  }

  if (!current) return null

  return (
    <Animated.View
      style={{
        position: 'absolute',
        top: topOffset,
        left: 12,
        right: 12,
        transform: [{ translateY }],
        zIndex: 1000,
      }}
    >
      <Pressable
        onPress={onPress}
        className="flex-row items-center bg-white rounded-2xl px-4 py-3 border border-gray-100 active:opacity-90"
        style={{
          shadowColor: '#000',
          shadowOpacity: 0.15,
          shadowRadius: 8,
          shadowOffset: { width: 0, height: 2 },
          elevation: 6,
        }}
      >
        <View className="w-9 h-9 rounded-full bg-blue-50 items-center justify-center mr-3">
          <Ionicons name="notifications" size={20} color="#2563EB" />
        </View>
        <View className="flex-1">
          <Text className="font-bold text-slate-900" numberOfLines={1}>
            {current.title}
          </Text>
          {!!current.body && (
            <Text className="text-gray-500 text-sm" numberOfLines={1}>
              {current.body}
            </Text>
          )}
        </View>
      </Pressable>
    </Animated.View>
  )
}

export default NotificationToast