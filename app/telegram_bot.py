from app.config import settings

COMMANDS = ['/status','/balance','/positions','/trades','/signals','/kronos','/risk','/pause','/resume','/emergency']

def authorized(user_id: int) -> bool:
    ids = {x.strip() for x in settings.telegram_admin_ids.split(',') if x.strip()}
    return str(user_id) in ids
