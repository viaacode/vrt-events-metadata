import pytest


@pytest.fixture(autouse=True)
def env_setup(monkeypatch):
    monkeypatch.setenv("MEDIAHAVEN_USERNAME", "username")
    monkeypatch.setenv("MEDIAHAVEN_PASSWORD", "password")
    monkeypatch.setenv("MEDIAHAVEN_HOST", "host")
    monkeypatch.setenv("FTP_HOST", "host")
    monkeypatch.setenv("FTP_USER", "username")
    monkeypatch.setenv("FTP_PASSWORD", "password")
    monkeypatch.setenv("RABBITMQ_USERNAME", "username")
    monkeypatch.setenv("RABBITMQ_PASSWORD", "password")
    monkeypatch.setenv("RABBITMQ_HOST", "host")
    monkeypatch.setenv("RABBITMQ_QUEUE", "queue")
    monkeypatch.setenv("RABBITMQ_EXCHANGE", "exchange")
    monkeypatch.setenv("RABBITMQ_GET_SUBTITLES_ROUTING_KEY", "routingkey")
    monkeypatch.setenv("MTD_TRANSFORMER", "url")
