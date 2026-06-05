import axios from 'axios'
import { Message, PickedImage } from '@/types/chat'

const API_URL = process.env.EXPO_PUBLIC_API_URL

export const uploadChatImage = async (
  conversationId: string | number,
  image: PickedImage
): Promise<Message> => {
  const formData = new FormData()
  formData.append('image', {
    uri: image.uri,
    name: image.name,
    type: image.type,
  } as any)

  const res = await axios.post(
    `${API_URL}/api/chats/conversations/${conversationId}/upload_image/`,
    formData,
    { headers: { 'Content-Type': 'multipart/form-data' } }
  )
  return res.data
}