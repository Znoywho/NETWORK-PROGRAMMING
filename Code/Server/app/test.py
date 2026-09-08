import bcrypt
from db import session
from models.user import User


def _check_user(username):
    return session.query(User).filter(User.username == username).first()


def hash_password(password: str) -> str:
    # Convert string password to bytes
    password_bytes = password.encode("utf-8")

    # Generate a secure random salt
    salt = bcrypt.gensalt()

    # Hash the password
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    password_bytes = plain_password.encode("utf-8")

    hashed_bytes = hashed_password.encode("utf-8")

    return bcrypt.checkpw(password_bytes, hashed_bytes)


def _login_handler(self, message, websocket):
    # NOTE:
    # user login with username
    # check database existence of user
    # if dont exist force user login with password
    user = self._check_user(message["username"])
    if user is None:
        return self._error(None, "USER_NOT_EXIST", "User khong ton tai")
    if not (verify_password(message["password"], user.password_hash)):
        return self._error(None, "WRONG_PASSWORD", "User sai mat khau")

    player_id = str(user.id)

    response = self._targeted([player_id], {"type": "login", "username": user.username, "playerId": player_id})

    broadcast = self._broadcast({"type": "online_players", "players": self._list_online_players()})

    return [response, broadcast]


print(_check_user("hao"))
