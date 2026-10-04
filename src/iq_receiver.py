from rtl_tcp_client import RtlTcpClient
import threading
import numpy as np

class IQReceiver(threading.Thread):
    """
    Thread for IQ samples acquisition.
    Connects to rtl_tcp server, receives and write samples to target buffer.

    Notes: frequency and sample_rate are currently not used. 
    The server is expected to be started with the right parameters already.
    """

    def __init__(
        self,
        ip,
        port,
        frequency,
        sample_rate,
        iq_buffer,
        stop_event,
        chunk_size=16384,
    ):
        super().__init__(name="IQReceiver", daemon=True)

        self.ip = ip
        self.port = port
        self.frequency = frequency
        self.sample_rate = sample_rate
        self.iq_buffer = iq_buffer
        self.stop_event = stop_event
        self.chunk_size = chunk_size

        self.sdr = None
        self.error = None

    def run(self):
        try:
            print(f"Connecting to {self.ip}:{self.port}...")

            self.sdr = RtlTcpClient(
                host=self.ip,
                port=self.port,
            )

            self.sdr.center_freq = self.frequency
            self.sdr.sample_rate = self.sample_rate

            self.sdr.connect()

            print("RTL-TCP connected.")
            print(f"Center frequency: {self.frequency/10**6} MHz")
            print(f"Sample rate:      {self.sample_rate/10**3} kHz")

            while not self.stop_event.is_set():
                samples = self.sdr.read_samples(self.chunk_size)

                if samples is None or len(samples) == 0:
                    continue

                samples = samples.astype(
                    np.complex64,
                    copy=False,
                )

                self.iq_buffer.write(samples)

        except Exception as exc:
            # Don't report an error if intentional stop event
            if not self.stop_event.is_set():
                self.error = exc
                print(f"IQ receiver error: {exc}")

                # -- inform the main thread of process stop.
                self.stop_event.set()

        finally:
            self._close()

            print("IQ receiver stopped.")

    def _close(self):
        if self.sdr is not None:
            try:
                self.sdr.close()
            except Exception:
                pass

            self.sdr = None

    def stop(self):
        self.stop_event.set()
        self._close()