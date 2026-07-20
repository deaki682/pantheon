#!/usr/bin/env python3
"""Extract the essential outline of a photo as a clean line drawing.

Designed for portraits and other photos with lots of fine texture
(freckles, skin, fabric): texture is smoothed away with an
edge-preserving filter before edge extraction, and tiny speckle
fragments are removed afterward, so only the structural lines remain.

Usage:
    python3 outline.py photo.jpg
    python3 outline.py photo.jpg -o outline.png --detail 0.3
    python3 outline.py photo.jpg --method sketch --svg

Output is black lines on a white background (use --invert to flip).
Requires: pip install opencv-python-headless numpy
"""

import argparse
import sys
from pathlib import Path

import cv2
import numpy as np


def load_gray(path: str, max_dim: int) -> np.ndarray:
    img = cv2.imread(path, cv2.IMREAD_COLOR)
    if img is None:
        sys.exit(f"error: could not read image: {path}")
    h, w = img.shape[:2]
    if max(h, w) > max_dim:
        scale = max_dim / max(h, w)
        img = cv2.resize(img, (round(w * scale), round(h * scale)),
                         interpolation=cv2.INTER_AREA)
    return cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)


def smooth_texture(gray: np.ndarray, detail: float) -> np.ndarray:
    """Kill fine texture (freckles, grain) while keeping structural edges.

    detail=0 -> heavy smoothing, only the boldest lines survive
    detail=1 -> light smoothing, fine features kept
    """
    # Repeated bilateral filtering flattens texture without blurring
    # across strong edges. Fewer/weaker passes at high detail.
    passes = max(1, round(3 - 2 * detail))
    sigma_color = 40 + 40 * (1 - detail)
    out = gray
    for _ in range(passes):
        out = cv2.bilateralFilter(out, d=9, sigmaColor=sigma_color, sigmaSpace=7)
    return out


def edges_contour(gray: np.ndarray, detail: float) -> np.ndarray:
    """Thin structural edges via Canny with gradient-percentile thresholds.

    Thresholding on the gradient-magnitude distribution (instead of image
    brightness) keeps the result stable across lighting conditions.
    Returns a binary mask (255 = line).
    """
    gx = cv2.Scharr(gray, cv2.CV_32F, 1, 0)
    gy = cv2.Scharr(gray, cv2.CV_32F, 0, 1)
    mag = cv2.magnitude(gx, gy)
    strong = mag[mag > 1.0]
    if strong.size == 0:
        return np.zeros_like(gray)
    # Lower percentile at high detail -> more edges accepted.
    hi = float(np.percentile(strong, 97 - 12 * detail))
    lo = 0.4 * hi
    edges = cv2.Canny(gx.astype(np.int16), gy.astype(np.int16), lo, hi,
                      L2gradient=True)
    # Bridge one-pixel gaps so outlines read as continuous strokes.
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    return cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel)


def edges_sketch(gray: np.ndarray, detail: float) -> np.ndarray:
    """XDoG ink-sketch look: outlines plus filled dark regions.

    Returns a binary mask (255 = ink).
    """
    g = gray.astype(np.float32) / 255.0
    sigma = 0.8 + 1.2 * (1 - detail)
    g1 = cv2.GaussianBlur(g, (0, 0), sigma)
    g2 = cv2.GaussianBlur(g, (0, 0), sigma * 1.6)
    tau = 0.98  # Winnemoller 2011 XDoG: S = G_sigma - tau * G_ksigma
    s = g1 - tau * g2
    eps = 0.02 * float(np.mean(g))  # ink threshold tracks overall exposure
    e = np.where(s >= eps, 1.0, 1.0 + np.tanh(200.0 * (s - eps)))
    return (e < 0.5).astype(np.uint8) * 255


def remove_speckles(mask: np.ndarray, detail: float) -> np.ndarray:
    """Drop connected components too small to be an essential line."""
    h, w = mask.shape
    # Minimum component size scales with image area; stricter at low detail.
    min_size = int((h * w) * (0.00002 + 0.00013 * (1 - detail)))
    n, labels, stats, _ = cv2.connectedComponentsWithStats(mask, connectivity=8)
    out = np.zeros_like(mask)
    for i in range(1, n):
        if stats[i, cv2.CC_STAT_AREA] >= min_size:
            out[labels == i] = 255
    return out


def write_svg(mask: np.ndarray, path: Path, line_width: float = 1.5) -> None:
    """Trace the line mask into an SVG of simplified polyline paths."""
    h, w = mask.shape
    contours, _ = cv2.findContours(mask, cv2.RETR_LIST, cv2.CHAIN_APPROX_TC89_L1)
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}">',
             f'<g fill="none" stroke="black" stroke-width="{line_width}" '
             'stroke-linecap="round" stroke-linejoin="round">']
    for c in contours:
        c = cv2.approxPolyDP(c, epsilon=1.2, closed=False)
        if len(c) < 2:
            continue
        pts = c.reshape(-1, 2)
        d = f"M{pts[0][0]},{pts[0][1]}" + "".join(f" L{x},{y}" for x, y in pts[1:])
        parts.append(f'<path d="{d}"/>')
    parts.append("</g></svg>")
    path.write_text("\n".join(parts))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("input", help="path to the source photo")
    ap.add_argument("-o", "--output",
                    help="output PNG path (default: <input>_outline.png)")
    ap.add_argument("--method", choices=("contour", "sketch"), default="contour",
                    help="contour: thin essential lines (default); "
                         "sketch: XDoG ink look with filled shadows")
    ap.add_argument("--detail", type=float, default=0.5, metavar="0..1",
                    help="0 = only the boldest essential lines, "
                         "1 = keep fine detail (default 0.5)")
    ap.add_argument("--max-dim", type=int, default=2000,
                    help="downscale so the longest side is at most this "
                         "(default 2000; full-res texture only adds noise)")
    ap.add_argument("--invert", action="store_true",
                    help="white lines on black instead of black on white")
    ap.add_argument("--svg", action="store_true",
                    help="also write a traced SVG next to the PNG")
    args = ap.parse_args()

    detail = min(1.0, max(0.0, args.detail))
    out_path = Path(args.output) if args.output else \
        Path(args.input).with_name(Path(args.input).stem + "_outline.png")

    gray = load_gray(args.input, args.max_dim)
    smoothed = smooth_texture(gray, detail)
    extract = edges_contour if args.method == "contour" else edges_sketch
    mask = remove_speckles(extract(smoothed, detail), detail)

    result = mask if args.invert else cv2.bitwise_not(mask)
    cv2.imwrite(str(out_path), result)
    print(f"wrote {out_path}")

    if args.svg:
        svg_path = out_path.with_suffix(".svg")
        write_svg(mask, svg_path)
        print(f"wrote {svg_path}")


if __name__ == "__main__":
    main()
