import { api } from '@/utils/api'
import { Message, PickedImage } from '@/types/chat'

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

  const res = await api.post(
    `/chats/conversations/${conversationId}/upload_image/`,
    formData,
    { headers: { 'Content-Type': 'multipart/form-data' } }
  )
  return res.data
}