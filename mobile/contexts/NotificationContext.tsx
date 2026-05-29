import React, { createContext, useCallback, useContext, useEffect, useRef, useState, ReactNode } from 'react'
import axios from 'axios'
import { useAuth } from '@/contexts/AuthContext'
import { NotificationEventMap, NotificationEventType } from '@/types/notifications'

const API_URL = process.env.EXPO_PUBLIC_API_URL
const WS_URL = process.env.EXPO_PUBLIC_WS_URL

type Handler<T> = (payload: T) => void
type AnyHandler = Handler<any>

interface NotificationContextType {
  subscribe: <K extends NotificationEventType>(
    eventType: K,
    handler: Handler<NotificationEventMap[K]>
  ) => () => void
  isConnected: boolean
}

const NotificationContext = createContext<NotificationContextType | undefined>(undefined)

export const NotificationProvider = ({ children }: { children: ReactNode }) => {
  const { authState } = useAuth()
  const [isConnected, setIsConnected] = useState(false)

  const wsRef = useRef<WebSocket | null>(null)
  const listenersRef = useRef<Map<string, Set<AnyHandler>>>(new Map())
  const reconnectTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const reconnectDelayRef = useRef(2000)
  const intentionalCloseRef = useRef(false)

  const connect = useCallback(async () => {
    if (wsRef.current || intentionalCloseRef.current) return

    try {
      const res = await axios.post(`${API_URL}/api/chats/ws-ticket/`)
      if (wsRef.current || intentionalCloseRef.current) return
      const ticket = res.data.ticket
      const ws = new WebSocket(`${WS_URL}/ws/notifications/?ticket=${ticket}`)
      wsRef.current = ws

      ws.onopen = () => {
        setIsConnected(true)
        reconnectDelayRef.current = 2000
      }

      ws.onclose = () => {
        setIsConnected(false)
        wsRef.current = null
        if (!intentionalCloseRef.current) {
          reconnectTimerRef.current = setTimeout(connect, reconnectDelayRef.current)
          reconnectDelayRef.current = Math.min(reconnectDelayRef.current * 2, 30000)
        }
      }

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          if (data.type === 'new_notification') {
            listenersRef.current.get(data.event_type)?.forEach(h => h(data.payload))
          }
        } catch { }
      }
    } catch {
      if (!intentionalCloseRef.current) {
        reconnectTimerRef.current = setTimeout(connect, reconnectDelayRef.current)
        reconnectDelayRef.current = Math.min(reconnectDelayRef.current * 2, 30000)
      }
    }
  }, [])

  useEffect(() => {
    if (authState.isLoading) return

    if (authState.isAuthenticated) {
      intentionalCloseRef.current = false
      connect()
    } else {
      intentionalCloseRef.current = true
      if (reconnectTimerRef.current) {
        clearTimeout(reconnectTimerRef.current)
        reconnectTimerRef.current = null
      }
      wsRef.current?.close()
      wsRef.current = null
    }

    return () => {
      intentionalCloseRef.current = true
      if (reconnectTimerRef.current) {
        clearTimeout(reconnectTimerRef.current)
        reconnectTimerRef.current = null
      }
      wsRef.current?.close()
      wsRef.current = null
    }
  }, [authState.isAuthenticated, authState.isLoading, connect])

  const subscribe = useCallback(<K extends NotificationEventType>(
    eventType: K,
    handler: Handler<NotificationEventMap[K]>
  ) => {
    if (!listenersRef.current.has(eventType)) {
      listenersRef.current.set(eventType, new Set())
    }
    listenersRef.current.get(eventType)!.add(handler as AnyHandler)
    return () => {
      listenersRef.current.get(eventType)?.delete(handler as AnyHandler)
    }
  }, [])

  return (
    <NotificationContext.Provider value={{ subscribe, isConnected }}>
      {children}
    </NotificationContext.Provider>
  )
}

export const useNotifications = () => {
  const context = useContext(NotificationContext)
  if (!context) {
    throw new Error('useNotifications must be used within NotificationProvider')
  }
  return context
}
