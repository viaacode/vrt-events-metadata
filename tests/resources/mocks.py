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
    def mock_init(self, config):
        print(f"Initiating MH Client.")
        pass

    def mock_get_fragment(self, query_key, value):
        return { "TotalNrOfResults": 0 }

    from app.services.mediahaven import MediahavenClient

    mocker.patch.object(MediahavenClient, "__init__", mock_init)
    mocker.patch.object(MediahavenClient, "get_fragment", mock_get_fragment)


@pytest.fixture
def mock_ftp(mocker):
    def mock_init(self, config):
        print(f"Initiating FTP Client.")
        pass

    from app.services.ftp import FTPClient

    mocker.patch.object(FTPClient, "__init__", mock_init)
