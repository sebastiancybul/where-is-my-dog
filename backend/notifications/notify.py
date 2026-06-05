from channels.layers import get_channel_layer


async def notify_user(user_id, event_type, payload):
    channel_layer = get_channel_layer()
    group_name = f"user_{user_id}"
    await channel_layer.group_send(
        group_name,
        {
            "type": "new_notification",
            "event_type": event_type,
            "payload": payload,
        },
    )
