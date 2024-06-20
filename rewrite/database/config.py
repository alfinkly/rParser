from environs import Env


class EnvSettings:
    def psycopg_url(self):
        return f"postgresql+psycopg2://{self.user}:{self.password}@{self.host}:{self.port}/{self.dbname}"

    def asyncpg_url(self):
        return f"postgresql+asyncpg://{self.user}:{self.password}@{self.host}:{self.port}/{self.dbname}"

    def __init__(self):
        env = Env()
        env.read_env(".env")
        self.host = env.str("DB_HOST")
        self.port = env.str("DB_PORT")
        self.user = env.str("DB_USER")
        self.password = env.str("DB_PASSWORD")
        self.dbname = env.str("DB_NAME")
        self.bot_token = env.str("BOT_TOKEN")
        self.timer = env.int("TIMER")
        self.logging_level = env.int("LOGGING_LEVEL")
        self.small_sleep = env.int("SMALL_SLEEP")
        self.geckodriver_src = env.str("GECKODRIVER_SOURCE")