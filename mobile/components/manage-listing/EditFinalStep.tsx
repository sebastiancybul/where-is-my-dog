import { View, Text, Pressable, ActivityIndicator, Modal } from 'react-native'
import React, { useState } from 'react'
import { FontAwesome5 } from "@expo/vector-icons"
import { ListingCreate, LocationState, PhotoManage } from "@/types/listingForm"
import { useAuth } from "@/contexts/AuthContext"
import { api } from '@/utils/api';
import { useRouter } from "expo-router"
import FinalStep from "./FinalStep"
import { ListingItem } from "@/types/listing"

type Props = {
  listingData: ListingCreate;
  photos: PhotoManage[];
  location: LocationState;
  resetForm: () => void;
  confirmedReward: string;
  setConfirmedReward: (reward: string) => void;
  initialListing: ListingItem;
  listingId: string;
  toDeletePhotos: PhotoManage[];
}

const EditFinalStep = ({listingData, photos, location, resetForm, confirmedReward, setConfirmedReward, initialListing, toDeletePhotos, listingId}: Props) => {
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string>('');
  const [success, setSuccess] = useState<boolean>(false);

  const { authState } = useAuth();
  const router = useRouter();

  const handleUpdateListing = async () => {
    setError('');
    try {
      setLoading(true);

      const headers = { Authorization: `Bearer ${authState.token}` };

      // 1. Update listing data
      await api.patch(`/listings/${listingId}/`, {
        ...listingData,
        reward_offered: confirmedReward || '',
      }, { headers });

      // 2. Delete removed photos
      await Promise.all(
        toDeletePhotos.map(photo =>
          api.delete(`/listings/${listingId}/photos/${photo.id}/`, { headers })
        )
      );

      // 3. Upload new photos
      const newPhotos = photos.filter(p => p.type === 'new');
      const remainingExistingCount = photos.filter(
        p => p.type === 'existing' && !toDeletePhotos.find(d => d.id === p.id)
      ).length;

      for (let i = 0; i < newPhotos.length; i++) {
        const { uri } = newPhotos[i];
        const filename = uri?.split('/').pop() ?? 'photo.jpg';
        const match = /\.(\w+)/.exec(filename);
        const type = match ? `image/${match[1]}` : 'image/jpeg';
        const formData = new FormData();
        formData.append('photo', { uri, name: filename, type } as any);
        formData.append('order_index', String(remainingExistingCount + i));
        await api.post(`/listings/${listingId}/upload_photo/`, formData, {
          headers: { ...headers, 'Content-Type': 'multipart/form-data' },
        });
      }

      // 4. Update location if changed. Assumes a single location per listing;
      const initialLocation = initialListing.primary_location ?? initialListing.locations[0];
      if (initialLocation) {
        const locationChanged =
          location.coords!.latitude  !== initialLocation.point.coordinates[1] ||
          location.coords!.longitude !== initialLocation.point.coordinates[0] ||
          location.radius            !== initialLocation.accuracy_meters;

        if (locationChanged) {
          await api.delete(
            `/listings/${listingId}/locations/${initialLocation.id}/`,
            { headers }
          );
          await api.post(`/listings/${listingId}/location/`, {
            point: {
              type: 'Point',
              coordinates: [location.coords!.longitude, location.coords!.latitude],
            },
            address: location.address,
            location_type: 'approximate',
            is_primary: true,
            notes: '',
            accuracy_meters: location.radius,
          }, { headers });
        }
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
        type="edit"
        listingData={listingData}
        photos={photos}
        location={location}
        resetForm={resetForm}
        onSaveListing={handleUpdateListing}
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
                <Text className="text-gray-800 font-bold text-lg">Updating listing...</Text>
                <Text className="text-gray-400 text-sm">Please wait a moment</Text>
              </>
            ) : (
              <>
                <FontAwesome5 name="check" size={24} color="#16a34a"/>
                <Text className="text-xl font-bold text-center text-gray-800">Listing updated!</Text>
                <Text className="text-gray-500 text-center text-sm">Your listing has been saved.</Text>

                <Pressable
                  className="bg-green-600 w-full py-4 rounded-xl items-center mt-2 active:opacity-80"
                  onPress={() => { resetForm(); router.back(); }}
                >
                  <Text className="text-white font-bold text-base">Back to listing</Text>
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

export default EditFinalStep