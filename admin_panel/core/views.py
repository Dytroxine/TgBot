from .models import User

async def get_user_statistics():
    return await User.objects.acount()

