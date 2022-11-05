def convert_entities(entities):
    result = []
    for entity in entities:
        entity_name = str(entity.type.name).lower()
        converted_entity = {
            "offset": entity.offset,
            "length": entity.length,
            "type": entity_name
        }
        if entity_name == "custom_emoji":
            converted_entity["custom_emoji_id"] = str(entity.custom_emoji_id)
        result.append(converted_entity)
    return result


def get_from(message):
    result = None
    if message.from_user:
        result = {
            'id': message.from_user.id,
            'first_name': message.from_user.first_name,
            'last_name': message.from_user.last_name,
            'username': message.from_user.username
        }
    if message.forward_from_chat:
        result = {
            'id': message.forward_from_chat.id,
            'name': message.forward_from_chat.title,
            'username': message.forward_from_chat.username
        }
    if message.forward_from or message.forward_sender_name or message.forward_from_chat:
        if message.forward_from_chat:
            result = {
                'id': message.forward_from_chat.id,
                'name': message.forward_from_chat.title,
                'username': message.forward_from_chat.username
            }
        elif message.forward_sender_name:
            result = {
                'id': message.forward_sender_name.__hash__(),
                'name': message.forward_sender_name,
                'username': "HiddenSender"
            }
        else:
            result = {
                'id': message.forward_from.id,
                'first_name': message.forward_from.first_name,
                'last_name': message.forward_from.last_name,
                'username': message.forward_from.username
            }
    return result


def get_media(message):
    media = None
    if message.photo:
        media = {
            'file_id': message.photo.file_id,
            'type': "photo"
        }
    if message.sticker:
        media = {
            'file_id': message.sticker.file_id,
            'type': "sticker"
        }
    return media


def get_text(message, is_reply: bool):
    msg = message.text

    if message.photo:
        if message.caption:
            if is_reply:
                msg = "🖼️ " + message.caption
            else:
                msg = message.caption
        else:
            msg = "🖼️"

    if message.sticker:
        if message.sticker.emoji:
            if is_reply:
                msg = "Стикер " + message.sticker.emoji
            else:
                msg = message.sticker.emoji
        else:
            msg = "Стикер"

    return msg


def convert_message(message, value: bool):
    if value is False:
        if not message.sticker and message.caption:
            message.text = get_text(message, value)
    result = {
        'from': get_from(message),
        'text': message.text,
        'entities': None,
        'reply_to_message': None,
        'media': get_media(message)
    }
    if message.entities:
        result['entities'] = convert_entities(message.entities)
    if message.reply_to_message:
        reply = message.reply_to_message
        reply.text = get_text(message.reply_to_message, True)
        result['reply_to_message'] = convert_message(reply, True)
    return result
