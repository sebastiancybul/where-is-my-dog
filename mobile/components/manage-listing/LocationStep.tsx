import { View, Text, ScrollView } from 'react-native';
import React, { useEffect } from 'react';
import { Ionicons } from "@expo/vector-icons";

import LocationPicker from "@/components/LocationPicker";
import { LocationState } from "@/types/listingForm";

type Props = {
  location: LocationState;
  setLocation: (location: LocationState) => void;
  listingType: 'lost' | 'found';
  setCanContinue: (flag: boolean) => void;
}

const LocationStep = ({location, setLocation, listingType, setCanContinue}: Props) => {
  useEffect(() => {
    setCanContinue(location.coords !== null);
  }, [location.coords]);

  return (
    <ScrollView
      contentContainerStyle={{ paddingBottom: 400 }}
    >
      <LocationPicker
        location={location}
        setLocation={setLocation}
        includeStreetNumber={listingType === 'found'}
      >
        <View className="flex-row items-center mb-2">
          <Ionicons name="location-sharp" size={24} />
          <Text className="ml-2 uppercase text-xl font-semibold">location</Text>
        </View>
        <Text className="mb-4 text-gray-700">Choose your dog&apos;s location.</Text>
      </LocationPicker>
    </ScrollView>
  )
}

export default LocationStep
