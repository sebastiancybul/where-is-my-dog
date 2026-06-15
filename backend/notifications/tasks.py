from celery import shared_task

from . import presence, push


@shared_task
def send_push_to_user(user_id, event_type, title, body, data=None):
    if presence.is_online(user_id):
        return None

    return push.send_to_user(
        user_id=user_id,
        event_type=event_type,
        title=title,
        body=body,
        data=data,
    )
