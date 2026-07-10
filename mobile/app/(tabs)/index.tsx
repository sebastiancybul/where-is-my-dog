import { View, Text, Pressable, FlatList, Modal, ScrollView, RefreshControl } from 'react-native'
import React, { useCallback, useEffect, useRef, useState } from 'react'
import { useRouter, useFocusEffect } from 'expo-router'
import { useAuth } from '@/contexts/AuthContext'
import { useNotifications } from '@/contexts/NotificationContext'
import { useLocation } from '@/contexts/LocationContext'
import { INBOX_EVENT_TYPES } from '@/types/notifications'
import { Ionicons } from '@expo/vector-icons';
import ListingCard, { ListingCardItem } from "@/components/ListingCard";
import axios from "axios";
import { COLOR_OPTIONS, GENDER_OPTIONS, SIZE_OPTIONS } from "@/constants/dogOptions";
import BreedPicker from "@/components/BreedPicker";
import ListingCardSkeleton from "@/components/skeletons/ListingCardSkeleton";
import LocationFilterModal from "@/components/LocationFilterModal";

interface ListingsResponse {
  results: ListingCardItem[];
  count: number;
}

interface Filters {
  breed: string[];
  color: string[];
  gender: ('male' | 'female' | 'unknown')[];
  size: ('small' | 'medium' | 'large')[];
}

const DEFAULT_FILTERS: Filters = {
  breed: [],
  color: [],
  gender: [],
  size: [],
};



