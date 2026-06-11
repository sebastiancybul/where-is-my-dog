import { View, Text, Pressable, Alert, ActivityIndicator } from 'react-native';
import React, { useState } from 'react';
import axios from 'axios';
import { Ionicons } from "@expo/vector-icons";

import { useAuth } from "@/contexts/AuthContext";
import { useListing } from "@/contexts/ListingContext";
import { ListingLocation } from "@/types/listing";
import { formatDateTime } from "@/utils/date";

const LocationHistory = () => {
  const { authState } = useAuth();
  const { listing: listingData, refetch } = useListing();

  const [deletingId, setDeletingId] = useState<number | null>(null);

  const API_URL = process.env.EXPO_PUBLIC_API_URL;

  const sortedLocations = [...(listingData?.locations ?? [])].sort(
    (a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
  );

  const canDelete = (location: ListingLocation) => {
    const userId = authState.user?.id;
    if (!userId) return false;
    return userId === location.added_by_user?.id || userId === listingData?.user?.id;
  };

  const handleDelete = (location: ListingLocation) => {
    Alert.alert(
      "Delete Location",
      "Are you sure you want to delete this location report?",
      [
        { text: "Cancel", style: "cancel" },
        {
          text: "Delete",
          style: "destructive",
          onPress: async () => {
            try {
              setDeletingId(location.id);
              await axios.delete(`${API_URL}/api/listings/${listingData?.id}/locations/${location.id}/`, {
                headers: { Authorization: `Bearer ${authState.token}` },
              });
              await refetch();
            } catch (e) {
              console.log(e);
              Alert.alert('Something went wrong. Please try again.');
            } finally {
              setDeletingId(null);
            }
          },
        },
      ]
    );
  };

  if (sortedLocations.length === 0) return null;

  return (
    <View className="mb-7">
      <Text className="text-lg font-semibold mb-2">Location History</Text>
      <View className="flex gap-2">
        {sortedLocations.map((location, index) => (
          <View
            key={location.id}
            className="flex-row items-center px-4 py-3 rounded-lg bg-gray-50 border border-gray-100"
          >
            <View className={`w-7 h-7 rounded-full items-center justify-center ${location.is_primary ? 'bg-red-500' : 'bg-gray-400'}`}>
              <Text className="text-white text-xs font-bold">{sortedLocations.length - index}</Text>
            </View>

            <View className="flex-col ml-4 flex-1">
              {!!location.address && (
                <Text className="font-semibold tracking-wider">{location.address}</Text>
              )}
              <Text className="text-xs text-gray-600 mt-1">
                {formatDateTime(location.created_at)} • {location.added_by_user?.username}
              </Text>
              {!!location.notes && (
                <Text className="text-xs text-gray-500 italic mt-1">{location.notes}</Text>
              )}
            </View>

            {canDelete(location) && (
              deletingId === location.id ? (
                <ActivityIndicator size="small" color="#ef4444" />
              ) : (
                <Pressable
                  onPress={() => handleDelete(location)}
                  disabled={deletingId !== null}
                  className="p-2 active:opacity-60"
                >
                  <Ionicons name="trash-outline" size={20} color="#ef4444" />
                </Pressable>
              )
            )}
          </View>
        ))}
      </View>
    </View>
  );
};

export default LocationHistory;
