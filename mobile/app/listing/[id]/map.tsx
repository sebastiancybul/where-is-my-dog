import { View, Text, Pressable, Linking, Platform } from 'react-native';
import React from 'react';
import { useListing } from "@/contexts/ListingContext";
import { useRouter } from "expo-router";
import { Ionicons } from "@expo/vector-icons";
import MapView, { Circle, Marker } from "react-native-maps";

const MapScreen = () => {
  const router = useRouter();
  const { listing: listingData } = useListing();

  const openNavigation = () => {
    const lat = parseFloat(listingData!.primary_location!.latitude)
    const lng = parseFloat(listingData!.primary_location!.longitude)
    
    if (Platform.OS === 'ios'){
      Linking.openURL(`maps://?daddr=${lat},${lng}`)  // iOS
    } else {
      Linking.openURL(`https://www.google.com/maps/dir/?api=1&destination=${lat},${lng}`)
    }
  }

  return (
    <View className="flex-1">
      <Pressable
        className="absolute top-12 left-4 z-10 bg-white/90 p-2 rounded-full shadow-sm"
        onPress={() => router.back()}
      >
        <Ionicons name="arrow-back" size={24} color="black" />
      </Pressable>
      <Pressable 
        onPress={() => openNavigation()}
        className="z-10 absolute bottom-8 left-8 right-8 bg-slate-800 py-4 rounded-2xl flex-row items-center justify-center gap-2 shadow-sm active:opacity-80"
      >
        <Text className="text-white text-lg font-semibold">Set navigation to the last location</Text>
      </Pressable>
      <MapView
        style={{ height: '100%', width: '100%'}}
        initialRegion={{
          latitude: parseFloat(listingData!.primary_location!.latitude),
          longitude: parseFloat(listingData!.primary_location!.longitude),
          latitudeDelta: 0.01,
          longitudeDelta: 0.01,
        }}
      >

        {listingData?.locations.map(loc => (
          <React.Fragment key={loc.id}>
            <Marker 
              coordinate={{
                latitude: parseFloat(loc.latitude),
                longitude: parseFloat(loc.longitude),
              }}
              pinColor={loc.is_primary ? 'red' : 'gray'}
            />
            {loc.accuracy_meters > 0 && (
              <Circle 
                center = {{
                  latitude: parseFloat(loc.latitude),
                  longitude: parseFloat(loc.longitude),
                }}
                radius={loc.accuracy_meters}
                fillColor={loc.is_primary ? "rgba(239,68,68,0.3)" : "rgba(156,163,175,0.1)"}
                strokeColor={loc.is_primary ? "rgba(239,68,68,0.5)" : "rgba(156,163,175,0.5)"}
              />
            )}
          </React.Fragment>
        ))}

      </MapView>
    </View>
  )
}

export default MapScreen