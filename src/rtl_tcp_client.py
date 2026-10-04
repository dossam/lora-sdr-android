import socket
import struct

import numpy as np


class RtlTcpClient:
    """
    Minimal client for the standard rtl_tcp protocol.

    rtl_tcp sends:
        12-byte header:
            4 bytes: "RTL0"
            4 bytes: tuner type
            4 bytes: tuner gain count

        followed by:
            unsigned 8-bit interleaved IQ samples

    This class converts the incoming samples to np.complex64.
    """

    # RTL-TCP command IDs
    CMD_SET_FREQUENCY = 0x01
    CMD_SET_SAMPLE_RATE = 0x02

    HEADER_SIZE = 12
    IQ_BYTES_PER_SAMPLE = 2

    def __init__(self, host, port, timeout=10.0):
        self.host = host
        self.port = port
        self.timeout = timeout

        self.sock = None

        # A TCP read can end anywhere in the byte stream.
        # Keep incomplete data here for the next read.
        self._rx_buffer = bytearray()

        self.tuner_type = None
        self.tuner_gain_count = None

    def connect(self):
        """Connect to the rtl_tcp server and read its header."""

        self.sock = socket.create_connection(
            (self.host, self.port),
            timeout=self.timeout,
        )

        # Header is exactly 12 bytes.
        header = self._recv_exact(self.HEADER_SIZE)

        magic = header[0:4]

        if magic != b"RTL0":
            self.close()
            raise RuntimeError(
                f"Invalid rtl_tcp header: {magic!r}"
            )

        self.tuner_type, self.tuner_gain_count = struct.unpack(
            ">II",
            header[4:12],
        )

    def _recv_exact(self, size):
        """
        Receive exactly `size` bytes.

        TCP does not preserve packet boundaries, so recv(size)
        is not guaranteed to return size bytes.
        """

        data = bytearray()

        while len(data) < size:
            chunk = self.sock.recv(size - len(data))

            if not chunk:
                raise ConnectionError(
                    "rtl_tcp server closed the connection"
                )

            data.extend(chunk)

        return bytes(data)

    def _send_command(self, command, parameter):
        """
        Send an rtl_tcp command.

        Wire format:

            1 byte   command
            4 bytes  big-endian unsigned parameter
        """

        packet = struct.pack(
            ">BI",
            command,
            parameter,
        )

        self.sock.sendall(packet)

    def set_frequency(self, frequency):
        """Set center frequency in Hz."""

        self._send_command(
            self.CMD_SET_FREQUENCY,
            int(frequency),
        )

    def set_sample_rate(self, sample_rate):
        """Set RTL-SDR sample rate in samples/second."""

        self._send_command(
            self.CMD_SET_SAMPLE_RATE,
            int(sample_rate),
        )

    def read_bytes(self, size=16384):
        """
        Read raw IQ bytes.

        The returned length is always even, so that it contains
        complete I/Q pairs.
        """

        while len(self._rx_buffer) < size:
            chunk = self.sock.recv(size)

            if not chunk:
                raise ConnectionError(
                    "rtl_tcp server closed the connection"
                )

            self._rx_buffer.extend(chunk)

        # IQ consists of two bytes per complex sample.
        size -= size % 2

        data = bytes(self._rx_buffer[:size])
        del self._rx_buffer[:size]

        return data

    def read_samples(self, count=16384):
        """
        Read `count` complex IQ samples.

        Returns
        -------
        numpy.ndarray
            np.complex64 array of shape (count,).

        The conversion is:

            I = (raw_I - 127.5) / 127.5
            Q = (raw_Q - 127.5) / 127.5

        resulting approximately in the range [-1, +1].
        """

        raw = self.read_bytes(count * self.IQ_BYTES_PER_SAMPLE)
        samples = np.frombuffer(raw, dtype=np.uint8)
        
        iq = samples.astype(np.float32)
        iq -= 127.5
        iq /= 127.5

        return (iq[0::2] + 1j * iq[1::2]).astype(np.complex64)

    def close(self):
        """Close the TCP connection."""

        if self.sock is not None:
            try:
                self.sock.shutdown(socket.SHUT_RDWR)
            except (OSError, AttributeError):
                pass

            try:
                self.sock.close()
            except OSError:
                pass

            self.sock = None

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()