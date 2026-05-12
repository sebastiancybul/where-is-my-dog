import { View, Text, TextInput, Pressable, ActivityIndicator } from 'react-native'
import { useRouter } from 'expo-router'
import { Ionicons } from '@expo/vector-icons'
import { useState } from 'react'
import axios from 'axios'
import { useAuth } from '@/contexts/AuthContext'
import ConfirmModal from '@/components/ConfirmModal'

const API_URL = process.env.EXPO_PUBLIC_API_URL

export default function DeleteAccount() {
  const router = useRouter()
  const { onLogout } = useAuth()

  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [errors, setErrors] = useState<{ password?: string }>({})
  const [loading, setLoading] = useState(false)
  const [modalVisible, setModalVisible] = useState(false)

  const handleDelete = async () => {
    setModalVisible(false)
    setErrors({})
    setLoading(true)
    try {
      await axios.post(`${API_URL}/api/settings/account/delete/`, { password })
      await onLogout()
      router.replace('/(tabs)/profile')
    } catch (e: any) {
      const data = e.response?.data
      if (data) setErrors(data)
      setLoading(false)
    }
  }

  return (
    <View className="flex-1 bg-white">
      <View className="flex-row items-center px-6 pt-14 pb-4">
        <Pressable onPress={() => router.back()} className="p-2 -ml-2 active:opacity-80">
          <Ionicons name="arrow-back" size={24} color="#1f2937" />
        </Pressable>
        <Text className="text-2xl font-black text-gray-900 tracking-tight ml-2">Delete Account</Text>
      </View>

      <View className="px-6 mt-4 gap-5">
        <View className="bg-red-50 border border-red-100 rounded-2xl p-4">
          <Text className="text-red-600 font-semibold mb-1">This action is permanent</Text>
          <Text className="text-red-400 text-sm">Your account and all listings will be deleted and cannot be recovered.</Text>
        </View>

        <View>
          <Text className="text-xs font-bold text-gray-400 uppercase tracking-widest mb-2">Confirm Password</Text>
          <View className={`flex-row items-center bg-gray-50 border rounded-xl px-4 ${errors.password ? 'border-red-400' : 'border-gray-200'}`}>
            <TextInput
              value={password}
              onChangeText={setPassword}
              secureTextEntry={!showPassword}
              autoCapitalize="none"
              className="flex-1 py-3.5 text-base text-gray-900"
            />
            <Pressable onPress={() => setShowPassword(v => !v)} className="pl-2 active:opacity-80">
              <Ionicons name={showPassword ? 'eye-off-outline' : 'eye-outline'} size={20} color="#9ca3af" />
            </Pressable>
          </View>
          {errors.password && <Text className="text-red-500 text-sm mt-1">{errors.password}</Text>}
        </View>

        <Pressable
          onPress={() => setModalVisible(true)}
          disabled={loading || password.length === 0}
          className={`py-4 rounded-xl items-center mt-2 ${loading || password.length === 0 ? 'bg-red-200' : 'bg-red-500 active:opacity-80'}`}
        >
          {loading
            ? <ActivityIndicator color="white" />
            : <Text className="text-white font-semibold text-base">Delete My Account</Text>
          }
        </Pressable>
      </View>

      <ConfirmModal
        visible={modalVisible}
        title="Delete Account"
        message="Are you sure? This action is permanent and cannot be undone."
        confirmLabel="Delete Account"
        onConfirm={handleDelete}
        onCancel={() => setModalVisible(false)}
        destructive
      />
    </View>
  )
}
