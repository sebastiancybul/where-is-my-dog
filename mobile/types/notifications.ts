export interface NewMessagePayload {
  conversation_id: number
  last_message: {
    id: number
    body: string
    has_photo: boolean
    sender_id: number
    created_at: string
  }
}

export interface MessageReadPayload {
  conversation_id: number
  message_id: number
  read_by_user_id: number
}

export interface AllMessagesReadPayload {
  conversation_id: number
  read_by_user_id: number
}

export type NotificationEventMap = {
  new_message: NewMessagePayload
  message_read: MessageReadPayload
  all_messages_read: AllMessagesReadPayload
}

export type NotificationEventType = keyof NotificationEventMap
