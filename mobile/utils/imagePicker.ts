import { Alert } from 'react-native'
import * as ImagePicker from 'expo-image-picker'
import { PickedImage } from '@/types/chat'

const toPickedImage = (asset: ImagePicker.ImagePickerAsset): PickedImage => {
  const uri = asset.uri
  const filename = uri.split('/').pop() ?? 'photo.jpg'
  const match = /\.(\w+)$/.exec(filename)
  const type = match ? `image/${match[1]}` : 'image/jpeg'
  return { uri, name: filename, type, width: asset.width, height: asset.height }
}

export const pickFromLibrary = async (
  options?: ImagePicker.ImagePickerOptions
): Promise<PickedImage | null> => {
  const permission = await ImagePicker.requestMediaLibraryPermissionsAsync()
  if (!permission.granted) {
    Alert.alert('Permission required', 'Permission to access the media library is required.')
    return null
  }
  const result = await ImagePicker.launchImageLibraryAsync({
    mediaTypes: ['images'],
    quality: 0.7,
    ...options,
  })
  if (result.canceled || !result.assets?.[0]) return null
  return toPickedImage(result.assets[0])
}

export const takePhoto = async (
  options?: ImagePicker.ImagePickerOptions
): Promise<PickedImage | null> => {
  const permission = await ImagePicker.requestCameraPermissionsAsync()
  if (!permission.granted) {
    Alert.alert('Brak dostępu', 'Musisz zezwolić na dostęp do aparatu, aby zrobić zdjęcie.')
    return null
  }
  const result = await ImagePicker.launchCameraAsync({
    quality: 0.7,
    ...options,
  })
  if (result.canceled || !result.assets?.[0]) return null
  return toPickedImage(result.assets[0])
}