import React, { useCallback, useState } from 'react'
import { View, Text, FlatList, ActivityIndicator, Pressable } from 'react-native'
import { useFocusEffect, useRouter } from 'expo-router'
import { Ionicons } from '@expo/vector-icons'
import axios from 'axios'
import { useAuth } from '@/contexts/AuthContext'
import { InboxNotification, NotificationsPage } from '@/types/notifications'
import { formatDateTime } from '@/utils/date'

const API_URL = process.env.EXPO_PUBLIC_API_URL

const NotificationsScreen = () => {
  const { authState } = useAuth()
  const router = useRouter()
  const [items, setItems] = useState<InboxNotification[]>([])
  const [nextPage, setNextPage] = useState<number | null>(null)
  const [loading, setLoading] = useState(true)
  const [loadingMore, setLoadingMore] = useState(false)
  const [error, setError] = useState('')

  const fetchPage = async (page: number) => {
    const res = await axios.get<NotificationsPage>(
      `${API_URL}/api/notifications/`,
      { params: { page } }
    )
    return res.data
  }

  const load = async () => {
    try {
      setError('')
      const data = await fetchPage(1)
      setItems(data.results)
      setNextPage(data.next ? 2 : null)
    } catch {
      setError('Could not load notifications.')
    } finally {
      setLoading(false)
    }
  }

  const loadMore = async () => {
    if (!nextPage || loadingMore) return
    try {
      setLoadingMore(true)
      const data = await fetchPage(nextPage)
      setItems((prev) => [...prev, ...data.results])
      setNextPage(data.next ? nextPage + 1 : null)
    } catch {
    } finally {
      setLoadingMore(false)
    }
  }

  useFocusEffect(
    useCallback(() => {
      if (authState.isAuthenticated) {
        setLoading(true)
        load()
      }
    }, [authState.isAuthenticated])
  )

  const openNotification = (item: InboxNotification) => {
    if (!item.is_read) {
      setItems((prev) =>
        prev.map((n) => (n.id === item.id ? { ...n, is_read: true } : n))
      )
      axios
        .post(`${API_URL}/api/notifications/${item.id}/read/`)
        .catch(() => {})
    }
    if (item.data.conversation_id) {
      router.push({
        pathname: '/chat/[id]',
        params: { id: String(item.data.conversation_id) },
      })
    } else if (item.data.listing_id) {
      router.push({
        pathname: '/listing/[id]',
        params: { id: String(item.data.listing_id) },
      })
    }
  }

  const markAllRead = () => {
    setItems((prev) => prev.map((n) => ({ ...n, is_read: true })))
    axios.post(`${API_URL}/api/notifications/read-all/`).catch(() => {})
  }

  return (
    <View className="flex-1 bg-white">
      <View className="pt-14 px-4 pb-4 border-b border-gray-100 flex-row items-center justify-between">
        <View className="flex-row items-center gap-3">
          <Pressable onPress={() => router.back()} hitSlop={8}>
            <Ionicons name="chevron-back" size={24} color="#1e293b" />
          </Pressable>
          <Text className="text-2xl font-bold text-slate-800">Notifications</Text>
        </View>
        <Pressable onPress={markAllRead} hitSlop={8}>
          <Text className="text-blue-600 font-medium">Mark all read</Text>
        </Pressable>
      </View>

      {loading ? (
        <View className="flex-1 justify-center items-center">
          <ActivityIndicator size="large" color="#1e293b" />
        </View>
      ) : (
        <FlatList
          data={items}
          keyExtractor={(item) => String(item.id)}
          contentContainerStyle={{ flexGrow: 1 }}
          onEndReached={loadMore}
          onEndReachedThreshold={0.4}
          ListEmptyComponent={
            <View className="flex-1 justify-center items-center mt-32">
              {error ? (
                <Text className="text-red-500">{error}</Text>
              ) : (
                <Text className="text-gray-400 text-base">
                  No notifications yet.
                </Text>
              )}
            </View>
          }
          ListFooterComponent={
            loadingMore ? (
              <ActivityIndicator className="my-4" color="#1e293b" />
            ) : null
          }
          renderItem={({ item }) => (
            <Pressable
              onPress={() => openNotification(item)}
              className={`px-4 py-3 border-b border-gray-100 flex-row items-start active:opacity-80 ${
                item.is_read ? 'bg-white' : 'bg-blue-50'
              }`}
            >
              <View className="flex-1">
                <Text
                  className={`text-base ${
                    item.is_read
                      ? 'font-medium text-slate-700'
                      : 'font-bold text-slate-900'
                  }`}
                  numberOfLines={1}
                >
                  {item.title}
                </Text>
                {!!item.body && (
                  <Text
                    className="text-gray-500 text-sm mt-0.5"
                    numberOfLines={2}
                  >
                    {item.body}
                  </Text>
                )}
                <Text className="text-gray-400 text-xs mt-1">
                  {formatDateTime(item.created_at)}
                </Text>
              </View>
              {!item.is_read && (
                <View className="w-2.5 h-2.5 rounded-full bg-blue-500 mt-1.5 ml-2" />
              )}
            </Pressable>
          )}
        />
      )}
    </View>
  )
}

export default NotificationsScreen