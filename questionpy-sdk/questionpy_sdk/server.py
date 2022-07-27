import logging
from json.decoder import JSONDecodeError
from typing import Iterator, TextIO

import pydantic
from pydantic.error_wrappers import ValidationError

from questionpy_sdk.messages import Message

log = logging.getLogger(__name__)


class QPyPackageServer(Iterator[Message]):
    def __init__(self, read_stream: TextIO, write_stream: TextIO, *, pretty: bool = False):
        self.read_stream = read_stream
        self.write_stream = write_stream
        self.pretty = pretty

    def __iter__(self) -> Iterator[Message]:
        return self

    def __next__(self) -> Message:
        message = None
        while not message:
            line = self._read_next_line()

            try:
                # Mypy wrongly infers the type of Message to object for some reason, leading to a false positive here.
                message = pydantic.parse_raw_as(Message, line)  # type: ignore[arg-type]
            except (JSONDecodeError, ValidationError) as e:
                log.error("Received invalid message, ignoring", exc_info=e)
                continue

        log.debug("Received: %s", message)
        return message

    def _read_next_line(self) -> str:
        line = None
        while not line or line.isspace():
            line = self.read_stream.readline()

            if len(line) == 0:
                log.debug("Received EOF, stop reading")
                raise StopIteration

        return line

    def send(self, message: Message) -> None:
        self.write_stream.write(message.json(indent=2 if self.pretty else None))
        self.write_stream.write("\n")
        self.write_stream.flush()
        log.debug("Sent: %s", message)
