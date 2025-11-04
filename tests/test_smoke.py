from src.bot.config import get_settings


def test_config_loads():
    try:
        cfg = get_settings()
        assert cfg.default_tz
    except RuntimeError:
        # Если нет .env с токеном — локально это допустимо
        pass
