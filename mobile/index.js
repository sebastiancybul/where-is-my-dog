import { Platform } from 'react-native'

if (Platform.OS === 'android') {
  const messaging = require('@react-native-firebase/messaging').default
  messaging().setBackgroundMessageHandler(async () => {})
}

require('expo-router/entry')
