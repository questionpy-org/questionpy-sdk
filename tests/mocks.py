from io import StringIO
from typing import List

from questionpy import Manifest
from questionpy_sdk.messages import Message
from questionpy_sdk.server import QPyPackageServer


class MockServer(QPyPackageServer):
    def __init__(self, queue: List[Message]):
        super().__init__(StringIO(), StringIO())
        self.queue: List[Message] = queue
        self.sent: List[Message] = []

    def __next__(self) -> Message:
        try:
            return self.queue.pop()
        except IndexError as e:
            raise StopIteration from e

    def send(self, message: Message) -> None:
        self.sent.append(message)


A_MANIFEST = Manifest(short_name="test", version="0.1.0", api_version="0.1", author="Alice Sample <alice@example.org>")
