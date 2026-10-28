import { View, Text, Pressable, ActivityIndicator, Modal } from 'react-native'
import React, { useState } from 'react'
import { FontAwesome5 } from "@expo/vector-icons"
import { ListingCreate, LocationState, PhotoManage } from "@/types/listingForm"
import { api } from '@/utils/api';
import { useRouter } from "expo-router"
import FinalStep from "./FinalStep"

type Props = {
  listingData: ListingCreate;
  photos: PhotoManage[];
  location: LocationState;
  resetForm: () => void;
  confirmedReward: string;
  setConfirmedReward: (reward: string) => void;
}

const CreateFinalStep = ({listingData, photos, location, resetForm, confirmedReward, setConfirmedReward}: Props) => {
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string>('');
  const [success, setSuccess] = useState<boolean>(false);
  const [newListingId, setNewListingId] = useState<number | null>(null);

  const router = useRouter();

  const handleCreateListing = async () => {
    setError('');
    try {
      setLoading(true);

      const listingPayload = {
        ...listingData,
        reward_offered: !!confirmedReward ? confirmedReward : ''
      }

      const locationPayload = {
        point: {
          type: 'Point',
          coordinates: [
            location.coords!.longitude,
            location.coords!.latitude
          ]
        },
        address: location.address,
        location_type: 'approximate',
        is_primary: true,
        notes: '',
        accuracy_meters: location.radius
      }

      const resultListing = await api.post(`/listings/`, listingPayload)

      const listingId = resultListing.data.id;
      setNewListingId(listingId);

      await api.post(`/listings/${listingId}/location/`, locationPayload)

      for (let i=0; i<photos.length; i++) {
        const uri = photos[i].uri;
        const filename = uri?.split('/').pop() ?? 'photo.jpg'
        const match = /\.(\w+)/.exec(filename)
        const type = match ? `image/${match[1]}` : 'image/jpeg'
        const formData = new FormData();

        formData.append('photo', {uri, name:filename, type} as any);
        formData.append('order_index', String(i))

        await api.post(`/listings/${listingId}/upload_photo/`, formData,
          {
            headers: { 'Content-Type': 'multipart/form-data' }
          }
        )
      }

      setSuccess(true);
    } catch (e) {
      console.log(e);
      setError('Something went wrong. Please try again.');
    } finally {
      setLoading(false);
    }
  }

  return (
    <>
      <FinalStep 
        type="create"
        listingData={listingData}
        photos={photos}
        location={location}
        resetForm={resetForm}
        onSaveListing={handleCreateListing}
        loading={loading}
        error={error}
        confirmedReward={confirmedReward}
        setConfirmedReward={setConfirmedReward}
    />

      <Modal visible={loading || success} transparent animationType="fade">
        <View className="flex-1 justify-center items-center bg-black/50 px-6">
          <View className="bg-white w-full rounded-2xl p-6 items-center gap-3">

            {loading ? (
              <>
                <ActivityIndicator size="large" color="#16a34a" />
                <Text className="text-gray-800 font-bold text-lg">Creating listing...</Text>
                <Text className="text-gray-400 text-sm">Please wait a moment</Text>
              </>
            ) : (
              <>
                <FontAwesome5 name="check" size={24} color="#16a34a"/>
                <Text className="text-xl font-bold text-center text-gray-800">Listing created!</Text>
                <Text className="text-gray-500 text-center text-sm">What do you want to do next?</Text>

                <Pressable
                  className="bg-green-600 w-full py-4 rounded-xl items-center mt-2 active:opacity-80"
                  onPress={() => { resetForm(); router.push(`/listing/${newListingId}`); }}
                >
                  <Text className="text-white font-bold text-base">See my listing</Text>
                </Pressable>

                <Pressable
                  className="w-full py-3 items-center active:opacity-80"
                  onPress={() => { resetForm(); router.replace('/(tabs)'); }}
                >
                  <Text className="text-green-600 font-semibold text-base">Go to home screen</Text>
                </Pressable>
              </>
            )}

          </View>
        </View>
      </Modal>
    </>
  )
}

export default CreateFinalStep