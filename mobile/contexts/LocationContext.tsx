import React, { createContext, useCallback, useContext, useEffect, useState, ReactNode } from 'react'
import AsyncStorage from '@react-native-async-storage/async-storage'
import * as Location from 'expo-location'
import { Coords } from '@/types/listingForm'

const STORAGE_KEY = 'location_preference'

export const RADIUS_OPTIONS = [1, 5, 10, 25, 40]

const DEFAULT_LOCATION: LocationPreference = {
  coords: { latitude: 51.2465, longitude: 22.5684 },
  label: 'Lublin',
  radius: 10,
}

export interface LocationPreference {
  coords: Coords
  label: string
  radius: number
}

interface LocationContextType {
  location: LocationPreference
  isReady: boolean
  setPlace: (coords: Coords, label: string) => void
  setRadius: (radius: number) => void
  resolveCurrentLocation: () => Promise<{ coords: Coords; label: string } | null>
}

const LocationContext = createContext<LocationContextType | undefined>(undefined)

const resolveLabel = async (coords: Coords): Promise<string> => {
  const results = await Location.reverseGeocodeAsync(coords).catch(() => [])
  const place = results[0]
  return place?.city ?? place?.subregion ?? place?.region ?? 'Selected location'
}

export const LocationProvider = ({ children }: { children: ReactNode }) => {
  const [location, setLocation] = useState<LocationPreference>(DEFAULT_LOCATION)
  const [isReady, setIsReady] = useState(false)

  const resolveCurrentLocation = useCallback(async (): Promise<{ coords: Coords; label: string } | null> => {
    const { status } = await Location.requestForegroundPermissionsAsync()
    if (status !== 'granted') return null

    const loc = await Location.getCurrentPositionAsync({}).catch(() => null)
    if (!loc) return null

    const coords = { latitude: loc.coords.latitude, longitude: loc.coords.longitude }
    const label = await resolveLabel(coords)
    return { coords, label }
  }, [])

  useEffect(() => {
    (async () => {
      const stored = await AsyncStorage.getItem(STORAGE_KEY).catch(() => null)
      if (stored) {
        try {
          setLocation(JSON.parse(stored))
          setIsReady(true)
          return
        } catch { }
      }

      const resolved = await resolveCurrentLocation()
      if (resolved) setLocation(prev => ({ ...prev, ...resolved }))
      setIsReady(true)
    })()
  }, [resolveCurrentLocation])

  useEffect(() => {
    if (!isReady) return
    AsyncStorage.setItem(STORAGE_KEY, JSON.stringify(location)).catch(() => { })
  }, [location, isReady])

  const setPlace = useCallback((coords: Coords, label: string) => {
    setLocation(prev => ({ ...prev, coords, label }))
  }, [])

  const setRadius = useCallback((radius: number) => {
    setLocation(prev => ({ ...prev, radius }))
  }, [])

  return (
    <LocationContext.Provider value={{ location, isReady, setPlace, setRadius, resolveCurrentLocation }}>
      {children}
    </LocationContext.Provider>
  )
}

export const useLocation = () => {
  const context = useContext(LocationContext)
  if (!context) {
    throw new Error('useLocation must be used within LocationProvider')
  }
  return context
}
