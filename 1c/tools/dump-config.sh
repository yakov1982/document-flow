#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_1c_dir="$(cd "${script_dir}/.." && pwd)"

default_out_dir="${repo_1c_dir}/src"
out_dir="${default_out_dir}"

usage() {
  cat >&2 <<'EOF'
Usage:
  dump-config.sh [--out DIR] <DESIGNER_CONNECTION_ARGS...>

Examples:
  export V8_DESIGNER="/opt/1cv8/x86_64/8.3.xx.xxxx/1cv8"
  ./1c/tools/dump-config.sh --out ./1c/src /F "/path/to/file-ib"
  ./1c/tools/dump-config.sh --out ./1c/src /S "server\base" /N user /P pass

Notes:
  - The script writes a log next to itself: dump-config.log
  - This is intended for dumping the *infobase configuration* to files.
EOF
}

if [[ $# -gt 0 ]]; then
  case "${1}" in
    -o|--out)
      if [[ $# -lt 2 ]]; then
        echo "ERROR: --out requires a value" >&2
        usage
        exit 2
      fi
      out_dir="${2}"
      shift 2
      ;;
    *)
      # allow a simple form: first arg is an out dir, if it doesn't look like a designer switch
      if [[ "${1}" != /* && "${1}" != -* ]]; then
        out_dir="${1}"
        shift
      fi
      ;;
  esac
fi

if [[ -z "${V8_DESIGNER:-}" ]]; then
  echo "ERROR: V8_DESIGNER is not set (path to 1cv8 executable)" >&2
  usage
  exit 2
fi

if [[ $# -eq 0 ]]; then
  echo "ERROR: missing DESIGNER connection arguments (/F ... or /S ...)" >&2
  usage
  exit 2
fi

mkdir -p "${out_dir}"

"${V8_DESIGNER}" DESIGNER "$@" \
  /DumpConfigToFiles "${out_dir}" \
  /DisableStartupMessages \
  /Out "${script_dir}/dump-config.log"

