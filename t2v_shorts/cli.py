from __future__ import annotations

import argparse

from rich import print

from .config import GenerateRequest
from .pipeline import run


def main() -> None:
    ap = argparse.ArgumentParser(prog="t2v-shorts")
    sub = ap.add_subparsers(dest="cmd", required=True)

    g = sub.add_parser("generate")
    g.add_argument("--text", required=True)
    g.add_argument("--seconds", type=int, default=6)
    g.add_argument("--fps", type=int, default=24)
    g.add_argument("--seed", type=int)
    g.add_argument("--backend", default="cogvideox")
    g.add_argument("--width", type=int, default=768)
    g.add_argument("--height", type=int, default=1344)
    g.add_argument("--no-upscale", action="store_true")
    g.add_argument("--out", default="out/out.mp4")
    g.add_argument("--dry-run", action="store_true")

    args = ap.parse_args()

    if args.cmd == "generate":
        req = GenerateRequest(
            text=args.text,
            seconds=args.seconds,
            fps=args.fps,
            seed=args.seed,
            backend=args.backend,
            width=args.width,
            height=args.height,
            upscale_4k=not args.no_upscale,
            out=args.out,
        )
        out = run(req, dry_run=args.dry_run)
        print(f"Wrote: {out}")


if __name__ == "__main__":
    main()
