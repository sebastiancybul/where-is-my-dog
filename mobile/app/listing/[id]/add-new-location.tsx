import { View, Text, Pressable, ScrollView, TextInput, ActivityIndicator, Modal, KeyboardAvoidingView } from 'react-native';
import React, { useState } from 'react';
import { useLocalSearchParams, useRouter } from "expo-router";
import axios from 'axios';
import { Ionicons, FontAwesome5 } from "@expo/vector-icons";

import LocationPicker from "@/components/LocationPicker";
import { useAuth } from "@/contexts/AuthContext";
import { useListing } from "@/contexts/ListingContext";
import { LocationState } from "@/types/listingForm";

const AddNewLocation = () => {
  const { id } = useLocalSearchParams();
  const router = useRouter();
  const { authState } = useAuth();
  const { listing: listingData, refetch } = useListing();

  const [location, setLocation] = useState<LocationState>({
    coords: null,
    radius: 0,
    address: null,
  });
  const [notes, setNotes] = useState<string>('');
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
  const [submitSuccess, setSubmitSuccess] = useState<boolean>(false);
  const [error, setError] = useState<string>('');

  const API_URL = process.env.EXPO_PUBLIC_API_URL;

  const initialCenter = listingData?.primary_location
    ? {
        latitude: parseFloat(listingData.primary_location.latitude),
        longitude: parseFloat(listingData.primary_location.longitude),
      }
    : undefined;

  const handleSubmit = async () => {
    if (!location.coords) return;
    setError('');
    try {
      setIsSubmitting(true);
      await axios.post(`${API_URL}/api/listings/${id}/location/`, {
        point: {
          type: 'Point',
          coordinates: [
            location.coords.longitude,
            location.coords.latitude
          ]
        },
        address: location.address,
        location_type: 'approximate',
        is_primary: true,
        notes,
        accuracy_meters: location.radius
      }, {
        headers: { Authorization: `Bearer ${authState.token}` }
      });
      await refetch();
      setSubmitSuccess(true);
    } catch (e) {
      console.log(e);
      setError('Something went wrong. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <View className="flex-1 bg-gray-100">
      <KeyboardAvoidingView
        behavior='padding'
        className="flex-1"
      >
      <ScrollView contentContainerStyle={{ paddingBottom: 120 }}>
        <View className="bg-white px-4 pt-14 pb-4 rounded-b-xl mb-4">
          <View className="flex-row items-center">
            <Pressable
              className="bg-gray-50 p-2 rounded-full active:opacity-80"
              onPress={() => router.back()}
            >
              <Ionicons name="arrow-back" size={24} color="black" />
            </Pressable>
            <Text className="ml-3 text-xl font-bold">Report New Location</Text>
          </View>
          <Text className="mt-3 text-gray-600">
            Spotted this dog? Mark the place where you saw it to help track it down.
          </Text>
        </View>

        <LocationPicker
          location={location}
          setLocation={setLocation}
          includeStreetNumber
          initialCenter={initialCenter}
        />

        <View className="bg-white px-4 py-4 rounded-xl mt-4">
          <Text className="font-semibold text-gray-800 mb-2">Notes (optional)</Text>
          <TextInput
            className="border border-gray-200 rounded-xl px-4 py-3 text-base text-gray-800"
            placeholder="e.g. The dog was running towards the park"
            placeholderTextColor="#9CA3AF"
            value={notes}
            onChangeText={setNotes}
            multiline
            numberOfLines={3}
            textAlignVertical="top"
          />
        </View>

        {!!error && (
          <Text className="text-red-500 text-sm font-medium text-center mt-4 px-4">{error}</Text>
        )}
      </ScrollView>
      </KeyboardAvoidingView>

      <View className="absolute bottom-7 left-6 right-6">
        <Pressable
          onPress={handleSubmit}
          disabled={!location.coords || isSubmitting}
          className={`flex-row p-4 rounded-3xl items-center justify-center active:opacity-80 ${!location.coords ? 'bg-gray-300' : 'bg-slate-800'}`}
        >
          {isSubmitting ? (
            <ActivityIndicator color="white" />
          ) : (
            <>
              <Ionicons name="location" color="white" size={24} />
              <Text className="text-white text-xl font-bold ml-2">Report Location</Text>
            </>
          )}
        </Pressable>
      </View>

      <Modal visible={submitSuccess} transparent animationType="fade">
        <View className="flex-1 justify-center items-center bg-black/50 px-6">
          <View className="bg-white w-full rounded-2xl p-6 items-center gap-3">
            <FontAwesome5 name="check" size={24} color="#16a34a" />
            <Text className="text-xl font-bold text-center text-gray-800">Location reported!</Text>
            <Text className="text-gray-400 text-sm text-center">Thank you for helping to find this dog.</Text>
            <Pressable
              className="bg-slate-800 w-full py-4 rounded-xl items-center mt-2 active:opacity-80"
              onPress={() => router.back()}
            >
              <Text className="text-white font-bold text-base">Back to listing</Text>
            </Pressable>
          </View>
        </View>
      </Modal>
    </View>
  )
}

export default AddNewLocation