const Index = () => {
  const [listings, setListings] = useState<ListingCardItem[]>([]);
  const [listingType, setListingType] = useState<'found' | 'lost'>('lost');
  const [loading, setLoading] = useState<boolean>(true);
  const [showFilters, setShowFilters] = useState<boolean>(false);
  const [showLocationPicker, setShowLocationPicker] = useState<boolean>(false);
  const [filters, setFilters] = useState<Filters>(DEFAULT_FILTERS);
  const [draftFilters, setDraftFilters] = useState<Filters>(DEFAULT_FILTERS);
  const [pages, setPages] = useState<{lost: number, found: number}>({ lost: 1, found: 1});
  const [totalCount, setTotalCount] = useState<number>(0);
  const [refreshing, setRefreshing] = useState<boolean>(false);
  const PAGE_SIZE = 5;
  const totalPages = Math.ceil(totalCount / PAGE_SIZE);

  const filterCount = filters.color.length + filters.gender.length + filters.size.length + filters.breed.length;

  const listRef = useRef<FlatList>(null);

  const API_URL = process.env.EXPO_PUBLIC_API_URL;

  const router = useRouter();
  const { authState } = useAuth();
  const { subscribe } = useNotifications();
  const { location, isReady } = useLocation();
  const [unreadCount, setUnreadCount] = useState(0);

  useFocusEffect(
    useCallback(() => {
      if (!authState.isAuthenticated) return;
      axios
        .get(`${API_URL}/api/notifications/unread-count/`)
        .then((res) => setUnreadCount(res.data.count))
        .catch(() => {});
    }, [authState.isAuthenticated])
  );

  useEffect(() => {
    const unsubs = INBOX_EVENT_TYPES.map((event) =>
      subscribe(event, () => setUnreadCount((c) => c + 1))
    );
    return () => unsubs.forEach((u) => u());
  }, [subscribe]);

  const toggleFilter = <K extends keyof Filters>(
    key: K,
    value: Filters[K][number]
  ) => {
    setDraftFilters(prev => {
      const current = prev[key] as string[];
      const exists = current.includes(value as string);
      return {
        ...prev,
        [key]: exists
          ? current.filter(v => v !== value)
          : [...current, value],
      };
    });
  };

  const resetFilters = () => {
    setDraftFilters(DEFAULT_FILTERS);
  };

  const applyFilters = () => {
    setFilters(draftFilters);
    setPages({ lost: 1, found: 1 });
    setShowFilters(false);
  };

  const openFilters = () => {
    setDraftFilters(filters);
    setShowFilters(true);
  };

  const onRefresh = () => {
    setRefreshing(true);
    setPages({ lost: 1, found: 1 });
  };

  const fetchListings = async() => {
    try {
      setLoading(true);
      const response = await axios.get<ListingsResponse>(`${API_URL}/api/listings/nearby/`, {
        params: {
          latitude: location.coords.latitude,
          longitude: location.coords.longitude,
          radius_km: location.radius,
          type: listingType,
          status: 'active',
          ...(filters.breed.length > 0 && { breed: filters.breed.join(',') }),
          ...(filters.size.length > 0 && { size: filters.size.join(',') }),
          ...(filters.gender.length > 0 && { gender: filters.gender.join(',') }),
          ...(filters.color.length > 0 && { color: filters.color.join(',') }),
          page: listingType === 'found' ? pages.found : pages.lost
        }
      });
      setListings(response.data.results);
      setTotalCount(response.data.count);
    } catch (error) {
      console.error('Failed to fetch listings:', error);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }

  useEffect(() => {
    if (!isReady) return;
    fetchListings();
  }, [listingType, filters, pages, location, isReady]);


  return (
    <View className="pt-safe px-4">
      {/* header */}
      <View className="pl-2 pt-4 pb-2 flex-row justify-between items-center">
        <Pressable className="active:opacity-80" onPress={() => setShowLocationPicker(true)}>
          <Text className="text-gray-500 text-sm font-medium uppercase tracking-wider">Location</Text>
          <View className="flex-row items-center mt-1">
            <Ionicons name="location" size={24} color="#2563EB" />
            <Text className="text-3xl font-bold tracking-wide">{location.label}</Text>
            <Text className="text-lg font-semibold text-gray-400 ml-2">· {location.radius} km</Text>
            <Ionicons name="chevron-down" size={22} color="#6B7280" />
          </View>
        </Pressable>

        <Pressable
          onPress={() => router.push('/notifications')}
          className="bg-white rounded-full p-2 active:opacity-80"
        >
          <Ionicons name="notifications-outline" size={24} />
          {unreadCount > 0 && (
            <View className="absolute -top-1 -right-1 bg-red-500 rounded-full min-w-5 h-5 px-1 items-center justify-center">
              <Text className="text-white text-xs font-bold">
                {unreadCount > 99 ? '99+' : unreadCount}
              </Text>
            </View>
          )}
        </Pressable>
      </View>

      <View className="flex-row mr-14 pr-1 gap-4">
        {/* Toggle between Lost and Found listings */}
        <View className="mt-2 mb-4 py-1 px-1 h-14 w-full flex-row rounded-2xl justify-center bg-gray-200">
          <Pressable
            onPress={() => setListingType('lost')}
            className={`flex-1 justify-center items-center rounded-xl active:opacity-80 ${listingType === 'lost' ? ' bg-slate-50': 'bg-transparent'}`}
          >
            <Text className={`font-bold text-2xl ${listingType === 'lost' ? 'text-red-600' : 'text-gray-700'}`}>
              Lost
            </Text>
          </Pressable>
          <Pressable
            onPress={() => setListingType('found')}
            className={`flex-1 justify-center items-center rounded-xl active:opacity-80 ${listingType === 'found' ? ' bg-slate-50': 'bg-transparent'}`}
          >
            <Text className={`font-bold text-2xl ${listingType === 'found' ? 'text-red-600' : 'text-gray-700'}`}>
              Found
            </Text>
          </Pressable>
        </View>

        {/* Search and filter*/}
        <Pressable
          className="flex justify-center mb-2 active:opacity-80"
          onPress={openFilters}
        >
          <View className="relative bg-white px-2 py-2 rounded-2xl">
            <Ionicons name="options-outline" size={24} />

            {!!filterCount && (
            <Text className="absolute w-6 left-6 bottom-7 text-center rounded-full bg-gray-800 border text-slate-50">
              {filterCount}
            </Text>
            )}
          </View>
        </Pressable>
      </View>
      
      
      {/* listings */}
      {loading &&(
        <ScrollView contentContainerStyle={{ paddingBottom: 100 }}>
          <ListingCardSkeleton />
          <ListingCardSkeleton />
          <ListingCardSkeleton />
        </ScrollView>
      )}

      {!loading && (
        <FlatList
          ref={listRef}
          data={listings}
          keyExtractor={item => item.id.toString()}
          showsVerticalScrollIndicator={false}
          contentContainerStyle={{ paddingBottom: 150 }}
          refreshControl={
            <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
          }
          renderItem={({item}) => (
            <ListingCard item={item} isPreview={false} />
          )}
          ListFooterComponent={() => {
            const currentPage = listingType === 'lost' ? pages.lost : pages.found;
            const isFirst = currentPage === 1;
            const isLast = currentPage >= totalPages;
            const setPage = (p: number) =>{
              setPages(prev => ({ ...prev, [listingType]: p }));
              listRef.current?.scrollToOffset({ offset: 0})
            }
            return (
              <View className="flex-row justify-between items-center mx-4 py-4">
                <Pressable
                  onPress={() => !isFirst && setPage(currentPage - 1)}
                  disabled={isFirst}
                  className={`flex-row items-center gap-2 px-5 py-3 rounded-2xl border-2 active:opacity-80 ${isFirst ? 'border-gray-100 bg-gray-50' : 'border-blue-600 bg-white'}`}
                >
                  <Ionicons name="chevron-back" size={18} color={isFirst ? '#d1d5db' : '#2563EB'} />
                  <Text className={`font-semibold text-base ${isFirst ? 'text-gray-300' : 'text-blue-600'}`}>Prev</Text>
                </Pressable>

                <View className="items-center">
                  <Text className="font-bold text-base text-gray-800">{currentPage} / {totalPages}</Text>
                  <Text className="text-xs text-gray-400 mt-0.5">{totalCount} listings</Text>
                </View>

                <Pressable
                  onPress={() => !isLast && setPage(currentPage + 1)}
                  disabled={isLast}
                  className={`flex-row items-center gap-2 px-5 py-3 rounded-2xl border-2 active:opacity-80 ${isLast ? 'border-gray-100 bg-gray-50' : 'border-blue-600 bg-blue-600'}`}
                >
                  <Text className={`font-semibold text-base ${isLast ? 'text-gray-300' : 'text-white'}`}>Next</Text>
                  <Ionicons name="chevron-forward" size={18} color={isLast ? '#d1d5db' : '#fff'} />
                </Pressable>
              </View>
            );
          }}
        />
      )}

      <Modal
        visible={showFilters}
        transparent
        animationType="slide"
        onRequestClose={() => setShowFilters(false)}
      >
        <Pressable className="flex-1 bg-black/50" onPress={() => setShowFilters(false)} />

        <View className="bg-white rounded-t-3xl pb-16 px-4" >
          <ScrollView showsVerticalScrollIndicator={false} >
            <View className="w-10 h-1 bg-gray-200 rounded-full self-center mt-3 mb-1" />

            <View className="flex-row justify-between mt-4 mb-4 items-center">
              <Text className="text-xl font-semibold tracking-wide mt-2">Filters</Text>
              <Pressable
                className="pl-4 pr-1 py-2 active:opacity-80"
                onPress={resetFilters}
              >
                <Text className="text-blue-600 font-semibold">Reset all</Text>
              </Pressable>
            </View>

            {/* Size */}
            <Text className="text-xs font-bold text-gray-400 uppercase tracking-widest mb-2.5">Size</Text>
            <View className="flex-row mb-5 gap-4">
              {SIZE_OPTIONS.map(opt => {
                const active = draftFilters.size.includes(opt.value);
                return (
                  <Pressable
                      key={opt.value}
                      onPress={() => toggleFilter('size', opt.value)}
                      className={`flex-1 items-center py-3 rounded-2xl border-2 active:opacity-80 ${
                        active ? 'bg-blue-600 border-blue-600' : 'bg-white border-gray-100'
                      }`}
                    >
                      <Text className={`font-bold text-sm ${active ? 'text-white' : 'text-gray-800'}`}>
                        {opt.label}
                      </Text>
                      <Text className={`text-xs mt-0.5 ${active ? 'text-blue-100' : 'text-gray-400'}`}>
                        {opt.sub}
                      </Text>
                    </Pressable>
                )
              })}
            </View>

            {/* Gender */}
            <Text className="text-xs font-bold text-gray-400 uppercase tracking-widest mb-2.5">Gender</Text>
            <View className="flex-row mb-5" style={{ gap: 8 }}>
              {GENDER_OPTIONS.map(opt => {
                const active = draftFilters.gender.includes(opt.value);
                return (
                  <Pressable
                    key={opt.value}
                    onPress={() => toggleFilter('gender', opt.value)}
                    className={`flex-1 items-center py-3 rounded-2xl border-2 active:opacity-80 ${
                      active ? 'bg-blue-600 border-blue-600' : 'bg-white border-gray-100'
                    }`}
                  >
                    <Text className={`font-semibold text-sm ${active ? 'text-white' : 'text-gray-700'}`}>
                      {opt.label}
                    </Text>
                  </Pressable>
                );
              })}
            </View>

            {/* Color */}
            <Text className="text-xs font-bold text-gray-400 uppercase tracking-widest mb-2.5">Color</Text>
            <View className="flex-row flex-wrap mb-5" style={{ gap: 8 }}>
              {COLOR_OPTIONS.map(opt => {
                const active = draftFilters.color.includes(opt.value);
                return (
                  <Pressable
                    key={opt.value}
                    onPress={() => toggleFilter('color', opt.value)}
                    className={`flex-row items-center px-3.5 py-2.5 rounded-full border-2 active:opacity-80 ${
                      active ? 'bg-blue-600 border-blue-600' : 'bg-white border-gray-100'
                    }`}
                  >
                    {opt.dot ? (
                      <View
                        style={{
                          width: 12, height: 12, borderRadius: 6,
                          backgroundColor: opt.dot,
                          borderWidth: 'border' in opt ? 1 : 0,
                          borderColor: '#d1d5db',
                          marginRight: 6,
                        }}
                      />
                    ) : (
                      <View style={{ width: 12, height: 12, borderRadius: 6, marginRight: 6, overflow: 'hidden', flexDirection: 'row' }}>
                        <View style={{ flex: 1, backgroundColor: '#7c4a1e' }} />
                        <View style={{ flex: 1, backgroundColor: '#f0f0f0' }} />
                        <View style={{ flex: 1, backgroundColor: '#1a1a1a' }} />
                      </View>
                    )}
                    <Text className={`text-sm font-semibold ${active ? 'text-white' : 'text-gray-700'}`}>
                      {opt.label}
                    </Text>
                  </Pressable>
                );
              })}
            </View>
            
            {/* Breed */}
            <Text className="text-xs font-bold text-gray-400 uppercase tracking-widest mb-2.5">Breed</Text>
            <View className="mb-6">
              <BreedPicker
                mode="multi"
                value={draftFilters.breed}
                onChange={breeds => setDraftFilters(prev => ({ ...prev, breed: breeds }))}
              />
            </View>
          </ScrollView>
              <Pressable
                onPress={applyFilters}
                className="absolute left-2 right-2 bottom-2 bg-blue-600 rounded-2xl h-14 items-center justify-center mb-1 active:opacity-80"
              >
                <Text className="text-white font-bold text-base tracking-wide">Show results</Text>
            </Pressable>
        </View>
      </Modal>

      <LocationFilterModal
        visible={showLocationPicker}
        onClose={() => setShowLocationPicker(false)}
        onApplied={() => setPages({ lost: 1, found: 1 })}
      />
    </View>
  )
}

export default Index