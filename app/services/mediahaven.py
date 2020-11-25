#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from lxml import etree

import functools
from io import BytesIO

import requests
from requests.auth import HTTPBasicAuth
from requests.exceptions import RequestException

from viaa.configuration import ConfigParser
from viaa.observability import logging


class AuthenticationException(Exception):
    """Exception raised when authentication fails."""

    pass


class MediahavenClient:
    def __init__(self, configParser: ConfigParser = None):
        self.log = logging.get_logger(__name__, config=configParser)
        self.cfg: dict = configParser.app_cfg
        self.token_info = None
        self.url = f'{self.cfg["mediahaven"]["host"]}/media/'

    def __authenticate(function):
        @functools.wraps(function)
        def wrapper_authenticate(self, *args, **kwargs):
            if not self.token_info:
                self.token_info = self.__get_token()
            try:
                return function(self, *args, **kwargs)
            except AuthenticationException:
                self.token_info = self.__get_token()
            return function(self, *args, **kwargs)

        return wrapper_authenticate

    def __get_token(self) -> str:
        """Gets an OAuth token that can be used in mediahaven requests to authenticate."""
        user: str = self.cfg["mediahaven"]["username"]
        password: str = self.cfg["mediahaven"]["password"]
        url: str = self.cfg["mediahaven"]["host"] + "/oauth/access_token"
        payload = {"grant_type": "password"}

        try:
            r = requests.post(
                url,
                auth=HTTPBasicAuth(user.encode("utf-8"), password.encode("utf-8")),
                data=payload,
            )

            if r.status_code != 201:
                raise RequestException(
                    f"Failed to get a token. Status: {r.status_code}"
                )
            token_info = r.json()
        except RequestException as e:
            raise e
        return token_info

    def _construct_headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self.token_info['access_token']}",
            "Accept": "application/vnd.mediahaven.v2+json",
        }

    @__authenticate
    def get_fragment(self, query_key: str, value: str) -> dict:
        headers = self._construct_headers()

        # Query is constructed as a string to prevent requests url encoding,
        # Mediahaven returns wrong result when encoded
        query = f"?q=%2b({query_key}:{value})"

        # Send the GET request
        response = requests.get(f"{self.url}{query}", headers=headers,)

        if response.status_code == 401:
            # AuthenticationException triggers a retry with a new token
            raise AuthenticationException(response.text)

        # If there is an HTTP error, raise it
        response.raise_for_status()

        return response.json()

    @__authenticate
    def update_metadata(self, fragment_id: str, sidecar: str) -> dict:
        headers = self._construct_headers()

        # Construct the URL to POST to
        url = f"{self.url}/{fragment_id}"

        data = {"metadata": sidecar, "reason": "metadataUpdated"}

        # Send the POST request, as multipart/form-data
        response = requests.post(url, headers=headers, files=data)

        if response.status_code == 401:
            # AuthenticationException triggers a retry with a new token
            raise AuthenticationException(response.text)

        # If there is an HTTP error, raise it
        response.raise_for_status()

        return True

    @__authenticate
    def delete_fragment(self, fragment_id: str) -> bool:
        headers = self._construct_headers()

        # Construct the URL to POST to
        url = f"{self.url}/{fragment_id}"

        # Set a reason for the DELETE
        data = {"reason": "New metadata available."}

        # Send the DELETE request, as multipart/form-data
        response = requests.delete(url, headers=headers, files=data)

        if response.status_code == 401:
            # AuthenticationException triggers a retry with a new token
            raise AuthenticationException(response.text)

        # If there is an HTTP error, raise it
        response.raise_for_status()

        return response.status_code == 204

    @__authenticate
    def upload_file(
        self, file: bytes, pid: str, external_id: str, department_id: str
    ) -> None:
        headers = self._construct_headers()

        payload = {
            "title": f"Collateral: metadata for pid: {pid}",
            "externalId": external_id,
            "autoPublish": True,
            "departmentId": department_id,
        }

        # file needs a name ending in .xml or mediahaven will think it's an image.
        named_file = BytesIO(file)
        named_file.name = f"{pid}.xml"

        files = [("file", named_file)]

        # Send the POST request, as multipart/form-data
        response = requests.post(self.url, headers=headers, data=payload, files=files)
