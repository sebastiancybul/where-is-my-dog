import { View, Text, TextInput, Pressable, ActivityIndicator, KeyboardAvoidingView, ScrollView } from 'react-native'
import React, { useState } from 'react'
import { useAuth } from "@/contexts/AuthContext"
import { useRouter } from "expo-router"
import { Ionicons } from "@expo/vector-icons"

const Login = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [errorMsg, setErrorMsg] = useState('');
  const [loading, setLoading] = useState<boolean>(false);
  const [showPassword, setShowPassword] = useState(false);

  const { onLogin } = useAuth();
  const router = useRouter();

  const handleLogin = async () => {
    setLoading(true);
    const result = await onLogin({email, password});
    setLoading(false);
    if(result.error) {
      setErrorMsg(result.msg)
      setPassword('');
    } else {
      router.back();
    }
  };

  return (
    <KeyboardAvoidingView
      behavior='padding'
      className="flex-1"
    >
      <ScrollView
        contentContainerStyle={{ flexGrow: 1 }}
        keyboardShouldPersistTaps="handled"
        scrollEnabled={false}
      >
        <View className="flex-1 px-6 justify-center">
          <Pressable
            onPress={() => router.back()}
            className="absolute top-12 left-6 active:opacity-80"
          >
            <Ionicons name="arrow-back" size={28} color="#374151" />
          </Pressable>

          <Text className="text-3xl font-bold mb-8 text-center">Login</Text>

          <TextInput
            placeholder="Email"
            placeholderTextColor="#9CA3AF" 
            value={email}
            onChangeText={setEmail}
            keyboardType="email-address"
            autoCapitalize="none"
            className="border border-gray-300 rounded-lg p-4 mb-4"
            autoFocus={true}
          />

          <View className="border border-gray-300 rounded-lg flex-row items-center mb-6">
            <TextInput
              placeholder="Password"
              placeholderTextColor="#9CA3AF"
              value={password}
              onChangeText={setPassword}
              secureTextEntry={!showPassword}
              className="flex-1 p-4"
            />
            <Pressable 
              onPress={() => setShowPassword(v => !v)} className="pr-4 active:opacity-80"
            >
              <Ionicons name={showPassword ? 'eye-off' : 'eye'} size={20} color="#9CA3AF" />
            </Pressable>
          </View>

          {errorMsg && (
            <View className="bg-red-100 rounded-lg p-4 mb-4">
              <Text className="text-red-700 font-bold text-center">{errorMsg}</Text>
            </View>
          )}

          <Pressable
            onPress={handleLogin}
            disabled={loading || !email || !password }
            className={`bg-blue-600 py-4 rounded-lg mb-4 active:opacity-80 ${(!email || !password || loading) ? 'opacity-60' : ''}`}
          >
            {loading
              ? <ActivityIndicator color="white" />
              : <Text className="text-white text-center font-semibold">Login</Text>
            }
          </Pressable>

          <Pressable onPress={() => router.push('/(auth)/register')} className="active:opacity-80">
            <Text className="text-center text-blue-600 font-medium">
              Don&apos;t have an account? Sign up
            </Text>
          </Pressable>

        </View>
      </ScrollView>
    </KeyboardAvoidingView>
  )
}

export default Login