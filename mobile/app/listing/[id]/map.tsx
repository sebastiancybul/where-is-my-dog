import { View, Text, Pressable, Linking, Platform } from 'react-native';
import React, { useRef, useState } from 'react';
import { useListing } from "@/contexts/ListingContext";
import { useRouter } from "expo-router";
import { Ionicons } from "@expo/vector-icons";
import MapView, { Circle, MapMarker, Marker, Polyline } from "react-native-maps";
import { formatDateTime } from "@/utils/date";
import { ListingLocation } from "@/types/listing";

const CIRCLE_SIZE = 28;
const BOTTOM_PADDING = 4;

const LocationMarker = ({ loc, index, markerRef }: { loc: ListingLocation; index: number; markerRef?: React.Ref<MapMarker> }) => {
  const [centerOffsetY, setCenterOffsetY] = useState(0);

  const coordinate = {
    latitude: parseFloat(loc.latitude),
    longitude: parseFloat(loc.longitude),
  };
  const street = loc.address?.split(',')[0]?.trim();
  const title = `#${index + 1}${street ? ` • ${street}` : ''}`;

  if (Platform.OS === 'android') {
    return (
      <Marker
        ref={markerRef}
        coordinate={coordinate}
        pinColor={loc.is_primary ? '#EF4444' : '#3B82F6'}
        title={title}
        description={formatDateTime(loc.created_at)}
      />
    );
  }

  return (
    <Marker coordinate={coordinate} centerOffset={{ x: 0, y: centerOffsetY }}>
      <View
        style={{ alignItems: 'center', paddingHorizontal: 4, paddingBottom: BOTTOM_PADDING }}
        onLayout={(e) => {
          const { height } = e.nativeEvent.layout;
          setCenterOffsetY(-(height / 2 - (CIRCLE_SIZE / 2 + BOTTOM_PADDING)));
        }}
      >
        <View
          style={{
            backgroundColor: 'rgba(255,255,255,0.8)',
            paddingHorizontal: 8,
            paddingVertical: 4,
            borderRadius: 8,
            alignItems: 'center',
            marginBottom: 4,
          }}
        >
          <Text style={{ fontSize: 10, lineHeight: 13, fontWeight: '700', color: '#1F2937' }}>
            {title}
          </Text>
          <Text style={{ fontSize: 10, lineHeight: 13, color: '#4B5563' }}>{formatDateTime(loc.created_at)}</Text>
        </View>
        <View
          style={{
            width: CIRCLE_SIZE,
            height: CIRCLE_SIZE,
            borderRadius: CIRCLE_SIZE / 2,
            borderWidth: 2,
            borderColor: 'white',
            alignItems: 'center',
            justifyContent: 'center',
            backgroundColor: loc.is_primary ? '#EF4444' : '#6B7280',
          }}
        >
          <Text style={{ color: 'white', fontSize: 12, lineHeight: 14, fontWeight: '700' }}>{index + 1}</Text>
        </View>
      </View>
    </Marker>
  );
};

const MapScreen = () => {
  const router = useRouter();
  const { listing: listingData } = useListing();
  const primaryMarkerRef = useRef<MapMarker>(null);

  const sortedLocations = [...(listingData?.locations ?? [])].sort(
    (a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime()
  );

  const pathCoords = sortedLocations.map(loc => ({
    latitude: parseFloat(loc.latitude),
    longitude: parseFloat(loc.longitude),
  }));

  const primaryLocation = listingData?.primary_location;
  if (!primaryLocation) return null;

  const openNavigation = () => {
    const lat = parseFloat(primaryLocation.latitude)
    const lng = parseFloat(primaryLocation.longitude)

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
      {Platform.OS === 'android' && (
        <View className="absolute top-24 left-4 right-4 z-10 bg-white/90 px-4 py-2 rounded-full shadow-sm flex-row items-center justify-center gap-2">
          <Ionicons name="information-circle-outline" size={16} color="#475569" />
          <Text className="text-xs text-slate-600">Tap a pin to see the address and date</Text>
        </View>
      )}
      <Pressable
        onPress={() => openNavigation()}
        className="z-10 absolute bottom-8 left-8 right-8 bg-slate-800 py-4 rounded-2xl flex-row items-center justify-center gap-2 shadow-sm active:opacity-80"
      >
        <Text className="text-white text-lg font-semibold">Set navigation to the last location</Text>
      </Pressable>
      <MapView
        style={{ height: '100%', width: '100%'}}
        initialRegion={{
          latitude: parseFloat(primaryLocation.latitude),
          longitude: parseFloat(primaryLocation.longitude),
          latitudeDelta: 0.01,
          longitudeDelta: 0.01,
        }}
        onMapReady={() => {
          if (Platform.OS === 'android') {
            setTimeout(() => primaryMarkerRef.current?.showCallout(), 500);
          }
        }}
      >

        {pathCoords.length > 1 && (
          <Polyline
            coordinates={pathCoords}
            strokeColor="#1e293b"
            strokeWidth={2}
            lineDashPattern={[8, 6]}
          />
        )}

        {sortedLocations.map((loc, index) => (
          <React.Fragment key={loc.id}>
            <LocationMarker loc={loc} index={index} markerRef={loc.is_primary ? primaryMarkerRef : undefined} />
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
