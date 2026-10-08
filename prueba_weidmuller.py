#!/usr/bin/env python3
"""Lee un transmisor 4-20 mA convertido a 0-10 V en un PLC 19R V6.

La utilidad es de solo lectura: no acciona reles, motores ni salidas.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path


ADC_MAX = 4095
VOLTAGE_MAX = 10.0
CURRENT_MIN_MA = 4.0
CURRENT_MAX_MA = 20.0
DEFAULT_DRIVER = str(
    Path.home() / "test" / "RPIPLC_V6" / "RPIPLC_19R" / "get-analog-input"
)


@dataclass(frozen=True)
class Measurement:
    raw: int
    voltage_v: float
    current_equivalent_ma: float
    percent: float
    engineering_value: float
    status: str


def read_raw(driver: str, channel: str) -> int:
    result = subprocess.run(
        [driver, channel],
        capture_output=True,
        text=True,
        timeout=3,
        check=False,
    )
    value = result.stdout.strip()
    if result.returncode != 0 or not value.isdigit():
        detail = result.stderr.strip() or value or f"codigo {result.returncode}"
        raise RuntimeError(f"no se pudo leer {channel}: {detail}")
    return int(value)


def convert(raw: int, engineering_min: float, engineering_max: float) -> Measurement:
    voltage = raw * VOLTAGE_MAX / ADC_MAX
    fraction = voltage / VOLTAGE_MAX
    percent = fraction * 100.0
    current = CURRENT_MIN_MA + fraction * (CURRENT_MAX_MA - CURRENT_MIN_MA)
    engineering = engineering_min + fraction * (engineering_max - engineering_min)

    if raw < 0 or raw > ADC_MAX:
        status = "ADC_FUERA_DE_RANGO"
    elif voltage < -0.05 or voltage > 10.05:
        status = "TENSION_FUERA_DE_RANGO"
    elif voltage <= 0.05:
        # Con una conversion 4-20 mA -> 0-10 V, el cero de escala y un
        # lazo abierto pueden producir casi la misma lectura.
        status = "CERO_ESCALA_O_LAZO_ABIERTO"
    else:
        status = "OK"

    return Measurement(
        raw=raw,
        voltage_v=round(voltage, 4),
        current_equivalent_ma=round(current, 4),
        percent=round(percent, 3),
        engineering_value=round(engineering, 4),
        status=status,
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Lee el ACT20M configurado 4-20 mA -> 0-10 V."
    )
    parser.add_argument(
        "--channel",
        default="I0.5",
        choices=("I0.2", "I0.3", "I0.4", "I0.5"),
    )
    parser.add_argument("--min", dest="engineering_min", type=float, default=0.0)
    parser.add_argument("--max", dest="engineering_max", type=float, default=100.0)
    parser.add_argument("--unit", default="%")
    parser.add_argument("--interval", type=float, default=1.0)
    parser.add_argument(
        "--samples",
        type=int,
        default=0,
        help="Cantidad de lecturas; 0 mantiene el monitoreo continuo.",
    )
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--driver", default=DEFAULT_DRIVER)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.engineering_max <= args.engineering_min:
        print("Error: --max debe ser mayor que --min", file=sys.stderr)
        return 2
    if args.interval <= 0:
        print("Error: --interval debe ser mayor que cero", file=sys.stderr)
        return 2
    if args.samples < 0:
        print("Error: --samples no puede ser negativo", file=sys.stderr)
        return 2

    try:
        sample_count = 0
        while True:
            raw = read_raw(args.driver, args.channel)
            measurement = convert(raw, args.engineering_min, args.engineering_max)

            if args.json:
                payload = asdict(measurement)
                payload["channel"] = args.channel
                payload["unit"] = args.unit
                print(json.dumps(payload, ensure_ascii=False), flush=True)
            else:
                print(
                    f"{args.channel} | raw={measurement.raw:4d} | "
                    f"{measurement.voltage_v:6.3f} V | "
                    f"equiv={measurement.current_equivalent_ma:6.3f} mA | "
                    f"{measurement.percent:6.2f} % | "
                    f"valor={measurement.engineering_value:9.4f} {args.unit} | "
                    f"{measurement.status}",
                    flush=True,
                )

            sample_count += 1
            if args.once or (args.samples and sample_count >= args.samples):
                return 0
            time.sleep(args.interval)
    except KeyboardInterrupt:
        return 0
    except (OSError, RuntimeError, subprocess.TimeoutExpired) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
