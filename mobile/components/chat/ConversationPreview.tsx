import React from 'react'
import { View, Text, Image, Pressable } from 'react-native'
import { Ionicons } from '@expo/vector-icons'
import { Conversation } from '@/types/chat'

interface Props {
  conversation: Conversation
  currentUserId: number
  onPress: () => void
}

const ConversationPreview = ({ conversation, currentUserId, onPress }: Props) => {
    const other = conversation.other_participant
    const lastMsg = conversation.last_message
    const isOwnLast = lastMsg?.sender_id === currentUserId
    const isUnread = lastMsg
      ? lastMsg.sender_id !== currentUserId && !lastMsg.read_by.includes(currentUserId)
      : false
    const isRead = isOwnLast && (lastMsg?.read_by.length ?? 0) > 0

    return (
    <Pressable
      onPress={onPress}
      className="flex-row items-center px-4 py-3 border-b border-gray-50 active:bg-gray-50"
    >
      <View className="w-12 h-12 rounded-full bg-indigo-100 items-center justify-center mr-3">
        {other?.profile_photo ? (
          <Image source={{ uri: other.profile_photo }} className="w-12 h-12 rounded-full" />
        ) : (
          <Text className="text-indigo-400 font-bold text-sm uppercase">
            {other?.username?.[0] ?? '?'}
          </Text>
        )}
      </View>

      <View className="flex-1">
        <Text className="text-lg mt-1" numberOfLines={1}>
          {conversation.listing_title && (
            <Text className="text-indigo-400">{conversation.listing_title}</Text>
          )}
        </Text>
        <View className="flex-row justify-between items-center">
          <Text className={`text-lg ${isUnread ? 'font-bold' : 'font-normal'} text-slate-800`}>
            {other?.username ?? 'Unknown'}
          </Text>
          {lastMsg && (
            <Text className="text-xs text-gray-400">
              {new Date(lastMsg.created_at).toLocaleDateString()}
            </Text>
          )}
        </View>
        <Text className={`text-base ${isUnread ? 'font-bold' : 'font-normal'} text-gray-700`}>
          {!!isOwnLast && 'You: '}
          {lastMsg?.body || (lastMsg?.photos?.length ? 'Photo' : 'No messages yet')}
        </Text>
      </View>

      {isUnread ? (
        <View className="w-3 h-3 rounded-full bg-indigo-500 ml-2" />
      ) : isOwnLast ? (
        <Ionicons
          name={isRead ? 'checkmark-done' : 'checkmark'}
          size={14}
          color={isRead ? '#6366f1' : '#9ca3af'}
        />
      ) : null}
    </Pressable>
  )
}

export default ConversationPreview