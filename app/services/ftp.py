# System imports
from io import BytesIO
from ftplib import FTP as BuiltinFTP
from urllib.parse import urlparse

# Third-party imports
from viaa.configuration import ConfigParser
from viaa.observability import logging

# Constants
BASE_DOMAIN = "viaa.be"


class FTPClient(object):
    """Abstraction for FTP"""

    def __init__(self, configParser: ConfigParser = None):
        self.log = logging.get_logger(__name__, config=configParser)
        self.cfg: dict = configParser.app_cfg
        self.host = self.__set_host()
        self.conn = self.__connect()

    def __set_host(self):
        """"""
        host = self.cfg["ftp"]["host"]
        parts = urlparse(host)
        self.log.debug(f"FTP: scheme={parts.scheme}, host={parts.netloc}")
        return parts.netloc

    def __connect(self):
        config = self.cfg
        ftp_user = config["ftp"]["user"]
        ftp_password = config["ftp"]["password"]

        try:
            conn = BuiltinFTP(host=self.host, user=ftp_user, passwd=ftp_password)
        except Exception as e:
            self.log.error(e)
            raise
        else:
            self.log.debug(f"Succesfully established connection to {self.host}")
            return conn

    def put(self, file, destination_path, destination_filename):
        self.log.debug(
            f"Putting {destination_filename} to {destination_path} on {self.host}"
        )
        with self.__connect() as conn:
            try:
                conn.cwd(destination_path)
                stor_cmd = f"STOR {destination_filename}"
                conn.storbinary(stor_cmd, BytesIO(file))
            except Exception as exception:
                self.log.critical(
                    f"Failed to put file on {self.host} {destination_path}",
                    exception=exception,
                )
                pass
