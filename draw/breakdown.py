#!/usr/bin/env python3
"""Break a reference photo down to pure form: remove specular and texture,
keep the anatomy crisp.

Two grades, the artist's picks:
  default   - the Denisa grade: shine removed, edge-preserving flatten x2,
              thin hair strands and fine dark shapes kept crisp
  --spots   - the freckle grade: adds dark-spot removal below eye scale
              (freckles, moles) before a single flatten pass; costs some
              thin-strand detail, use on spotted skin

Usage: python3 breakdown.py [--spots] input.jpg [output.jpg]

Requires: opencv-python-headless (pip install opencv-python-headless)
"""
import sys
import cv2

def breakdown(img, spots=False):
    out = img.copy()
    # specular: bright thin/small outliers (shine, glints, droplets, jewelry)
    # replaced with the local median, at all scales
    for ksize, thr in [(15, 9), (31, 8), (51, 8)]:
        med = cv2.medianBlur(out, ksize)
        m = cv2.subtract(out, med) > thr
        out[m] = med[m]
    if spots:
        # dark texture (freckles, spots): ONLY below eye scale, so pupils,
        # lids, nostrils and the lip line survive
        for ksize, thr in [(9, 8), (15, 8), (21, 9)]:
            med = cv2.medianBlur(out, ksize)
            m = cv2.subtract(med, out) > thr
            out[m] = med[m]
    # texture: edge-preserving flattening - planes go matte and flat while
    # the form edges stay crisp
    bgr = cv2.cvtColor(out, cv2.COLOR_GRAY2BGR)
    if spots:
        bgr = cv2.edgePreservingFilter(bgr, flags=cv2.RECURS_FILTER,
                                       sigma_s=55, sigma_r=0.18)
    else:
        bgr = cv2.edgePreservingFilter(bgr, flags=cv2.RECURS_FILTER,
                                       sigma_s=60, sigma_r=0.22)
        bgr = cv2.edgePreservingFilter(bgr, flags=cv2.RECURS_FILTER,
                                       sigma_s=40, sigma_r=0.18)
    out = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
    out = cv2.bilateralFilter(out, 13, 26 if not spots else 24, 13)
    return out

if __name__ == '__main__':
    args = [a for a in sys.argv[1:] if a != '--spots']
    spots = '--spots' in sys.argv[1:]
    src = args[0]
    dst = args[1] if len(args) > 1 else src.rsplit('.', 1)[0] + '-form.jpg'
    img = cv2.imread(src, cv2.IMREAD_GRAYSCALE)
    if img is None:
        sys.exit(f'could not read {src}')
    cv2.imwrite(dst, breakdown(img, spots), [cv2.IMWRITE_JPEG_QUALITY, 92])
    print(dst)
