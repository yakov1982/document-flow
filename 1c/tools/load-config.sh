#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_1c_dir="$(cd "${script_dir}/.." && pwd)"

default_src_dir="${repo_1c_dir}/src"
src_dir="${default_src_dir}"

usage() {
  cat >&2 <<'EOF'
Usage:
  load-config.sh [--src DIR] <DESIGNER_CONNECTION_ARGS...> [extra designer keys...]

Examples:
  export V8_DESIGNER="/opt/1cv8/x86_64/8.3.xx.xxxx/1cv8"
  ./1c/tools/load-config.sh --src ./1c/src /F "/path/to/file-ib"
  ./1c/tools/load-config.sh --src ./1c/src /F "/path/to/file-ib" /UpdateDBCfg

Notes:
  - The script writes a log next to itself: load-config.log
  - This is intended for loading the *infobase configuration* from files.
EOF
}

if [[ $# -gt 0 ]]; then
  case "${1}" in
    -s|--src)
      if [[ $# -lt 2 ]]; then
        echo "ERROR: --src requires a value" >&2
        usage
        exit 2
      fi
      src_dir="${2}"
      shift 2
      ;;
    *)
      # allow a simple form: first arg is a src dir, if it doesn't look like a designer switch
      if [[ "${1}" != /* && "${1}" != -* ]]; then
        src_dir="${1}"
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

if [[ ! -d "${src_dir}" ]]; then
  echo "ERROR: source directory does not exist: ${src_dir}" >&2
  exit 2
fi

"${V8_DESIGNER}" DESIGNER "$@" \
  /LoadConfigFromFiles "${src_dir}" \
  /DisableStartupMessages \
  /Out "${script_dir}/load-config.log"

