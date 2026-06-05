import { View, Text, Image, Pressable } from 'react-native';
import React from 'react';
import { Ionicons, MaterialIcons } from "@expo/vector-icons";
import { PhotoManage } from "@/types/listingForm";
import { pickFromLibrary, takePhoto } from '@/utils/imagePicker';

type Props = {
  photos: PhotoManage[];
  toDeletePhotos: PhotoManage[]; 
  setPhotos: (photos: PhotoManage[]) => void;
  setToDeletePhotos: (photos: PhotoManage[]) => void;
}

const PhotosStep = ({photos, setPhotos, toDeletePhotos, setToDeletePhotos}: Props) => {
  const pickImageAsync = async() => {
    const picked = await pickFromLibrary({
      mediaTypes: ['images', 'videos'],
      allowsEditing: true,
      aspect: [1, 1],
    });
    if (picked) {
      setPhotos([...photos, { type: 'new', uri: picked.uri }]);
    }
  }

  const takePhotoAsync = async () => {
    const picked = await takePhoto({
      allowsEditing: true,
      aspect: [1, 1],
    });
    if (picked) {
      setPhotos([...photos, { type: 'new', uri: picked.uri }]);
    }
  }

  const handleRemovePhoto = (idx: number) => {
    if (photos[idx].type === 'new') {
      setPhotos(photos.filter((_, i) => i !== idx))
    } else {
      setToDeletePhotos([...toDeletePhotos, photos[idx]])
      setPhotos(photos.filter((_, i) => i !== idx))
    }
  }

  const handleRestorePhoto = (id: number) => {
    const photo = toDeletePhotos.find((p) => p.id === id)
    if (!photo) return
    setToDeletePhotos(toDeletePhotos.filter((p) => p.id !== id))
    setPhotos([...photos, photo])
  }

  return (
    <View className="bg-white px-4 py-6 rounded-2xl">
      <View className="flex-row justify-between mb-1">
        <Text className="text-2xl font-bold uppercase">pictures</Text>
        <Text className="rounded-full tracking-widest text-sm bg-gray-100 px-3 py-1">{photos.length}/2</Text>
      </View>
      <Text className="text-sm text-gray-400 tracking-wide font-medium mb-4">Add up to 2 photos, the first will be the main one</Text>
      
      <View className="flex-row justify-between px-2 mb-10" >
        {!!photos[0] ? (
          <View className="w-44 h-44 bg-gray-100 rounded-xl items-center justify-center border border-dashed border-gray-400">
            <Image
              source={{ uri: photos[0].uri || photos[0].cloudinary_url }}
              className="w-full h-full rounded-xl"
            />
            <Pressable
              onPress={() => handleRemovePhoto(0)}
              className="absolute -top-2 -right-2 bg-red-500 rounded-full p-1 shadow-md active:opacity-80"
            >
              <Ionicons name="close" size={20} color="white" />
            </Pressable>
          </View>
        ) : (
          <View className="w-44 h-44 bg-gray-100 rounded-xl items-center justify-center border border-dashed border-gray-400">
            <Ionicons name="camera-outline" size={30} color="gray" />
          </View>
        )}
        
        {!!photos[1] ? (
          <View className="w-44 h-44 bg-gray-100 rounded-xl items-center justify-center border border-dashed border-gray-400">
            <Image
              source={{ uri: photos[1].uri || photos[1].cloudinary_url }}
              className="w-full h-full rounded-xl"
            />
            <Pressable
              onPress={() => handleRemovePhoto(1)}
              className="absolute -top-2 -right-2 bg-red-500 rounded-full p-1 shadow-md active:opacity-80"
            >
              <Ionicons name="close" size={20} color="white" />
            </Pressable>
          </View>
        ) : (
          <View className="w-44 h-44 bg-gray-100 rounded-xl items-center justify-center border border-dashed border-gray-400">
            <Ionicons name="camera-outline" size={30} color="gray" />
          </View>
        )}
      </View>

      {toDeletePhotos.length > 0 && (
        <View className="mb-6">
          <Text className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-3">Marked for deletion</Text>
          <View className="flex-row flex-wrap gap-3">
            {toDeletePhotos.map((photo) => (
              <View key={photo.id} className="w-20 h-20 rounded-xl overflow-hidden opacity-50">
                <Image
                  source={{ uri: photo.cloudinary_url }}
                  className="w-full h-full"
                />
                <Pressable
                  onPress={() => handleRestorePhoto(photo.id!)}
                  className="absolute inset-0 items-center justify-center bg-black/40 active:opacity-80"
                >
                  <Ionicons name="refresh" size={24} color="white" />
                </Pressable>
              </View>
            ))}
          </View>
        </View>
      )}

      <View className="flex-row px-2 justify-between gap-2">
        <Pressable
          onPress={takePhotoAsync}
          disabled={photos.length >= 2}
          className="w-44 flex-row bg-gray-800 py-3 rounded-xl border-2 border-gray-800 justify-center items-center active:opacity-80"
        >
          <Ionicons name="camera" size={24} color="white"/>
          <Text className="text-white font-semibold ml-2">Aparat</Text>
        </Pressable>

        <Pressable
          onPress={pickImageAsync}
          disabled={photos.length >= 2}
          className="w-44 flex-row bg-white border-2 border-gray-800 py-3 rounded-xl justify-center items-center active:opacity-80"
        >
          <MaterialIcons name="photo-library" size={24} color="black"/>
          <Text className="text-black font-semibold ml-2">Gallery</Text>
        </Pressable>
      </View>
      
    </View>
  )
}

export default PhotosStep