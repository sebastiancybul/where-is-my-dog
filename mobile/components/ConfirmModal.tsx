import { Modal, View, Text, Pressable } from 'react-native'

interface ConfirmModalProps {
  visible: boolean
  title: string
  message: string
  confirmLabel: string
  onConfirm: () => void
  onCancel: () => void
  destructive?: boolean
}

export default function ConfirmModal({ visible, title, message, confirmLabel, onConfirm, onCancel, destructive }: ConfirmModalProps) {
  return (
    <Modal visible={visible} transparent animationType="fade" onRequestClose={onCancel}>
      <Pressable className="flex-1 bg-black/50 justify-end" onPress={onCancel}>
        <Pressable onPress={() => {}} className="bg-white rounded-t-3xl px-6 pt-6 pb-10">
          <View className="w-10 h-1 bg-gray-200 rounded-full self-center mb-6" />
          <Text className="text-xl font-black text-gray-900 tracking-tight mb-2">{title}</Text>
          <Text className="text-sm text-gray-400 mb-8">{message}</Text>
          <View className="gap-3">
            <Pressable
              onPress={onConfirm}
              className={`py-4 rounded-xl items-center active:opacity-80 ${destructive ? 'bg-red-500' : 'bg-gray-900'}`}
            >
              <Text className="text-white font-semibold text-base">{confirmLabel}</Text>
            </Pressable>
            <Pressable onPress={onCancel} className="py-4 rounded-xl items-center bg-gray-100 active:opacity-80">
              <Text className="text-gray-900 font-semibold text-base">Cancel</Text>
            </Pressable>
          </View>
        </Pressable>
      </Pressable>
    </Modal>
  )
}
