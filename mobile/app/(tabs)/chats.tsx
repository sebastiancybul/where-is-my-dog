import React, { useCallback, useEffect, useState } from 'react'
import { View, Text, FlatList, ActivityIndicator, RefreshControl } from 'react-native'
import { useFocusEffect, useRouter } from 'expo-router'
import axios from 'axios'
import { useAuth } from '@/contexts/AuthContext'
import { Conversation } from '@/types/chat'
import ConversationPreview from "@/components/chat/ConversationPreview"

const API_URL = process.env.EXPO_PUBLIC_API_URL

const ChatsScreen = () => {
  const {authState} = useAuth();
  const router = useRouter();
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState('');

  const fetchConversations = async(isRefresh = false) => {
    try {
      setError('');
      if (isRefresh) setRefreshing(true)
      const res = await axios.get(`${API_URL}/api/chats/conversations/`);
      setConversations(res.data);
    } catch {
      setError('Could not load coversations.')
    } finally {
      setLoading(false)
      setRefreshing(false)
    }
  }

  useEffect(() => {
    if (!authState.isLoading && !authState.isAuthenticated) {
      router.replace('/(auth)/login')
    }
  }, [authState.isLoading, authState.isAuthenticated])

  useFocusEffect(useCallback(() => {
    if (authState.isAuthenticated) {
      fetchConversations()
    }
  }, [authState.isAuthenticated]))


  if (loading || !authState.isAuthenticated) {
    return (
    <View className="flex-1 justify-center items-center bg-white">
      <ActivityIndicator size="large" color="#1e293b" />
    </View>
    )
  }


  return (
    <View className="flex-1 bg-white">
      <View className="pt-14 px-4 pb-4 border-b border-gray-100">
        <Text className="text-2xl font-bold text-slate-800">Chats</Text>
      </View>

      <FlatList
        data={conversations}
        keyExtractor={(item) => String(item.id)}
        contentContainerStyle={{ flexGrow: 1 }}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={() => fetchConversations(true)} />
        }
        ListEmptyComponent={
          <View className="flex-1 justify-center items-center mt-32">
            {error
              ? <Text className="text-red-500">{error}</Text>
              : <Text className="text-gray-400 text-base">No conversations yet.</Text>
            }
          </View>
        }
        renderItem={({ item }) => (
          <ConversationPreview
            conversation={item}
            currentUserId={authState.user!.id}
            onPress={() => router.push({
              pathname: '/chat/[id]',
              params: {
                id: item.id,
                listing_title: item.listing_title ?? '',
                other_username: item.other_participant?.username ?? '',
              },
            })}
          />
        )}
      />
    </View>
  )
}

export default ChatsScreen