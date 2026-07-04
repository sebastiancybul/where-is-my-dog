import { Stack } from "expo-router";
import './global.css'
import { AuthProvider } from "@/contexts/AuthContext";
import { PushProvider } from "@/contexts/PushContext";
import { NotificationProvider } from "@/contexts/NotificationContext";

export default function RootLayout() {
  return (
    <AuthProvider>
      <PushProvider>
      <NotificationProvider>
      <Stack>
        <Stack.Screen 
          name="(tabs)"
          options={{ headerShown:false }}
        />
        <Stack.Screen
          name="(auth)"
          options={{ headerShown: false }}
        />
        <Stack.Screen
          name="listing/[id]"
          options={{ headerShown: false }}
        />
        <Stack.Screen
          name="settings"
          options={{ headerShown: false }}
        />
        <Stack.Screen
          name="chat/[id]"
          options={{ headerShown: false }}
        />
      </Stack>
      </NotificationProvider>
      </PushProvider>
    </AuthProvider>
  )
}
