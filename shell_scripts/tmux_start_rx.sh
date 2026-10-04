#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

usage() {
    cat <<EOF
Usage:
  $0 --port <port> --freq <freq> --sample-rate <rate> [options]

Mandatory:
  --port <port>              TCP Port
  --freq <freq>              Frequency
  --sample-rate <rate>       Sample rate

Optional:
  --addr <addr>              Address
  --sf <sf>                  Spreading factor
  --netid <netid>            Network ID
  --upchirps <upchirps>      Number of preamble upchirps
EOF
    exit 2
}

addr=""
port=""
freq=""
sample_rate=""
sf=""
netid=""
upchirps=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --addr)
            [[ $# -ge 2 ]] || { echo "Error: --addr requires a value" >&2; usage; }
            addr="$2"
            shift 2
            ;;

        --port)
            [[ $# -ge 2 ]] || { echo "Error: --port requires a value" >&2; usage; }
            port="$2"
            shift 2
            ;;

        --freq)
            [[ $# -ge 2 ]] || { echo "Error: --freq requires a value" >&2; usage; }
            freq="$2"
            shift 2
            ;;

        --sample-rate)
            [[ $# -ge 2 ]] || { echo "Error: --sample-rate requires a value" >&2; usage; }
            sample_rate="$2"
            shift 2
            ;;

        --sf)
            [[ $# -ge 2 ]] || { echo "Error: --sf requires a value" >&2; usage; }
            sf="$2"
            shift 2
            ;;

        --netid)
            [[ $# -ge 2 ]] || { echo "Error: --netid requires a value" >&2; usage; }
            netid="$2"
            shift 2
            ;;

        --upchirps)
            [[ $# -ge 2 ]] || { echo "Error: --upchirps requires a value" >&2; usage; }
            upchirps="$2"
            shift 2
            ;;

        --help|-h)
            usage
            ;;

        *)
            echo "Error: unknown argument: $1" >&2
            usage
            ;;
    esac
done

# Check mandatory arguments
[[ -n "$port" ]] ||
    { echo "Error: --port is mandatory" >&2; usage; }

[[ -n "$freq" ]] ||
    { echo "Error: --freq is mandatory" >&2; usage; }

[[ -n "$sample_rate" ]] ||
    { echo "Error: --sample-rate is mandatory" >&2; usage; }

addr="${addr:-127.0.0.1}"           # defaults to 127.0.0.1

# Start rtl_tcp through an Android intent
am start -a android.intent.action.VIEW \
  -d "iqsrc://-a ${addr} -p ${port} -f ${freq} -s ${sample_rate}"

# Construct arguments for start_receiver.sh
args=(
    --port "$port"
    --freq "$freq"
    --sample-rate "$sample_rate"
)

args+=(--addr "$addr")
[[ -n "$sf" ]]       && args+=(--sf "$sf")
[[ -n "$netid" ]]    && args+=(--netid "$netid")
[[ -n "$upchirps" ]] && args+=(--upchirps "$upchirps")

# Launch Ubuntu distro and start receiver 
USERNAME=lorasdr
pd login ubuntu --user ${USERNAME} -- "/home/$USERNAME/lora-sdr-android/shell_scripts/start_receiver.sh" "${args[@]}"
