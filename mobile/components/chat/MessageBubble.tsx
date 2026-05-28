import React, { useEffect } from 'react'
import { View, Text } from 'react-native'
import { Ionicons } from '@expo/vector-icons'
import { Message } from '@/types/chat'

interface Props {
  message: Message
  isOwn: boolean
  onVisible: () => void
}

const MessageBubble = ({ message, isOwn, onVisible }: Props) => {
  useEffect(() => {
    onVisible()
  }, [])

  return (
    <View className={`mb-2 max-w-[75%] ${isOwn ? 'self-end' : 'self-start'}`}>
      <View className={`rounded-2xl px-4 py-2 ${isOwn ? 'bg-slate-800' : 'bg-gray-100'}`}>
        {message.body ? (
          <Text className={isOwn ? 'text-white' : 'text-slate-800'}>{message.body}</Text>
        ) : null}
      </View>
      <View className={`flex-row items-center mt-0.5 px-1 gap-1 ${isOwn ? 'self-end' : 'self-start'}`}>
        <Text className="text-[10px] text-gray-400">
          {new Date(message.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
        </Text>
        {isOwn && (
          <Ionicons
            name={message.read_by.length > 0 ? 'checkmark-done' : 'checkmark'}
            size={12}
            color={message.read_by.length > 0 ? '#3b82f6' : '#9ca3af'}
          />
        )}
      </View>
    </View>
  )
}

export default MessageBubble
