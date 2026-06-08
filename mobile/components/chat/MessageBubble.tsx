import React, { useEffect, useState } from 'react'
import { View, Text, Image, Pressable } from 'react-native'
import { Ionicons } from '@expo/vector-icons'
import { Message } from '@/types/chat'

interface Props {
  message: Message
  isOwn: boolean
  showSender?: boolean
  onVisible: () => void
  onPhotoPress: (uri: string) => void
}

const PHOTO_WIDTH = 220

const ChatPhoto = ({ uri, onPress }: { uri: string; onPress: () => void }) => {
  const [aspect, setAspect] = useState(1)
  return (
    <Pressable onPress={onPress} className="mb-1">
      <Image
        source={{ uri }}
        style={{ width: PHOTO_WIDTH, aspectRatio: aspect, borderRadius: 12 }}
        resizeMode="cover"
        onLoad={(e) => {
          const { width, height } = e.nativeEvent.source
          if (width && height) setAspect(width / height)
        }}
      />
    </Pressable>
  )
}

const MessageBubble = ({ message, isOwn, showSender, onVisible, onPhotoPress }: Props) => {
  const isSending = message.status === 'sending'

  useEffect(() => {
    onVisible()
  }, [])

  const renderStatusIcon = () => {
    if (message.status === 'sending') {
      return <Ionicons name="time-outline" size={12} color="#9ca3af" />
    }
    if (message.status === 'failed') {
      return <Ionicons name="alert-circle" size={12} color="#ef4444" />
    }
    return (
      <Ionicons
        name={message.read_by.length > 0 ? 'checkmark-done' : 'checkmark'}
        size={12}
        color={message.read_by.length > 0 ? '#3b82f6' : '#9ca3af'}
      />
    )
  }

  return (
    <View
      style={{ opacity: isSending ? 0.6 : 1 }}
      className={`mb-2 max-w-[75%] ${isOwn ? 'self-end' : 'self-start'}`}
    >
      {showSender && (
        <Text className="text-xs text-gray-400 mb-0.5 px-1">{message.sender_username}</Text>
      )}

      {message.photos.map((photo) => (
        <ChatPhoto key={photo.id} uri={photo.url} onPress={() => onPhotoPress(photo.url)} />
      ))}

      {message.body ? (
        <View className={`rounded-2xl px-4 py-2 ${isOwn ? 'bg-slate-800' : 'bg-gray-100'}`}>
          <Text className={isOwn ? 'text-white' : 'text-slate-800'}>{message.body}</Text>
        </View>
      ) : null}

      <View className={`flex-row items-center mt-0.5 px-1 gap-1 ${isOwn ? 'self-end' : 'self-start'}`}>
        <Text className="text-[10px] text-gray-400">
          {new Date(message.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
        </Text>
        {isOwn && renderStatusIcon()}
      </View>
    </View>
  )
}

export default MessageBubble