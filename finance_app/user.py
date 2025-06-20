from dataclasses import dataclass, field
from typing import Dict
import hashlib

@dataclass
class User:
    username: str
    password_hash: str

    @classmethod
    def create(cls, username: str, password: str) -> 'User':
        return cls(username=username, password_hash=hashlib.sha256(password.encode()).hexdigest())

    def verify(self, password: str) -> bool:
        return self.password_hash == hashlib.sha256(password.encode()).hexdigest()

@dataclass
class UserManager:
    users: Dict[str, User] = field(default_factory=dict)

    def register(self, username: str, password: str) -> bool:
        if username in self.users:
            return False
        self.users[username] = User.create(username, password)
        return True

    def login(self, username: str, password: str) -> bool:
        user = self.users.get(username)
        if not user:
            return False
        return user.verify(password)
