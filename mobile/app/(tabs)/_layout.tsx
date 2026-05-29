import React, { useEffect, useState } from 'react'
import { Tabs } from "expo-router"
import { Ionicons } from '@expo/vector-icons'
import { useAuth } from "@/contexts/AuthContext"
import { useNotifications } from "@/contexts/NotificationContext"

const TabsLayout = () => {
  const { authState } = useAuth();
  const { subscribe } = useNotifications();
  const [unreadCount, setUnreadCount] = useState(0);

  useEffect(() => {
    return subscribe('new_message', () => {
      setUnreadCount(prev => prev + 1);
    });
  }, [subscribe]);

  return (
    <Tabs>
        <Tabs.Screen
          name="index"
          options={{
              title: 'Home',
              headerShown: false,
              tabBarIcon: ({ color, size, focused }) => (
                <Ionicons 
                  name={focused ? 'home' : 'home-outline'} 
                  size={size} 
                  color={color} 
                />
              )
          }}
        />
        <Tabs.Screen 
          name="create"
          options={{
            title: 'Create',
            headerShown: false,
            href: authState.isAuthenticated ? undefined : null,
            tabBarIcon: ({ color, size, focused }) => (
              <Ionicons 
                name={focused ? 'add-circle' : 'add-circle-outline'} 
                size={size} 
                color={color} 
              />
            )
          }}
        />
        <Tabs.Screen
          name="chats"
          options={{
            title: 'Chats',
            headerShown: false,
            href: authState.isAuthenticated ? undefined : null,
            tabBarBadge: unreadCount > 0 ? unreadCount : undefined,
            tabBarIcon: ({ color, size, focused }) => (
              <Ionicons
                name={focused ? 'chatbubbles' : 'chatbubbles-outline'}
                size={size}
                color={color}
              />
            )
          }}
          listeners={{
            tabPress: () => setUnreadCount(0),
          }}
        />
        <Tabs.Screen
          name="profile"
          options={{
            title: 'Profile',
            headerShown: false,
            tabBarIcon: ({ color, size, focused }) => (
              <Ionicons 
                name={focused ? 'person' : 'person-outline'} 
                size={size} 
                color={color} 
              />
            )
          }}
        />
    </Tabs>
  )
}

export default TabsLayout