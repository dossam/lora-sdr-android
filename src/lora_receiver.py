import argparse
import threading

import numpy as np
from iq_receiver import IQReceiver
from pylorasdr import CircBuffer, Receiver


BUFFER_SIZE=2**18

# Received frame handler
def print_payload(frame_info:dict):
    if frame_info['uplink']:
        up_str = "--------- Uplink frame ---------"
    else:
        up_str = "-------- Downlink frame --------"


    out_str = f"{up_str}\n" + \
            f"CR: {frame_info['cr']}\n" + \
            f"SNR: {format(10*np.log10(frame_info['snr']), '.2f')} dB\n" + \
            f"Payload: \"{bytes(frame_info['payload']).decode('utf-8')}\"\n"+ \
            f"{len(up_str)*"-"}"
    print(out_str)

def main():
    parser = argparse.ArgumentParser(
        description="RTL-TCP IQ receiver with background acquisition"
    )

    parser.add_argument(
        "--addr",
        required=False,
        default="127.0.0.1",
        help="IP address",
    )

    parser.add_argument(
        "--port",
        type=int,
        required=True,
        help="TCP port",
    )

    parser.add_argument(
        "--freq",
        type=int,
        required=True,
        help="Center frequency in Hz",
    )

    parser.add_argument(
        "--sample-rate",
        type=int,
        required=True,
        help="Sample rate",
    )

    parser.add_argument(
        "--sf",
        type=int,
        required=False,
        default=7,
        help="Spreading factor",
    )

    parser.add_argument(
        "--netid",
        type=int,
        required=False,
        default=0x12,
        help="Network ID expected",
    )

    parser.add_argument(
        "--upchirps",
        type=int,
        required=False,
        default=8,
        help="Number of preamble upchirps",
    )

    args = parser.parse_args()

    # Shared shutdown signal.
    stop_event = threading.Event()

    # Samples buffer.
    iq_buffer = CircBuffer(BUFFER_SIZE)

    receiver = IQReceiver(
        ip=args.addr,
        port=args.port,
        frequency=args.freq,
        sample_rate=args.sample_rate,
        iq_buffer=iq_buffer,
        stop_event=stop_event,
    )

    try:
        # Start the acquisition thread.
        receiver.start()
        
        center_freq = args.freq
        bw = args.sample_rate/2      # LoRa Rx is used with x2 oversampling
        sf = args.sf
        netid = args.netid                    # netID
        n_up = args.upchirps
        soft_decoding = True

        lora_rx = Receiver(center_freq, bw, sf, 2, netid, n_up, soft_decoding)
        lora_rx.register_frame_handler(print_payload)
        lora_rx.attach_buffer(iq_buffer)
        
        print("Starting LoRa Rx ...")
        lora_rx.start()

    except KeyboardInterrupt:
        print("\nCtrl-C received.")

        stop_event.set()

    finally:
        # Stop the acquisition thread and close the TCP connection.
        receiver.stop()
        receiver.join(timeout=2.0)

        if receiver.is_alive():
            print("Warning: receiver thread did not stop immediately.")

        print("Program terminated.")

if __name__ == "__main__":
    main()