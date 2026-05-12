import { View, Text, TextInput, Pressable, ActivityIndicator } from 'react-native'
import { useRouter } from 'expo-router'
import { Ionicons } from '@expo/vector-icons'
import { useState } from 'react'
import axios from 'axios'
import { useAuth } from '@/contexts/AuthContext'
import ConfirmModal from '@/components/ConfirmModal'

const API_URL = process.env.EXPO_PUBLIC_API_URL

export default function EditPhone() {
  const router = useRouter()
  const { authState, onUpdateUser } = useAuth()
  const user = authState.user

  const [phone, setPhone] = useState(user?.phone ?? '')
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const [modalVisible, setModalVisible] = useState(false)

  if (!user) return null

  const hasChanges = phone !== (user.phone ?? '')

  const handleSave = async () => {
    setModalVisible(false)
    setError(null)
    setLoading(true)
    try {
      const response = await axios.patch(`${API_URL}/api/settings/profile/`, { phone: phone || null })
      onUpdateUser(response.data)
      router.back()
    } catch (e: any) {
      setError(e.response?.data?.phone ?? 'Something went wrong')
    } finally {
      setLoading(false)
    }
  }

  return (
    <View className="flex-1 bg-white">
      <View className="flex-row items-center px-6 pt-14 pb-4">
        <Pressable onPress={() => router.back()} className="p-2 -ml-2 active:opacity-80">
          <Ionicons name="arrow-back" size={24} color="#1f2937" />
        </Pressable>
        <Text className="text-2xl font-black text-gray-900 tracking-tight ml-2">Phone</Text>
      </View>

      <View className="px-6 mt-4 gap-5">
        <View>
          <TextInput
            value={phone}
            onChangeText={setPhone}
            keyboardType="phone-pad"
            placeholder="Optional"
            placeholderTextColor="#9ca3af"
            autoFocus
            className={`bg-gray-50 border rounded-xl px-4 py-3.5 text-base text-gray-900 ${error ? 'border-red-400' : 'border-gray-200'}`}
          />
          {error && <Text className="text-red-500 text-sm mt-1">{error}</Text>}
        </View>

        <Pressable
          onPress={() => setModalVisible(true)}
          disabled={loading || !hasChanges}
          className={`py-4 rounded-xl items-center ${loading || !hasChanges ? 'bg-gray-300' : 'bg-gray-900 active:opacity-80'}`}
        >
          {loading
            ? <ActivityIndicator color="white" />
            : <Text className="text-white font-semibold text-base">Save</Text>
          }
        </Pressable>
      </View>

      <ConfirmModal
        visible={modalVisible}
        title="Change Phone"
        message={`Change your phone number to "${phone || 'none'}"?`}
        confirmLabel="Save"
        onConfirm={handleSave}
        onCancel={() => setModalVisible(false)}
      />
    </View>
  )
}
