import { View, Text, Pressable } from 'react-native'
import { useRouter } from 'expo-router'
import { Ionicons } from '@expo/vector-icons'
import { useAuth } from '@/contexts/AuthContext'

export default function SettingsIndex() {
  const router = useRouter()
  const { authState, onLogout } = useAuth()
  const user = authState.user
  if (!user) return null

  return (
    <View className="flex-1 bg-white">
      <View className="flex-row items-center px-6 pt-14 pb-4">
        <Pressable onPress={() => router.back()} className="p-2 -ml-2 active:opacity-80">
          <Ionicons name="arrow-back" size={24} color="#1f2937" />
        </Pressable>
        <Text className="text-2xl font-black text-gray-900 tracking-tight ml-2">Settings</Text>
      </View>

      <View className="px-6 py-4 flex-row items-center gap-4 border-b border-gray-100 mb-2">
        <View className="w-14 h-14 rounded-full bg-gray-900 items-center justify-center">
          <Text className="text-2xl font-bold text-white">{user.username[0].toUpperCase()}</Text>
        </View>
        <View>
          <Text className="text-base font-bold text-gray-900">{user.username}</Text>
          <Text className="text-sm text-gray-400">{user.email}</Text>
        </View>
      </View>

      <View className="px-4 mt-4">
        <Pressable
          onPress={() => router.push('/settings/edit-username')}
          className="flex-row items-center px-4 py-4 border-b border-gray-100 active:opacity-80"
        >
          <View className="w-9 h-9 rounded-full bg-gray-100 items-center justify-center mr-4">
            <Ionicons name="person-outline" size={18} color="#1f2937" />
          </View>
          <View className="flex-1">
            <Text className="text-base font-medium text-gray-900">Change Username</Text>
            <Text className="text-sm text-gray-400">{user.username}</Text>
          </View>
          <Ionicons name="chevron-forward" size={18} color="#9ca3af" />
        </Pressable>

        <Pressable
          onPress={() => router.push('/settings/edit-phone')}
          className="flex-row items-center px-4 py-4 border-b border-gray-100 active:opacity-80"
        >
          <View className="w-9 h-9 rounded-full bg-gray-100 items-center justify-center mr-4">
            <Ionicons name="call-outline" size={18} color="#1f2937" />
          </View>
          <View className="flex-1">
            <Text className="text-base font-medium text-gray-900">Change Phone</Text>
            <Text className="text-sm text-gray-400">{user.phone ?? 'Not set'}</Text>
          </View>
          <Ionicons name="chevron-forward" size={18} color="#9ca3af" />
        </Pressable>

        <Pressable
          onPress={() => router.push('/settings/change-password')}
          className="flex-row items-center px-4 py-4 border-b border-gray-100 active:opacity-80"
        >
          <View className="w-9 h-9 rounded-full bg-gray-100 items-center justify-center mr-4">
            <Ionicons name="lock-closed-outline" size={18} color="#1f2937" />
          </View>
          <Text className="flex-1 text-base font-medium text-gray-900">Change Password</Text>
          <Ionicons name="chevron-forward" size={18} color="#9ca3af" />
        </Pressable>

        <Pressable
          onPress={async () => { await onLogout(); router.replace('/(tabs)/profile') }}
          className="flex-row items-center px-4 py-4 border-b border-gray-100 active:opacity-80"
        >
          <View className="w-9 h-9 rounded-full bg-gray-100 items-center justify-center mr-4">
            <Ionicons name="log-out-outline" size={18} color="#1f2937" />
          </View>
          <Text className="flex-1 text-base font-medium text-gray-900">Log Out</Text>
        </Pressable>

        <Pressable
          onPress={() => router.push('/settings/delete-account')}
          className="flex-row items-center px-4 py-4 active:opacity-80"
        >
          <View className="w-9 h-9 rounded-full bg-red-50 items-center justify-center mr-4">
            <Ionicons name="trash-outline" size={18} color="#ef4444" />
          </View>
          <Text className="flex-1 text-base font-medium text-red-500">Delete Account</Text>
          <Ionicons name="chevron-forward" size={18} color="#9ca3af" />
        </Pressable>
      </View>
    </View>
  )
}
