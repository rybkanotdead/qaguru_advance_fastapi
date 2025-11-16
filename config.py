import os

class Server:
    def __init__(self, env: str):
        env = env.lower()
        urls = {
            "dev": os.environ.get("APP_URL", "http://127.0.0.1:8000"),
            "rc": os.environ.get("APP_URL", "http://127.0.0.1:8000"),
        }
        if env not in urls:
            raise ValueError(f"Unknown environment: {env}")
        self.app = urls[env]
