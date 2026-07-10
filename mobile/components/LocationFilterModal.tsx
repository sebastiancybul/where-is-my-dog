import { View, Text, Pressable, Modal, TextInput, ActivityIndicator, ScrollView, Keyboard } from 'react-native'
import React, { useEffect, useRef, useState } from 'react'
import { Ionicons } from '@expo/vector-icons'
import { useLocation, RADIUS_OPTIONS, LocationPreference } from '@/contexts/LocationContext'
import { Coords } from '@/types/listingForm'

type Props = {
  visible: boolean
  onClose: () => void
  onApplied?: () => void
}

type Suggestion = {
  id: string
  label: string
  sublabel: string
  coords: Coords
}

const searchPlaces = async (q: string): Promise<Suggestion[]> => {
  const res = await fetch(
    `https://nominatim.openstreetmap.org/search?format=jsonv2&addressdetails=1&countrycodes=pl&limit=8&q=${encodeURIComponent(q)}`,
    { headers: { 'User-Agent': 'where-is-my-dog' } }
  ).catch(() => null)
  if (!res?.ok) return []

  const data = await res.json().catch(() => null)
  if (!Array.isArray(data)) return []

  return data
    .filter((d: any) => {
      const a = d.address ?? {}
      return a.city || a.town || a.village || a.hamlet
    })
    .map((d: any) => {
      const a = d.address ?? {}
      const label = a.city ?? a.town ?? a.village ?? a.hamlet
      const sublabel = [a.county, a.state].filter(Boolean).join(', ')
      return {
        id: String(d.place_id),
        label,
        sublabel,
        coords: { latitude: parseFloat(d.lat), longitude: parseFloat(d.lon) },
      }
    })
}

const LocationFilterModal = ({ visible, onClose, onApplied }: Props) => {
  const { location, resolveCurrentLocation, setPlace, setRadius } = useLocation()
  const [draft, setDraft] = useState<LocationPreference>(location)
  const [query, setQuery] = useState('')
  const [suggestions, setSuggestions] = useState<Suggestion[]>([])
  const [loadingGps, setLoadingGps] = useState(false)
  const [loadingSuggestions, setLoadingSuggestions] = useState(false)
  const [error, setError] = useState('')
  const skipSearchRef = useRef(false)

  useEffect(() => {
    if (!visible) return
    setDraft(location)
    setQuery('')
    setSuggestions([])
    setError('')
  }, [visible])

  useEffect(() => {
    if (skipSearchRef.current) {
      skipSearchRef.current = false
      return
    }

    const q = query.trim()
    if (q.length < 2) {
      setSuggestions([])
      return
    }

    const handle = setTimeout(async () => {
      setLoadingSuggestions(true)
      const results = await searchPlaces(q)
      setLoadingSuggestions(false)
      setSuggestions(results)
    }, 400)

    return () => clearTimeout(handle)
  }, [query])

  const handleGps = async () => {
    setError('')
    setLoadingGps(true)
    const resolved = await resolveCurrentLocation()
    setLoadingGps(false)
    if (!resolved) {
      setError('Could not get your location. Check permissions or enter a city.')
      return
    }
    setDraft(prev => ({ ...prev, ...resolved }))
  }

  const handleSelect = (s: Suggestion) => {
    setDraft(prev => ({ ...prev, coords: s.coords, label: s.label }))
    skipSearchRef.current = true
    setQuery(s.label)
    setSuggestions([])
    Keyboard.dismiss()
  }

  const handleApply = () => {
    setPlace(draft.coords, draft.label)
    setRadius(draft.radius)
    onApplied?.()
    onClose()
  }

  return (
    <Modal visible={visible} animationType="slide" onRequestClose={onClose}>
      <View className="flex-1 bg-white pt-safe">
        <View className="flex-row items-center justify-between px-4 py-3 border-b border-gray-100">
          <Pressable onPress={onClose} className="py-1 active:opacity-60">
            <Text className="text-base text-gray-500">Cancel</Text>
          </Pressable>
          <Text className="text-lg font-semibold">Search area</Text>
          <Pressable onPress={handleApply} className="py-1 active:opacity-60">
            <Text className="text-base font-bold text-blue-600">Apply</Text>
          </Pressable>
        </View>

        <View className="flex-1 px-4 pt-4 pb-safe">
          <View className="flex-row items-center bg-blue-50 rounded-2xl px-4 py-3 mb-5">
            <Ionicons name="location" size={24} color="#2563EB" />
            <View className="ml-2 flex-1">
              <Text className="text-base font-bold text-gray-800">{draft.label}</Text>
              <Text className="text-sm text-blue-700">Showing lost and found dogs within {draft.radius} km</Text>
            </View>
          </View>

          <Pressable
            onPress={handleGps}
            disabled={loadingGps}
            className="flex-row bg-black gap-2 justify-center items-center py-3 rounded-xl active:opacity-80 mb-5"
          >
            {loadingGps ? (
              <ActivityIndicator color="white" />
            ) : (
              <>
                <Ionicons name="navigate" size={22} color="white" />
                <Text className="text-white text-lg font-semibold">Use My Current Location</Text>
              </>
            )}
          </Pressable>

          <Text className="text-xs font-bold text-gray-400 uppercase tracking-widest mb-2.5">Or enter a city</Text>
          <View className="flex-row items-center border border-gray-200 rounded-xl px-3">
            <Ionicons name="search" size={20} color="#9CA3AF" />
            <TextInput
              className="flex-1 px-2 py-3 text-gray-800"
              style={{ fontSize: 16 }}
              placeholder="e.g. Warsaw"
              placeholderTextColor="#9CA3AF"
              value={query}
              onChangeText={setQuery}
              autoCapitalize="words"
              autoCorrect={false}
            />
            {loadingSuggestions && <ActivityIndicator size="small" color="#9CA3AF" />}
          </View>

          <View className="flex-1 mt-2">
            <ScrollView keyboardShouldPersistTaps="handled">
              {suggestions.map(s => (
                <Pressable
                  key={s.id}
                  onPress={() => handleSelect(s)}
                  className="px-4 py-3 border-b border-gray-100 active:bg-gray-50"
                >
                  <Text className="text-base font-semibold text-gray-800">{s.label}</Text>
                  {!!s.sublabel && <Text className="text-sm text-gray-400">{s.sublabel}</Text>}
                </Pressable>
              ))}
            </ScrollView>
          </View>

          {!!error && <Text className="text-red-500 text-sm font-medium mb-2">{error}</Text>}

          <View className="pt-4 border-t border-gray-100">
            <Text className="text-xs font-bold text-gray-400 uppercase tracking-widest mb-2.5">Radius</Text>
            <View className="flex-row flex-wrap gap-2">
              {RADIUS_OPTIONS.map(km => {
                const active = draft.radius === km
                return (
                  <Pressable
                    key={km}
                    onPress={() => setDraft(prev => ({ ...prev, radius: km }))}
                    className={`px-4 py-2 rounded-full border-2 active:opacity-80 ${active ? 'bg-blue-600 border-blue-600' : 'bg-white border-gray-100'}`}
                  >
                    <Text className={`text-sm font-semibold ${active ? 'text-white' : 'text-gray-700'}`}>{km} km</Text>
                  </Pressable>
                )
              })}
            </View>
          </View>
        </View>
      </View>
    </Modal>
  )
}

export default LocationFilterModal
