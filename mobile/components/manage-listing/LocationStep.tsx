import { View, Text, Pressable, Alert, ScrollView } from 'react-native';
import React, { useEffect, useRef } from 'react';
import { Ionicons } from "@expo/vector-icons";

import * as Location from 'expo-location';
import MapView, { Marker, Circle } from 'react-native-maps';

import Slider from '@react-native-community/slider'
import { LocationState } from "@/types/listingForm";

type Props = {
  location: LocationState;
  setLocation: (location: LocationState) => void;
  listingType: 'lost' | 'found';
  setCanContinue: (flag: boolean) => void;
}

const LocationStep = ({location, setLocation, listingType, setCanContinue}: Props) => {
  const { coords, radius, address } = location;

  const mapRef = useRef<MapView>(null);

  useEffect(() => {
    setCanContinue(coords !== null);
  }, [coords]);

  const getCurrentLocationAsync = async () => {
    let { status } = await Location.requestForegroundPermissionsAsync();
    if (status !== 'granted') {
      Alert.alert('Permission to access location was denied');
      return;
    }

    const loc = await Location.getCurrentPositionAsync({});
    const newCoords = { latitude: loc.coords.latitude, longitude: loc.coords.longitude };

    mapRef.current?.animateToRegion({
      latitude: loc.coords.latitude,
      longitude: loc.coords.longitude,
      latitudeDelta: 0.01,
      longitudeDelta: 0.01
    }, 800);

    resolveAddressAsync(newCoords);
  }

  const resolveAddressAsync = async (newCoords: { latitude: number; longitude: number }) => {
    const results = await Location.reverseGeocodeAsync(newCoords);
    if (results.length > 0) {
      const r = results[0];

      const street = [r.street, listingType === 'found' && r.streetNumber]
        .filter(Boolean)
        .join(' ');

      const parts = [
        street,
        r.district,
        r.city,
      ].filter(Boolean);

      setLocation({
        ...location,
        coords: newCoords,
        address: parts.join(', '),
      });
    }
  };

  return (
    <ScrollView
      contentContainerStyle={{ paddingBottom: 400 }}
    >
      <View className="bg-white px-4 py-4 rounded-xl mb-4">
        <View className="flex-row items-center mb-2">
          <Ionicons name="location-sharp" size={24} />
          <Text className="ml-2 uppercase text-xl font-semibold">location</Text>
        </View>
        <View>
          <Text className="mb-2 text-gray-700">Choose your dog&apos;s location.</Text>
          <Pressable
            onPress={getCurrentLocationAsync}
            className="flex-row bg-black gap-2 justify-center items-center py-3 rounded-xl mb-4 active:opacity-80"
          >
            <Ionicons name="navigate" size={24} color="white" />
            <Text className="text-white text-lg font-semibold ">Use My Current Location</Text>
          </Pressable>
        </View>
      </View>

      <View className="bg-white pt-2 rounded-xl">

        <Text className="px-4 mb-2 font-semibold text-gray-800">Tap the map to select a location</Text>

        <View className="relative">
          <MapView
            ref={mapRef}
            style={{ height: 300, borderRadius: 12, marginBottom: 10 }}
            initialRegion={{
              latitude: coords?.latitude ?? 51.2465,
              longitude: coords?.longitude ?? 22.5684,
              latitudeDelta: 0.01,
              longitudeDelta: 0.01,
            }}
            onPress={(e) => {
              const { latitude, longitude } = e.nativeEvent.coordinate;
              resolveAddressAsync({ latitude, longitude });
            }}
          >
            {coords && (
              <>
                <Marker
                  coordinate={coords}
                  draggable
                  onDragEnd={(e) => setLocation({ ...location, coords: e.nativeEvent.coordinate })}
                />
                <Circle
                  center={coords}
                  radius={radius}
                  fillColor="rgba(0,0,255,0.1)"
                  strokeColor="blue"
                />
              </>
            )}
          </MapView>

          {!!address && (
            <View className="absolute top-2 left-2 right-2 bg-white/90 p-2 rounded-lg z-50">
              <Text className="text-red-500">{address}</Text>
            </View>
          )}

        </View>

        <Slider
          style={{ marginHorizontal: 16 }}
          minimumValue={0}
          maximumValue={1000}
          step={50}
          value={radius}
          onValueChange={(value) => setLocation({ ...location, radius: value })}
        />
        <Text className="mb-2 text-gray-600 text-sm font-bold text-center">Location {radius}m radius</Text>

      </View>

    </ScrollView>
  )
}

export default LocationStep