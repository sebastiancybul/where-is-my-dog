import { useListing } from "@/contexts/ListingContext";
import React from 'react';
import ListingFormScreen from "@/components/manage-listing/ListingFormScreen";
import { View, Text, Pressable } from "react-native";
import { useRouter } from "expo-router";

const Edit = () => {
  const { listing: listingData } = useListing()
  const router = useRouter();

  return (
    <View className="pt-safe flex-1">
      <View className="flex-row justify-end px-4 pt-2">
        <Pressable onPress={() => router.back()} className="active:opacity-80">
          <Text className="text-gray-500 font-medium px-10">Cancel</Text>
        </Pressable>
      </View>
      <ListingFormScreen mode="edit" initialListing={listingData} />
    </View>
  )
}

export default Edit