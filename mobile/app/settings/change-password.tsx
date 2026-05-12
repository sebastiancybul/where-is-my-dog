import { View, Text, TextInput, Pressable, ActivityIndicator } from 'react-native'
import { useRouter } from 'expo-router'
import { Ionicons } from '@expo/vector-icons'
import { useState } from 'react'
import axios from 'axios'
import ConfirmModal from '@/components/ConfirmModal'

const API_URL = process.env.EXPO_PUBLIC_API_URL

export default function ChangePassword() {
  const router = useRouter()

  const [password, setPassword] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [newPassword2, setNewPassword2] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [showNewPassword, setShowNewPassword] = useState(false)
  const [showNewPassword2, setShowNewPassword2] = useState(false)
  const [errors, setErrors] = useState<{ password?: string; new_password?: string; new_password2?: string }>({})
  const [loading, setLoading] = useState(false)
  const [modalVisible, setModalVisible] = useState(false)

  const canSubmit = password.length > 0 && newPassword.length > 0 && newPassword2.length > 0

  const handleSave = async () => {
    setModalVisible(false)
    setErrors({})
    setLoading(true)
    try {
      await axios.patch(`${API_URL}/api/settings/password/`, { password, new_password: newPassword, new_password2: newPassword2 })
      router.back()
    } catch (e: any) {
      const data = e.response?.data
      if (data) setErrors(data)
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
        <Text className="text-2xl font-black text-gray-900 tracking-tight ml-2">Change Password</Text>
      </View>

      <View className="px-6 mt-4 gap-5">
        <View>
          <Text className="text-xs font-bold text-gray-400 uppercase tracking-widest mb-2">Current Password</Text>
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

        <View>
          <Text className="text-xs font-bold text-gray-400 uppercase tracking-widest mb-2">New Password</Text>
          <View className={`flex-row items-center bg-gray-50 border rounded-xl px-4 ${errors.new_password ? 'border-red-400' : 'border-gray-200'}`}>
            <TextInput
              value={newPassword}
              onChangeText={setNewPassword}
              secureTextEntry={!showNewPassword}
              autoCapitalize="none"
              className="flex-1 py-3.5 text-base text-gray-900"
            />
            <Pressable onPress={() => setShowNewPassword(v => !v)} className="pl-2 active:opacity-80">
              <Ionicons name={showNewPassword ? 'eye-off-outline' : 'eye-outline'} size={20} color="#9ca3af" />
            </Pressable>
          </View>
          {errors.new_password && <Text className="text-red-500 text-sm mt-1">{errors.new_password}</Text>}
        </View>

        <View>
          <Text className="text-xs font-bold text-gray-400 uppercase tracking-widest mb-2">Confirm New Password</Text>
          <View className={`flex-row items-center bg-gray-50 border rounded-xl px-4 ${errors.new_password2 ? 'border-red-400' : 'border-gray-200'}`}>
            <TextInput
              value={newPassword2}
              onChangeText={setNewPassword2}
              secureTextEntry={!showNewPassword2}
              autoCapitalize="none"
              className="flex-1 py-3.5 text-base text-gray-900"
            />
            <Pressable onPress={() => setShowNewPassword2(v => !v)} className="pl-2 active:opacity-80">
              <Ionicons name={showNewPassword2 ? 'eye-off-outline' : 'eye-outline'} size={20} color="#9ca3af" />
            </Pressable>
          </View>
          {errors.new_password2 && <Text className="text-red-500 text-sm mt-1">{errors.new_password2}</Text>}
        </View>

        <Pressable
          onPress={() => setModalVisible(true)}
          disabled={loading || !canSubmit}
          className={`py-4 rounded-xl items-center mt-2 ${loading || !canSubmit ? 'bg-gray-300' : 'bg-gray-900 active:opacity-80'}`}
        >
          {loading
            ? <ActivityIndicator color="white" />
            : <Text className="text-white font-semibold text-base">Save Password</Text>
          }
        </Pressable>
      </View>

      <ConfirmModal
        visible={modalVisible}
        title="Change Password"
        message="Are you sure you want to change your password?"
        confirmLabel="Change Password"
        onConfirm={handleSave}
        onCancel={() => setModalVisible(false)}
      />
    </View>
  )
}
