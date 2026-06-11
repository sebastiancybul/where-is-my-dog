import { View, Text, Pressable, Alert } from 'react-native';
import React, { ReactNode, useRef } from 'react';
import { Ionicons } from "@expo/vector-icons";

import * as Location from 'expo-location';
import MapView, { Marker, Circle } from 'react-native-maps';

import Slider from '@react-native-community/slider'
import { Coords, LocationState } from "@/types/listingForm";

type Props = {
  location: LocationState;
  setLocation: (location: LocationState) => void;
  includeStreetNumber?: boolean;
  initialCenter?: Coords;
  children?: ReactNode;
}

const LocationPicker = ({ location, setLocation, includeStreetNumber = false, initialCenter, children }: Props) => {
  const { coords, radius, address } = location;

  const mapRef = useRef<MapView>(null);

  const getCurrentLocationAsync = async () => {
    let { status } = await Location.requestForegroundPermissionsAsync();
    if (status !== 'granted') {
      Alert.alert('Permission to access location was denied');
      return;
    }

    const loc = await Location.getCurrentPositionAsync({}).catch(() => null);
    if (!loc) {
      Alert.alert('Could not get your current location. Please try again.');
      return;
    }
    const newCoords = { latitude: loc.coords.latitude, longitude: loc.coords.longitude };

    mapRef.current?.animateToRegion({
      latitude: loc.coords.latitude,
      longitude: loc.coords.longitude,
      latitudeDelta: 0.01,
      longitudeDelta: 0.01
    }, 800);

    selectCoords(newCoords);
  }

  const selectCoords = (newCoords: Coords) => {
    setLocation({ ...location, coords: newCoords });
    resolveAddressAsync(newCoords);
  };

  const buildAddress = (street: string | null | undefined, streetNumber: string | null | undefined, district: string | null | undefined, city: string | null | undefined) => {
    const streetLine = [street, includeStreetNumber && streetNumber]
      .filter(Boolean)
      .join(' ');

    return [streetLine, district, city].filter(Boolean).join(', ');
  };

  const reverseGeocodeFallbackAsync = async ({ latitude, longitude }: Coords) => {
    const res = await fetch(
      `https://nominatim.openstreetmap.org/reverse?format=jsonv2&lat=${latitude}&lon=${longitude}`,
      { headers: { 'User-Agent': 'where-is-my-dog' } }
    ).catch(() => null);
    if (!res?.ok) return '';

    const data = await res.json().catch(() => null);
    const a = data?.address;
    if (!a) return '';

    return buildAddress(a.road, a.house_number, a.suburb ?? a.city_district, a.city ?? a.town ?? a.village);
  };

  const resolveAddressAsync = async (newCoords: Coords) => {
    const results = await Location.reverseGeocodeAsync(newCoords).catch(() => []);

    const address = results.length > 0
      ? buildAddress(results[0].street, results[0].streetNumber, results[0].district, results[0].city)
      : await reverseGeocodeFallbackAsync(newCoords);

    if (!address) return;

    setLocation({
      ...location,
      coords: newCoords,
      address,
    });
  };

  return (
    <>
      <View className="bg-white px-4 py-4 rounded-xl mb-4">
        {children}
        <Pressable
          onPress={getCurrentLocationAsync}
          className="flex-row bg-black gap-2 justify-center items-center py-3 rounded-xl active:opacity-80"
        >
          <Ionicons name="navigate" size={24} color="white" />
          <Text className="text-white text-lg font-semibold ">Use My Current Location</Text>
        </Pressable>
      </View>

      <View className="bg-white pt-2 rounded-xl">

        <Text className="px-4 mb-2 font-semibold text-gray-800">Tap the map to select a location</Text>

        <View className="relative">
          <MapView
            ref={mapRef}
            style={{ height: 300, borderRadius: 12, marginBottom: 10 }}
            initialRegion={{
              latitude: coords?.latitude ?? initialCenter?.latitude ?? 51.2465,
              longitude: coords?.longitude ?? initialCenter?.longitude ?? 22.5684,
              latitudeDelta: 0.01,
              longitudeDelta: 0.01,
            }}
            onPress={(e) => {
              const { latitude, longitude } = e.nativeEvent.coordinate;
              selectCoords({ latitude, longitude });
            }}
          >
            {coords && (
              <>
                <Marker
                  coordinate={coords}
                  draggable
                  onDragEnd={(e) => selectCoords(e.nativeEvent.coordinate)}
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
    </>
  )
}

export default LocationPicker
