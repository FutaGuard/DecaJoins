from pyrogram.types import User


def fullname(user: User) -> str:
    if user.last_name:
        return user.first_name + ' ' + user.last_name
    return user.first_name
