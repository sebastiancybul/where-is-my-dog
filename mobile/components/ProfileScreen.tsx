import { View, Text, ScrollView, ActivityIndicator, Pressable, RefreshControl } from "react-native";
import React, { useCallback, useState } from 'react';
import { useFocusEffect, useRouter } from 'expo-router';
import { Ionicons } from "@expo/vector-icons";
import axios from "axios";
import ListingCard, { ListingCardItem } from "@/components/ListingCard";

const API_URL = process.env.EXPO_PUBLIC_API_URL;

interface ProfileUser {
  id: number;
  username: string;
}

interface ProfileScreenProps {
  user: ProfileUser;
  onLogout: () => void;
}

const formatDateLabel = (dateStr: string): string => {
  const date = new Date(dateStr);
  const today = new Date();
  const yesterday = new Date(today);
  yesterday.setDate(today.getDate() - 1);

  if (date.toDateString() === today.toDateString()) return 'Today';
  if (date.toDateString() === yesterday.toDateString()) return 'Yesterday';
  return date.toLocaleDateString('en-GB', { day: 'numeric', month: 'short' });
};


const ProfileScreen = ({ user, onLogout }: ProfileScreenProps) => {
  const [listings, setListings] = useState<ListingCardItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'lost' | 'found' | 'history'>('lost');
  const [activeHistoryTab, setActiveHistoryTab] = useState<'came_home' | 'returned' | 'expired'>('came_home');
  const [refreshing, setRefreshing] = useState<boolean>(false);

  const router = useRouter();

  const activeLost = listings.filter(l => l.status === 'active' && l.type === 'lost');
  const activeFound = listings.filter(l => l.status === 'active' && l.type === 'found');
  const historyCameHome = listings.filter(l => l.status === 'found');
  const historyReturned = listings.filter(l => l.status === 'returned');
  const historyExpired = listings.filter(l => l.status === 'expired');
  const history = [...historyCameHome, ...historyReturned, ...historyExpired];

  const tabs = [
    { id: 'lost', label: 'Lost', count: activeLost.length },
    { id: 'found', label: 'Found', count: activeFound.length },
    { id: 'history', label: 'History', count: history.length },
  ] as const;

  const fetchUserListings = async () => {
      try {
        setLoading(true);
        const response = await axios.get(`${API_URL}/api/listings/`, {
          params: { user: user.id }
        });
        setListings(response.data.results);
      } catch (error) {
        console.error('Failed to fetch user listings:', error);
      } finally {
        setLoading(false);
        setRefreshing(false);
      }
    };

  useFocusEffect(useCallback(() => {
    fetchUserListings();
  }, [user.id]));

  const onRefresh = () => {
    setRefreshing(true);
    fetchUserListings();
  };

  return (
    <View className="flex-1 bg-white">
      <View className="flex-row items-center justify-between px-6 pt-14 pb-4">
        <Text className="text-2xl font-black text-gray-900 tracking-tight">Profile</Text>
        <View className="flex-row gap-2">
          <Pressable onPress={() => router.push('/settings')} className="p-2 bg-gray-100 rounded-full active:opacity-80">
            <Ionicons name="settings-outline" size={24} color="#1f2937" />
          </Pressable>
          <Pressable onPress={onLogout} className="p-2 bg-red-50 rounded-full active:opacity-80">
            <Ionicons name="log-out-outline" size={24} color="#ef4444" />
          </Pressable>
        </View>
      </View>


      <ScrollView 
        showsVerticalScrollIndicator={false} contentContainerStyle={{ paddingBottom: 100 }}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
        }
      >
        <View className="px-6 py-6 flex-row items-center">
          <View className="w-20 h-20 rounded-full bg-gray-900 items-center justify-center">
            <Text className="text-3xl font-bold text-white">
              {user.username[0].toUpperCase()}
            </Text>
          </View>
          <View className="ml-5">
            <Text className="text-xl font-bold text-gray-900">{user.username}</Text>
          </View>
        </View>

        <View className="flex-row px-6 gap-3 mb-8">
          <View className="flex-1 bg-gray-50 p-4 rounded-2xl border border-gray-100">
            <View className="flex-row items-center gap-1.5 mb-1">
              {(activeLost.length > 0 || activeFound.length > 0) && <View className="w-2 h-2 rounded-full bg-green-500" />}
              <Text className="text-gray-400 text-[10px] font-bold uppercase tracking-widest">Active</Text>
            </View>
            <Text className="text-xl font-bold text-gray-900">{activeLost.length + activeFound.length}</Text>
          </View>
          <View className="flex-1 bg-gray-50 p-4 rounded-2xl border border-gray-100">
            <Text className="text-gray-400 text-[10px] font-bold uppercase tracking-widest mb-1">Archived</Text>
            <Text className="text-xl font-bold text-gray-900">{history.length}</Text>
          </View>
        </View>

        <View className="px-6">
          <View className="flex-row border-b border-gray-100">
            {tabs.map((tab) => (
              <Pressable
                key={tab.id}
                onPress={() => setActiveTab(tab.id)}
                className={`mr-8 pb-3 relative active:opacity-80 ${activeTab === tab.id ? '' : 'opacity-40'}`}
              >
                <View className="flex-row items-center">
                  <Text className={`text-base font-bold ${activeTab === tab.id ? 'text-gray-900' : 'text-gray-500'}`}>
                    {tab.label}
                  </Text>
                  {tab.count > 0 && (
                    <Text className="ml-1.5 text-xs text-gray-400 font-medium">({tab.count})</Text>
                  )}
                </View>
                {activeTab === tab.id && (
                  <View className="absolute bottom-0 left-0 right-0 h-[3px] bg-gray-900 rounded-full" />
                )}
              </Pressable>
            ))}
          </View>
        </View>

        <View className="px-4 mt-4">
          {loading ? (
            <ActivityIndicator className="mt-12" color="#111827" />
          ) : activeTab !== 'history' ? (() => {
            const currentItems = activeTab === 'lost' ? activeLost : activeFound;
            return currentItems.length === 0 ? (
              <View className="items-center py-20">
                <Text className="text-gray-400 font-medium">No listings here yet</Text>
              </View>
            ) : currentItems.map((item, index) => {
              const label = formatDateLabel(item.created_at);
              const showSeparator = index === 0 || label !== formatDateLabel(currentItems[index - 1].created_at);
              return (
                <React.Fragment key={item.id}>
                  {showSeparator && (
                    <Text className="text-xs font-bold text-gray-400 uppercase tracking-widest mb-3 mt-2">{label}</Text>
                  )}
                  <ListingCard item={item} isPreview={false} />
                </React.Fragment>
              );
            });
          })() : (
            <>
              <View className="flex-row gap-4 mb-4 border-b border-gray-100 pb-3">
                {([
                  { id: 'came_home', label: 'My dog came home', count: historyCameHome.length },
                  { id: 'returned', label: 'Returned to owner', count: historyReturned.length },
                  { id: 'expired', label: 'Expired', count: historyExpired.length },
                ] as const).map(tab => (
                  <Pressable
                    key={tab.id}
                    onPress={() => setActiveHistoryTab(tab.id)}
                    className={`pb-2 relative active:opacity-80 ${activeHistoryTab === tab.id ? '' : 'opacity-40'}`}
                  >
                    <View className="flex-row items-center">
                      <Text className={`text-sm font-bold ${activeHistoryTab === tab.id ? 'text-gray-900' : 'text-gray-500'}`}>
                        {tab.label}
                      </Text>
                      {tab.count > 0 && (
                        <Text className="ml-1 text-xs text-gray-400">({tab.count})</Text>
                      )}
                    </View>
                    {activeHistoryTab === tab.id && (
                      <View className="absolute bottom-0 left-0 right-0 h-[2px] bg-gray-900 rounded-full" />
                    )}
                  </Pressable>
                ))}
              </View>
              {(() => {
                const items = activeHistoryTab === 'came_home' ? historyCameHome : activeHistoryTab === 'returned' ? historyReturned : historyExpired;
                return items.length === 0 ? (
                  <View className="items-center py-20">
                    <Text className="text-gray-400 font-medium">No listings here yet</Text>
                  </View>
                ) : items.map((item, index) => {
                  const label = formatDateLabel(item.created_at);
                  const showSeparator = index === 0 || label !== formatDateLabel(items[index - 1].created_at);
                  return (
                    <React.Fragment key={item.id}>
                      {showSeparator && (
                        <Text className="text-xs font-bold text-gray-400 uppercase tracking-widest mb-3 mt-2">{label}</Text>
                      )}
                      <ListingCard item={item} isPreview={false} />
                    </React.Fragment>
                  );
                });
              })()}
            </>
          )}
        </View>
      </ScrollView>
    </View>
  );
};

export default ProfileScreen;