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
