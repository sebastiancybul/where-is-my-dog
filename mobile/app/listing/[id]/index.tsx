import { Image, Pressable, ScrollView, Text, View, Alert, Modal, ActivityIndicator } from 'react-native'
import React, { useCallback, useEffect, useState } from 'react'
import { Stack, useFocusEffect, useLocalSearchParams, useRouter } from "expo-router"
import axios from "axios";
import { FontAwesome5, Ionicons, MaterialCommunityIcons } from "@expo/vector-icons";
import { useAuth } from "@/contexts/AuthContext";
import { useListing } from "@/contexts/ListingContext";
import { DEFAULT_EXPIRY_DAYS } from "@/types/listing";
import LocationHistory from "@/components/LocationHistory";


const Details = () => {
	const { id } = useLocalSearchParams();
	const [isAuthor, setIsAuthor] = useState<boolean>(false);
  const [isDeleting, setIsDeleting] = useState<boolean>(false);
  const [deleteSuccess, setDeleteSuccess] = useState<boolean>(false);
  const [deleteError, setDeleteError] = useState<string>('');
  const [isMenuOpen, setIsMenuOpen] = useState<boolean>(false);
  const [markResolvedError, setMarkResolvedError] = useState<string>('');
  const [isMarkingAsResolved, setIsMarkingAsResolved] = useState<boolean>(false);
  const [markResolvedSuccess, setMarkResolvedSuccess] = useState<boolean>(false);
  const [isStartingChat, setIsStartingChat] = useState(false)
  const [isJoiningGroup, setIsJoiningGroup] = useState(false)
  const [isBumping, setIsBumping] = useState(false)

	const { authState } = useAuth();
  const { listing: listingData, refetch } = useListing()

  useFocusEffect(useCallback(() => {
    refetch();
  }, []))
	const router = useRouter();

	const API_URL = process.env.EXPO_PUBLIC_API_URL;

  const handleDelete = () => {
    Alert.alert(
      "Delete Listing",
      "Are you sure you want to delete this listing? This action cannot be undone.",
      [
        { text: "Cancel", style: "cancel" },
        {
          text: "Delete",
          style: "destructive",
          onPress: async () => {
            setDeleteError('');
            try {
              setIsDeleting(true);
              await axios.delete(`${API_URL}/api/listings/${id}/`, {
                headers: { Authorization: `Bearer ${authState.token}` },
              });
              setDeleteSuccess(true);
            } catch (e) {
              console.log(e);
              setDeleteError('Something went wrong. Please try again.');
            } finally {
              setIsDeleting(false);
            }
          },
        },
      ]
    );
  };

  const handleMarkAsResolved = () => {
    Alert.alert(
      "Mark as resolved",
      "Are you sure this listing is resolved? It will be moved to your history and closed.",
      [
        { text: "Cancel", style: "cancel" },
        {
          text: "Mark as resolved",
          style: "default",
          onPress: async() => {
            setMarkResolvedError('');
            try{
              setIsMarkingAsResolved(true);
              await axios.post(`${API_URL}/api/listings/${id}/mark_found/`, {
                headers: {Authorization: `Bearer ${authState.token}` },
              });
              setMarkResolvedSuccess(true);
            } catch (e) {
              console.log(e);
              setMarkResolvedError('Something went wrong. Please try again.');
            } finally {
              setIsMarkingAsResolved(false);
            }
          },
        },
      ]
    )
  }

  const handleMessage = async () => {
    if (!authState.user || !listingData) return
    try {
      setIsStartingChat(true)
      const res = await axios.post(`${API_URL}/api/chats/conversations/`, {
        user_id: listingData.user.id,
        listing_id: id,
      })
      router.push(`/chat/${res.data.id}`)
    } catch (e) {
      console.log(e)
    } finally {
      setIsStartingChat(false)
    }
  }

  const handleGroupChat = async () => {
    const convId = listingData?.public_conversation_id
    if (!convId) return
    try {
      setIsJoiningGroup(true)
      await axios.post(`${API_URL}/api/chats/conversations/${convId}/join/`)
      router.push({
        pathname: '/chat/[id]',
        params: {
          id: String(convId),
          listing_title: listingData?.title ?? '',
          is_group: 'true',
        },
      })
    } catch (e) {
      console.log(e)
    } finally {
      setIsJoiningGroup(false)
    }
  }

  const handleBump = async () => {
    try {
      setIsBumping(true)
      await axios.post(`${API_URL}/api/listings/${id}/bump/`)
      await refetch()
      setIsMenuOpen(false)
    } catch (e) {
      console.log(e)
    } finally {
      setIsBumping(false)
    }
  }

	useEffect(() => {
		setIsAuthor(authState?.user?.id == listingData?.user?.id)
	}, [authState?.user, listingData?.user])

	const hasName = !!listingData?.dog_name;

	const mainTitle = hasName ? listingData?.dog_name : listingData?.breed;

	const subTitle = hasName
  ? [listingData?.breed, listingData?.age_estimate].filter(Boolean).join(' • ')
  : listingData?.age_estimate;

  const getExpiryBadge = () => {
    if (listingData?.status === 'expired') {
      return { text: 'Expired', tone: 'expired' as const }
    }
    if (listingData?.status === 'active' && listingData?.expires_at) {
      const date = new Date(listingData.expires_at)
      const ms = date.getTime() - Date.now()
      if (ms <= 0) return { text: 'Expired', tone: 'expired' as const }
      const formatted = date.toLocaleDateString(undefined, { day: 'numeric', month: 'short' })
      const soon = ms < 24 * 3_600_000
      return { text: `Expires ${formatted}`, tone: soon ? ('soon' as const) : ('normal' as const) }
    }
    return null
  }

  const expiryBadge = getExpiryBadge()

  const bumpDays = listingData ? DEFAULT_EXPIRY_DAYS[listingData.type] : 0

  const expiryStyles = {
    expired: 'bg-red-50 border-red-100',
    soon: 'bg-red-50 border-red-100',
    normal: 'bg-gray-50 border-gray-100',
  }
  const expiryTextStyles = {
    expired: 'text-red-600',
    soon: 'text-red-600',
    normal: 'text-gray-500',
  }


	return (
		<View className="flex-1">
			<Stack.Screen options={{ headerShown: false }} />
			<ScrollView
				className="flex-1 bg-white"
			>
				<View className="relative">
					{!!listingData?.photos?.[0]?.cloudinary_url ? (
						<Image
							source={{ uri: listingData?.photos?.[0]?.cloudinary_url }}
							className="w-full h-96"
						/>) : (
							<Image
								source={require('../../../assets/images/dog-placeholder.png')}
								className="w-full h-96"
							/>
						)}

					<Pressable
						className="absolute top-12 left-4 z-10 bg-white/80 p-2 rounded-full shadow-sm active:opacity-80"
						onPress={() => router.back()}
					>
						<Ionicons name="arrow-back" size={24} color="black" />
					</Pressable>
					<View className={`absolute bottom-8 left-6 px-4 py-1 rounded-full ${listingData?.type === 'lost' ? 'bg-red-600' : 'bg-green-600'}`}>
						<Text className="text-white uppercase text-sm font-semibold tracking-wide text-center">
							{listingData?.type === 'lost' ? 'Lost' : 'Found'}
						</Text>
					</View>
				</View>

				<View
					className="flex-1 -mt-6 rounded-t-3xl bg-white pt-6 px-4"
				>
					<View className="border-b pb-6 mb-4 border-gray-100">
						{!!mainTitle && (
							<Text className="text-3xl font-bold">
								{mainTitle}
							</Text>
						)}


						{!!subTitle && (
							<Text className="text-gray-600 tracking-wide mt-1">
								{subTitle}
							</Text>
						)}


						{!!listingData?.reward_offered && (
							<View className="flex-row items-center bg-yellow-50 p-3 rounded-xl self-start mt-4 border border-yellow-100">
								<FontAwesome5 name="award" size={18} color="#EAB308" />
								<Text className="ml-2 font-bold text-yellow-700">
									Reward: {listingData?.reward_offered} PLN
								</Text>
							</View>
						)}

						{isAuthor && expiryBadge && (
							<View className={`flex-row items-center px-3 py-1.5 rounded-full self-start mt-4 border ${expiryStyles[expiryBadge.tone]}`}>
								{expiryBadge.tone === 'normal' ? (
									<Ionicons name="time-outline" size={16} color="#6B7280" />
								) : (
									<Ionicons name="warning" size={16} color="#dc2626" />
								)}
								<Text className={`ml-1.5 text-sm font-semibold ${expiryTextStyles[expiryBadge.tone]}`}>
									{expiryBadge.text}
								</Text>
							</View>
						)}

						{isAuthor && expiryBadge?.tone === 'soon' && (
							<View className="flex-row items-center flex-wrap mt-1.5">
								<Text className="text-xs text-gray-400">Tap Manage listing </Text>
								<Ionicons name="arrow-forward" size={12} color="#9ca3af" />
								<Text className="text-xs text-gray-400"> Bump to keep it active</Text>
							</View>
						)}
					</View>

					<View className="flex-row flex-wrap justify-around border-b pb-6 pt-4 mb-6 border-gray-100">

						<View className="flex items-center gap-1 w-20">
							<MaterialCommunityIcons name="ruler" size={20} color="#9CA3AF" ></MaterialCommunityIcons>
							<Text className="text-sm text-gray-400">Size</Text>
							<Text className="text-gray-700 font-bold text-sm">{listingData?.size}</Text>
						</View>

						<View className="flex items-center gap-1 w-20">
							<MaterialCommunityIcons
									name={listingData?.has_collar ? "link-variant" : "link-variant-off"}
									size={20}
									color={listingData?.has_collar ? "#9CA3AF" : "#dc2626"}
							/>
							<Text className="text-sm text-gray-400">Collar</Text>
							<Text className="text-gray-700 font-bold text-sm">
									{listingData?.has_collar ? `${listingData?.collar_color}` : "No collar"}
							</Text>
						</View>

						<View className="flex items-center gap-1 w-20">
							<Ionicons name="color-palette-sharp" size={20} color="#9CA3AF" />
							<Text className="text-sm text-gray-400">Color</Text>
							<Text className="text-gray-700 font-bold text-center text-sm">{listingData?.color}</Text>
						</View>

						<View className="flex items-center gap-1 w-20">
							<Ionicons name="paw" size={20} color="#9CA3AF" />
							<Text className="text-sm text-gray-400">Marks</Text>
							<Text className="text-gray-700 font-bold text-sm">{!!listingData?.special_marks ? 'yes' : 'no'}</Text>
						</View>

					</View>

					{!!listingData?.special_marks && (
						<View className="mx-4 mb-6 overflow-hidden rounded-2xl bg-red-50 border border-red-100 shadow-sm">
							<View className="flex-row items-center p-4">
								<View>
									<Ionicons name="alert-circle" size={22} color="white" />
								</View>

								<View className="ml-4 flex-1">
									<Text className="text-red-400 text-xs font-bold uppercase tracking-wider">
										Special Marks
									</Text>
									<Text className="text-red-900 text-lg font-semibold leading-6">
										{listingData?.special_marks}
									</Text>
								</View>

								<Ionicons name="paw" size={24} color="#fca5a5" style={{ opacity: 0.3 }} />
							</View>
						</View>
					)}

					<View className="mb-6">
						<Text className="font-semibold text-lg mb-1">Description</Text>
						<Text className="text-gray-600 text-base">
							{listingData?.description}
						</Text>
					</View>

					<View className="mb-7">
						<Text className="text-lg font-semibold mb-2">Last Location</Text>
						<View className="flex gap-2">
              <Pressable
                onPress={() => router.push(`/listing/${id}/map`)}
                className="active:opacity-80"
              >
                <View
                  className="flex-row items-center px-4 py-2 rounded-lg bg-gray-50 border border-gray-100 "
                >
                  <Ionicons name="location" size={24} color="#EF4444" />

                    <View className="flex-col ml-6">
                      <Text className="font-semibold tracking-wider">{listingData?.primary_location?.address}</Text>
                      <View className="flex-row gap-2">
                        <Text className="tracking-wide">{listingData?.primary_location?.latitude && `Lat: ${parseFloat(listingData?.primary_location?.latitude).toFixed(4)},`}</Text>
                        <Text className="tracking-wide">{listingData?.primary_location?.longitude && `Long: ${parseFloat(listingData?.primary_location?.longitude).toFixed(4)}`}</Text>
                      </View>
                      <Text className="text-xs tracking-wide text-gray-600 mt-1">Tap to view all reported locations on the map</Text>
                    </View>
                </View>
              </Pressable>

              {authState.isAuthenticated && listingData?.type === 'found' && listingData?.status === 'active' && (
                <Pressable
                  onPress={() => router.push(`/listing/${id}/add-new-location`)}
                  className="flex-row items-center justify-center gap-2 px-4 py-3 rounded-lg bg-gray-50 border border-gray-100 active:opacity-80"
                >
                  <Ionicons name="add-circle-outline" size={20} color="#1e293b" />
                  <Text className="font-semibold text-slate-800">Report new location</Text>
                </Pressable>
              )}
						</View>
					</View>

					<LocationHistory />

					<View className="flex flex-row items-center p-4 bg-white border-t border-gray-100 rounded-2xl">
						<View className="w-12 h-12 items-center justify-center rounded-full bg-indigo-50">
							<Text className="text-sm font-bold text-indigo-300 uppercase">IMG</Text>
						</View>

						<View className="ml-3 flex-1 justify-center">
							<Text className="text-base font-bold text-gray-800 leading-tight">
								{listingData?.user?.username || "Anonim"}
							</Text>
							<Text className="text-xs font-medium text-gray-400">
								Author
							</Text>
						</View>

						<View className="self-start mt-4">
							<Text className="text-[11px] font-semibold text-gray-300 uppercase tracking-tighter">
								{listingData?.updated_at?.split("T")[0]}
							</Text>
						</View>
					</View>

				</View>

				<View className="h-28 w-full bg-gray-100">

				</View>
			</ScrollView>

			{!isAuthor && (
        <View className="absolute bottom-7 left-6 right-6 flex-row gap-3">
          <Pressable
            onPress={handleMessage}
            disabled={isStartingChat}
            className="flex-1 flex-row p-4 rounded-3xl items-center justify-center bg-slate-800 active:opacity-80"
          >
            {isStartingChat ? (
              <ActivityIndicator color="white" />
            ) : (
              <>
                <Ionicons name="chatbubbles" color="white" size={24} />
                <Text className="text-white text-xl font-bold ml-2">Message</Text>
              </>
            )}
          </Pressable>

          {!!listingData?.public_conversation_id && !listingData?.public_conversation_is_closed && (
            <Pressable
              onPress={handleGroupChat}
              disabled={isJoiningGroup}
              className="flex-1 flex-row p-4 rounded-3xl items-center justify-center bg-blue-600 active:opacity-80"
            >
              {isJoiningGroup ? (
                <ActivityIndicator color="white" />
              ) : (
                <>
                  <Ionicons name="people" color="white" size={24} />
                  <Text className="text-white text-xl font-bold ml-2">Group Chat</Text>
                </>
              )}
            </Pressable>
          )}
        </View>
      )}

      {isAuthor && (
				<View className="absolute bottom-10 left-6 right-6 flex justify-between gap-3">
          {!!isMenuOpen &&
            <View className="bg-white rounded-2xl shadow-lg border border-gray-100 mb-3 overflow-hidden">
              {!!listingData?.public_conversation_id && !listingData?.public_conversation_is_closed && (
                <Pressable
                  onPress={handleGroupChat}
                  disabled={isJoiningGroup}
                  className="flex-row items-center gap-3 px-5 py-4 active:bg-blue-50"
                >
                  <Ionicons name="people" size={20} color="#2563eb" />
                  <Text className="text-blue-600 text-base font-semibold">Group Chat</Text>
                </Pressable>
              )}
              <Pressable
                onPress={handleDelete}
                className="flex-row items-center gap-3 px-5 py-4 active:bg-red-50"
              >
                <Ionicons name="trash-outline" size={20} color="#ef4444" />
								<Text className="text-red-800 text-base font-semibold">Delete</Text>
              </Pressable>
              {listingData?.status === 'active' && (
                <Pressable
                  onPress={() => router.push(`/listing/${id}/edit`)}
                  className="flex-row items-center gap-3 px-5 py-4 active:bg-gray-50"
                >
                  <Ionicons name="pencil-sharp" size={20} color="#1e293b" />
                  <Text className="text-slate-800 text-base font-semibold">Edit</Text>
                </Pressable>
              )}
              {listingData?.status === 'active' && (
                <Pressable
                  onPress={handleMarkAsResolved}
                  className="flex-row items-center gap-3 px-5 py-4 active:bg-green-50"
                >
                  <Ionicons name="checkmark-circle-outline" size={20} color="#16a34a" />
                  <Text className="text-green-700 text-base font-semibold">Mark as resolved</Text>
                </Pressable>
              )}
              {listingData?.status === 'active' && (
                <Pressable
                  onPress={handleBump}
                  disabled={isBumping}
                  className="flex-row items-center gap-3 px-5 py-4 active:bg-yellow-50"
                >
                  {isBumping ? (
                    <ActivityIndicator size="small" color="#EAB308" />
                  ) : (
                    <Ionicons name="refresh-outline" size={20} color="#EAB308" />
                  )}
                  <View>
                    <Text className="text-yellow-700 text-base font-semibold">Bump listing</Text>
                    <Text className="text-gray-400 text-xs">Renews for {bumpDays} days</Text>
                  </View>
                </Pressable>
              )}
            </View>
          }
					<Pressable
            onPress={() => setIsMenuOpen(!isMenuOpen)}
            className="bg-slate-800 flex-1 py-4 rounded-2xl flex-row items-center justify-center gap-2 shadow-sm active:opacity-80"
          >
            {!!isMenuOpen && <Ionicons name="chevron-down-outline" color="#FFFFFF" size={18} />}
						<Text className="text-white text-lg font-semibold">Manage Listing</Text>
					</Pressable>
				</View>
			)}

			<Modal visible={isDeleting || deleteSuccess || isMarkingAsResolved || markResolvedSuccess} transparent animationType="fade">
				<View className="flex-1 justify-center items-center bg-black/50 px-6">
					<View className="bg-white w-full rounded-2xl p-6 items-center gap-3">

						{isDeleting ? (
							<>
								<ActivityIndicator size="large" color="#ef4444" />
								<Text className="text-gray-800 font-bold text-lg">Deleting listing...</Text>
								<Text className="text-gray-400 text-sm">Please wait a moment</Text>
							</>
						) : isMarkingAsResolved ? (
							<>
								<ActivityIndicator size="large" color="#16a34a" />
								<Text className="text-gray-800 font-bold text-lg">Marking as resolved...</Text>
								<Text className="text-gray-400 text-sm">Please wait a moment</Text>
							</>
						) : markResolvedSuccess ? (
							<>
								<FontAwesome5 name="check" size={24} color="#16a34a" />
								{!!markResolvedError ? (
									<Text className="text-red-500 text-sm font-medium text-center">{markResolvedError}</Text>
								) : (
									<Text className="text-xl font-bold text-center text-gray-800">Listing resolved!</Text>
								)}
								<Pressable
									className="bg-slate-800 w-full py-4 rounded-xl items-center mt-2 active:opacity-80"
									onPress={() => router.replace('/(tabs)')}
								>
									<Text className="text-white font-bold text-base">Go to home screen</Text>
								</Pressable>
							</>
						) : (
							<>
								<FontAwesome5 name="check" size={24} color="#ef4444" />
								{!!deleteError ? (
									<Text className="text-red-500 text-sm font-medium text-center">{deleteError}</Text>
								): (
                  <Text className="text-xl font-bold text-center text-gray-800">Listing deleted!</Text>
                )}

								<Pressable
									className="bg-slate-800 w-full py-4 rounded-xl items-center mt-2 active:opacity-80"
									onPress={() => router.replace('/(tabs)')}
								>
									<Text className="text-white font-bold text-base">Go to home screen</Text>
								</Pressable>
							</>
						)}

					</View>
				</View>
			</Modal>
      
		</View>
	)
}

export default Details
