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
  listing_inquiry: InboxNotification
  listing_author_contact: InboxNotification
  location_reported: InboxNotification
  listing_expiring: InboxNotification
  listing_expired: InboxNotification
  listing_resolved: InboxNotification
  nearby_listing: InboxNotification
}

export type NotificationEventType = keyof NotificationEventMap

export const INBOX_EVENT_TYPES = [
  'listing_inquiry',
  'listing_author_contact',
  'location_reported',
  'listing_expiring',
  'listing_expired',
  'listing_resolved',
  'nearby_listing',
] as const

export interface InboxNotification {
  id: number
  event_type: string
  title: string
  body: string
  data: {
    conversation_id?: number
    listing_id?: number
    location_id?: number
    [key: string]: unknown
  }
  is_read: boolean
  created_at: string
}

export interface NotificationsPage {
  count: number
  next: string | null
  previous: string | null
  results: InboxNotification[]
}
