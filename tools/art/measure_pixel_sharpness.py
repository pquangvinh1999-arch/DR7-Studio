#!/usr/bin/env python3
"""Measure native gameplay-frame sharpness; never infer anatomical acceptance."""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage

def measure(path):
    image=Image.open(path).convert('RGBA');a=np.array(image)
    mask=a[:,:,3]>0
    if not mask.any(): raise ValueError('Frame has no visible pixels')
    # Ignore hidden RGB; compare images using the same transparent-black convention.
    rgb=a[:,:,:3].copy();rgb[~mask]=0
    gray=rgb.astype(float)@np.array([.2126,.7152,.0722])
    boundary=mask&~ndimage.binary_erosion(mask)
    sobel=np.hypot(ndimage.sobel(gray,axis=0),ndimage.sobel(gray,axis=1))
    b=image.getbbox();runs=[]
    for row in a:
        start=0
        while start<len(row):
            if row[start,3]==0: start+=1;continue
            end=start+1
            while end<len(row) and np.array_equal(row[end],row[start]):end+=1
            runs.append(end-start);start=end
    return {'file':str(path),'file_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
        'canvas_size_px':list(image.size),
        'body_bbox_px':[b[0],b[1],b[2]-b[0],b[3]-b[1]],
        'visible_pixels':int(mask.sum()),'rgb_colors':int(len(np.unique(rgb[mask],axis=0))),
        'edge_acutance_sobel':round(float(sobel[boundary].mean()),3),
        'alpha_hardness_pct':100*float(np.isin(a[:,:,3],[0,255]).mean()),
        'visible_alpha_hardness_pct':100*float((a[:,:,3][mask]==255).mean()),
        'minimum_horizontal_constant_rgba_run_px':min(runs),
        'single_pixel_run_fraction':sum(r==1 for r in runs)/len(runs),
        'method':'BT709 gray; transparent RGB zeroed; scipy Sobel unnormalized/default reflect; inner binary alpha boundary; binary erosion default connectivity1',
        'limits':'No automatic visual/anatomy/animation verdict; run lengths do not alone measure perceived sharpness or prove a texel grid.'}

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('frame',type=Path)
    args=parser.parse_args()
    print(json.dumps(measure(args.frame),ensure_ascii=False,indent=2))
