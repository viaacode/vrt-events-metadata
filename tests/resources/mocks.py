import pytest


@pytest.fixture
def mock_rabbit(mocker):
    def mock_init(self):
        print(f"Initiating Rabbit connection.")
        pass

    def mock_send_message(self, body, routing_key):
        print(f"Sending Rabbit message.")
        pass

    def mock_listen(self, on_message_callback, queue=None):
        print(f"Listening for Rabbit messages.")
        pass

    from app.services.rabbit import RabbitClient

    mocker.patch.object(RabbitClient, "__init__", mock_init)
    mocker.patch.object(RabbitClient, "send_message", mock_send_message)
    mocker.patch.object(RabbitClient, "listen", mock_listen)


@pytest.fixture
def mock_mediahaven(mocker):
    def mock_init(self, url, grant):
        print(f"Initiating MH Client.")
        pass

    def mock_request_token(self, user, password):
        print(f"Mocking getting a token.")
        pass

    from mediahaven import MediaHaven
    from mediahaven.oauth2 import ROPCGrant

    mocker.patch.object(MediaHaven, "__init__", mock_init)
    mocker.patch.object(ROPCGrant, "request_token", mock_request_token)
