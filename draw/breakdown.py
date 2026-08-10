#!/usr/bin/env python3
"""Break a reference photo down to pure form: remove specular and texture,
keep the anatomy crisp. The 'crisper' grade the artist standardized on.

Usage: python3 breakdown.py input.jpg [output.jpg]

Requires: opencv-python-headless (pip install opencv-python-headless)
"""
import sys
import cv2

def breakdown(img):
    out = img.copy()
    # specular: bright thin/small outliers (shine, glints, droplets, jewelry)
    # replaced with the local median, at all scales
    for ksize, thr in [(15, 9), (31, 8), (51, 8)]:
        med = cv2.medianBlur(out, ksize)
        m = cv2.subtract(out, med) > thr
        out[m] = med[m]
    # dark texture (freckles, spots): ONLY below eye scale, so pupils, lids,
    # nostrils and the lip line survive
    for ksize, thr in [(9, 8), (15, 8), (21, 9)]:
        med = cv2.medianBlur(out, ksize)
        m = cv2.subtract(med, out) > thr
        out[m] = med[m]
    # texture: one edge-preserving flattening pass - planes go matte and
    # flat while the form edges stay crisp
    bgr = cv2.cvtColor(out, cv2.COLOR_GRAY2BGR)
    bgr = cv2.edgePreservingFilter(bgr, flags=cv2.RECURS_FILTER,
                                   sigma_s=55, sigma_r=0.18)
    out = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
    out = cv2.bilateralFilter(out, 13, 24, 13)
    return out

if __name__ == '__main__':
    src = sys.argv[1]
    dst = sys.argv[2] if len(sys.argv) > 2 else src.rsplit('.', 1)[0] + '-form.jpg'
    img = cv2.imread(src, cv2.IMREAD_GRAYSCALE)
    if img is None:
        sys.exit(f'could not read {src}')
    cv2.imwrite(dst, breakdown(img), [cv2.IMWRITE_JPEG_QUALITY, 92])
    print(dst)
