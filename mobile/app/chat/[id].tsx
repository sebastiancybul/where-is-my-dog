import React, { useCallback, useRef, useState } from 'react'
import {
  View, Text, FlatList, TextInput, Pressable,
  ActivityIndicator, KeyboardAvoidingView, Platform,
} from 'react-native'
import { useFocusEffect, useLocalSearchParams, useRouter } from 'expo-router'
import axios from 'axios'
import { Ionicons } from '@expo/vector-icons'
import { useAuth } from '@/contexts/AuthContext'
import { Message, WsIncomingMessage } from '@/types/chat'
import MessageBubble from '@/components/chat/MessageBubble'

const API_URL = process.env.EXPO_PUBLIC_API_URL
const WS_URL = process.env.EXPO_PUBLIC_WS_URL

const ConversationScreen = () => {
  const { id, listing_title, other_username } = useLocalSearchParams<{
    id: string
    listing_title: string
    other_username: string
  }>();
  const { authState } = useAuth();
  const router = useRouter();

  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(true);
  const [wsConnected, setWsConnected] = useState(false);
  const [input, setInput] = useState('');
  const wsRef = useRef<WebSocket | null>(null);

  const fetchMessages = async () => {
    try {
      const res = await axios.get(`${API_URL}/api/chats/conversations/${id}/messages/`);
      const data = res.data.results ?? res.data;
      setMessages(data);
    } finally {
      setLoading(false);
    }
  }

  const connectWs = async () => {
    try {
      const res = await axios.post(`${API_URL}/api/chats/ws-ticket/`);
      const ticket = res.data.ticket;
      const ws = new WebSocket(`${WS_URL}/ws/chats/${id}/?ticket=${ticket}`);
      wsRef.current = ws;

      ws.onopen = () => setWsConnected(true)
      ws.onclose = () => setWsConnected(false)

      ws.onmessage = (event) => {
        const data: WsIncomingMessage = JSON.parse(event.data);

        if (data.type === 'chat_message') {
          const newMessage: Message = {
            id: data.message_id,
            body: data.body,
            photos: [],
            sender_id: data.sender_id,
            sender_username: data.sender_username,
            created_at: data.created_at,
            read_by: [],
          }
          setMessages((prev) => [newMessage, ...prev])
        }

        if (data.type === 'message_read') {
          setMessages((prev) =>
            prev.map((m) =>
              m.id === data.message_id && !m.read_by.includes(data.user_id)
                ? { ...m, read_by: [...m.read_by, data.user_id] }
                : m
            )
          )
        }

        if (data.type === 'all_messages_read') {
          setMessages((prev) =>
            prev.map((m) =>
              m.sender_id !== data.user_id && !m.read_by.includes(data.user_id)
                ? { ...m, read_by: [...m.read_by, data.user_id] }
                : m
            )
          )
        }
      }
    } catch (e) {
      console.log('WS connect error', e)
    }
  }

  useFocusEffect(
    useCallback(() => {
      setLoading(true)
      fetchMessages()
      connectWs()
      return () => {
        wsRef.current?.close()
        wsRef.current = null
      }
    }, [id])
  )

  const sendMessage = () => {
    const body = input.trim()
    if (!body || !wsRef.current || !wsConnected ) return
    wsRef.current.send(JSON.stringify({ type: 'chat_message', body }))
    setInput('')
  }

  const markRead = (messageId: number) => {
    if (!wsConnected) return
    wsRef!.current!.send(JSON.stringify({ type: 'mark_read', message_id: messageId }))
  }

  if (loading) {
    return (
      <View className="flex-1 justify-center items-center bg-white">
        <ActivityIndicator size="large" color="#1e293b" />
      </View>
    )
  }

  return (
    <KeyboardAvoidingView
      className="flex-1 bg-white"
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
    >
      <View className="pt-14 px-4 pb-3 border-b border-gray-100 flex-row items-center gap-3">
        <Pressable onPress={() => router.back()} className="active:opacity-60">
          <Ionicons name="arrow-back" size={24} color="#1e293b" />
        </Pressable>
        <View className="flex-1">
          {listing_title ? (
            <Text className="text-lg text-indigo-400 font-medium" numberOfLines={1}>{listing_title}</Text>
          ) : null}
          <Text className="text-base font-bold text-slate-800" numberOfLines={1}>
            {other_username || 'Conversation'}
          </Text>
        </View>
      </View>

      <FlatList
        data={messages}
        keyExtractor={(item) => String(item.id)}
        extraData={messages}
        inverted
        contentContainerStyle={{ padding: 12 }}
        renderItem={({ item }) => (
          <MessageBubble
            message={item}
            isOwn={item.sender_id === authState.user!.id}
            onVisible={() => {
              if (
                item.sender_id !== authState.user!.id &&
                !item.read_by.includes(authState.user!.id)
              ) {
                markRead(item.id)
              }
            }}
          />
        )}
      />

      <View className="flex-row items-center px-3 py-2 border-t border-gray-100 gap-2">
        <TextInput
          value={input}
          onChangeText={setInput}
          placeholder="Type a message..."
          placeholderTextColor="#9ca3af"
          className="flex-1 bg-gray-100 rounded-2xl px-4 py-4 text-base mb-6"
          multiline
        />
        <Pressable
          onPress={sendMessage}
          disabled={!wsConnected}
          className={`w-10 h-10 rounded-full items-center justify-center mb-6 ${wsConnected ? 'bg-slate-800 active:opacity-70' : 'bg-gray-300'}`}
        >
          <Ionicons name="send" size={18} color="white" />
        </Pressable>
      </View>
    </KeyboardAvoidingView>
  )
}

export default ConversationScreen