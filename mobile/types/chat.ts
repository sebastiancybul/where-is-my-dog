 export interface MessagePhoto {
  id: number
  url: string
  uploaded_at: string
}

export interface Message {
  id: number
  body: string
  photos: MessagePhoto[]
  sender_id: number
  sender_username: string
  created_at: string
  read_by: number[]
}

export interface OtherParticipant {
  id: number
  username: string
  profile_photo: string | null
}

export interface Conversation {
  id: number
  type: 'public' | 'private'
  listing_id: number | null
  listing_title: string | null
  is_closed: boolean
  last_message: Message | null
  other_participant: OtherParticipant | null
  created_at: string
}

export type WsIncomingMessage =
  | {
      type: 'chat_message'
      message_id: number
      body: string
      sender_id: number
      sender_username: string
      created_at: string
    }
  | {
      type: 'message_read'
      message_id: number
      user_id: number
      username: string
    }
  | {
      type: 'all_messages_read'
      user_id: number
      username: string
    }
  | {
      type: 'error'
      code: string
    }
