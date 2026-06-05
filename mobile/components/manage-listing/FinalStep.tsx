import { View, Text, Pressable, Switch, TextInput, Keyboard, Image, ScrollView } from 'react-native'
import React, { useState } from 'react'
import { Ionicons, FontAwesome5, MaterialCommunityIcons } from "@expo/vector-icons"
import ListingCard from "../ListingCard"
import { ListingCreate, LocationState, PhotoManage } from "@/types/listingForm"

import MapView, { Circle, Marker } from "react-native-maps"

type Props = {
  type: 'create' | 'edit';
  listingData: ListingCreate;
  photos: PhotoManage[];
  location: LocationState;
  resetForm: () => void;
  onSaveListing: () => void;
  loading: boolean;
  error: string;
  confirmedReward: string;
  setConfirmedReward: (reward: string) => void;
}

const FinalStep = ({type, listingData, photos, location, onSaveListing, loading, error, confirmedReward, setConfirmedReward}: Props) => {
  const [rewardActive, setRewardActive] = useState<boolean>(!!confirmedReward);
  const [reward, setReward] = useState<string>(confirmedReward);
  const [isConfirmed, setIsConfirmed] = useState<boolean>(!!confirmedReward);

  const toggleReward = (value: boolean) => {
    setRewardActive(value);
    if (!value) {
      setReward("0");
      setIsConfirmed(false);
      setConfirmedReward("");
    }
  };

  const handleConfirm = () => {
    if (reward.length > 0) {
      setIsConfirmed(true);
      setConfirmedReward(reward);
      Keyboard.dismiss();
    }
  };

  return (
    <>
      <ScrollView
        contentContainerStyle={{ paddingBottom: 400 }}
      >
        {listingData.type=="lost" && (
          <View className="bg-white mb-4 px-4 py-3 rounded-2xl shadow-sm border border-gray-100">
            <View className="flex-row justify-between items-center">
              <View className="flex-row items-center">
                <View className={`p-2 rounded-lg ${rewardActive ? 'bg-yellow-100' : 'bg-gray-100'}`}>
                  <FontAwesome5 name="medal" size={16} color={rewardActive ? "#FFB800" : "#9CA3AF"} />
                </View>
                <Text className="font-bold ml-3 text-gray-800 text-[15px]">Award</Text>
              </View>
              <Switch
                value={rewardActive}
                onValueChange={toggleReward}
              />
            </View>

            {rewardActive && (
              <View className="mt-4">
                <View
                  className={`flex-row items-center border-2 rounded-xl px-3 py-1 ${
                    isConfirmed ? 'border-green-500 bg-green-50' : 'border-gray-200 bg-white'
                  }`}
                >
                  <TextInput
                    value={reward}
                    onChangeText={(text) => {
                      setReward(text);
                      setIsConfirmed(false);
                    }}
                    placeholder="Enter amount..."
                    keyboardType="numeric"
                    returnKeyType="done"
                    onSubmitEditing={handleConfirm}
                    className="flex-1 leading-tight h-12 text-gray-900 font-semibold text-lg"
                  />

                  <View className="flex-row items-center">
                    <Text className="mr-3 font-bold text-gray-400">PLN</Text>

                    <Pressable
                      onPress={handleConfirm}
                      disabled={reward.length === 0 || isConfirmed}
                      hitSlop={10}
                      className={`flex-row items-center px-3 py-2 rounded-lg active:scale-90 ${
                        isConfirmed ? 'bg-green-500' : 'bg-gray-600'
                      } ${reward.length === 0 ? 'opacity-50' : 'opacity-100'}`}
                    >
                      <Text className="text-white font-bold text-xs mr-1">
                        {isConfirmed ? 'OK' : 'SET'}
                      </Text>
                      <FontAwesome5
                        name={isConfirmed ? "check" : "chevron-right"}
                        size={10}
                        color="white"
                      />
                    </Pressable>
                  </View>
                </View>

                {!isConfirmed && reward.length > 0 && (
                  <Text className="text-blue-500 text-[10px] mt-1 ml-1 font-medium italic">
                    Tap &quot;Set&quot; to save the amount
                  </Text>
                )}
              </View>
            )}

          </View>
        )}

        <View className="bg-white px-4 py-4 rounded-xl items-center justify-center mb-4">
          <Ionicons name="document-text-outline" size={34} color="gray" />
          <Text className="text-gray-400 font-bold">Summary Preview</Text>
          <Text className="text-sm text-gray-400 font-semibold">Review all your data before submitting the listing</Text>
        </View>

        <ListingCard
          item={{
            ...listingData,
            id: 0,
            status: 'active',
            primary_location: location.address,
            primary_photo: photos[0].uri || photos[0].cloudinary_url || null,
            created_at: '2000-01-01',
            reward_offered: reward,
            has_collar: listingData.has_collar ?? false,
            collar_color: listingData.collar_color ?? '',
            breed: listingData.breed ?? null,
            color: listingData.color ?? null,
            dog_name: listingData.dog_name ?? null,
            age_estimate: listingData.age_estimate ?? null,
          }}
          isPreview={true}
        />

        <View className="bg-white px-4 py-4 rounded-2xl mb-4 border border-gray-100 shadow-sm gap-4">
          <View>
            <Text className="font-bold text-gray-800 text-base mb-2">Full Description</Text>
            <Text>{listingData.description}</Text>
          </View>
          <Text className="font-bold text-gray-800 text-base">More details</Text>

          <View className="flex-row gap-2">
            {!!listingData.size && (
              <View className="flex-row items-center bg-gray-100 px-3 py-2 rounded-xl gap-2">
                <MaterialCommunityIcons name="ruler" size={16} color="#6b7280" />
                <Text className="text-gray-700 font-semibold text-sm capitalize">{listingData.size}</Text>
              </View>
            )}
            {!!listingData.gender && (
              <View className="flex-row items-center bg-gray-100 px-3 py-2 rounded-xl gap-2">
                <Ionicons
                  name={listingData.gender === 'male' ? 'male' : listingData.gender === 'female' ? 'female' : 'help-circle-outline'}
                  size={16}
                  color="#6b7280"
                />
                <Text className="text-gray-700 font-semibold text-sm capitalize">{listingData.gender}</Text>
              </View>
            )}
          </View>

          {!!listingData.special_marks && (
            <View className="bg-red-50 border border-red-100 rounded-xl p-3 gap-1">
              <Text className="text-red-400 text-xs font-bold uppercase tracking-wider">Special Marks</Text>
              <Text className="text-red-900 font-semibold">{listingData.special_marks}</Text>
            </View>
          )}

          {listingData.type === 'found' && !!listingData.fostering_address && (
            <View className="gap-1">
              <Text className="text-gray-400 text-xs font-bold uppercase tracking-wider">Fostering address</Text>
              <View className="flex-row items-center gap-2">
                <Ionicons name="home-outline" size={16} color="#6b7280" />
                <Text className="text-gray-700 font-semibold">{listingData.fostering_address}</Text>
              </View>
            </View>
          )}

          {(!!location.address || !!location.coords) && (
            <View className="relative">
              <MapView
                style={{height: 300, borderRadius:12, marginBottom:10}}
                initialRegion={{
                  latitude: location.coords!.latitude,
                  longitude: location.coords!.longitude,
                  latitudeDelta: 0.01,
                  longitudeDelta: 0.01,
                }}
              >
                <>
                  <Marker
                    coordinate={location.coords!}
                  />
                  <Circle
                    center={location.coords!}
                    radius={location.radius}
                    fillColor="rgba(0,0,255,0.1)"
                    strokeColor="blue"
                  />
                </>
              </MapView>

                <View className="absolute top-2 left-2 right-2 bg-white/90 p-2 rounded-lg z-50">
                  <Text className="text-red-500">{location.address}</Text>
                </View>
            </View>
          )}

          {photos.length > 1 && (
            <View className="gap-2">
              <Text className="text-gray-400 text-xs font-bold uppercase tracking-wider">Photos</Text>
              <ScrollView horizontal showsHorizontalScrollIndicator={false} className="flex-row gap-2">
                {photos.map((photo, i) => (
                  <Image key={i} source={{ uri: photo.uri }} className="w-24 h-24 rounded-xl mr-2" />
                ))}
              </ScrollView>
            </View>
          )}
        </View>
        
        {!!error && (
          <Text className="text-red-500 text-sm font-medium text-center mb-2">{error}</Text>
        )}

        <Pressable
          onPress={onSaveListing}
          disabled={loading}
          className={`items-center bg-green-600 rounded-2xl py-4 active:opacity-80 ${loading ? 'opacity-60' : ''}`}
        >
          <Text className="text-white font-bold text-xl">
            {type=='create' ? 'Create Listing' : 'Update Listing'}
          </Text>
        </Pressable>

      </ScrollView>

    </>
  )
}

export default FinalStep