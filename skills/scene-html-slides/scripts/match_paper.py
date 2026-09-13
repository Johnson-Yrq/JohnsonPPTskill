#!/usr/bin/env python3
"""Flatten a generated scene image's background onto the paper colour so the frame edge disappears.

Generated renders carry a gentle lighting gradient (corners a few levels apart). On the flat paper
that gradient shows up as a faint rectangle around every picture. This fits a smooth surface to the
background, subtracts it and re-centres on the paper colour; the subject shifts by the same few
levels locally, which is invisible, while shadows keep their depth.

Usage: python3 match_paper.py images/01.png images/02.png [--paper #F7F6F2] [--tolerance 8] [--dry-run]
Originals are copied to images/original/ before the file is rewritten (PNG output).
"""
import argparse
import shutil
from pathlib import Path


def parse_color(value):
    value = value.lstrip('#')
    if len(value) != 6:
        raise ValueError('纸色须为 #RRGGBB')
    return tuple(int(value[i:i + 2], 16) for i in (0, 2, 4))


def edge_stats(arr, band=12):
    import numpy as np
    edge = np.concatenate([arr[:band].reshape(-1, 3), arr[-band:].reshape(-1, 3), arr[:, :band].reshape(-1, 3), arr[:, -band:].reshape(-1, 3)])
    corners = [arr[y, x] for y, x in [(4, 4), (4, arr.shape[1] - 5), (arr.shape[0] - 5, 4), (arr.shape[0] - 5, arr.shape[1] - 5)]]
    return np.median(edge, axis=0), np.ptp(np.array(corners), axis=0).max()


def flatten(arr, paper, tolerance):
    """Return corrected array and a description. Background = pixels near the edge median, cleaned by an opening."""
    import numpy as np
    from PIL import Image, ImageFilter
    h, w, _ = arr.shape
    median, _ = edge_stats(arr)
    dist = np.abs(arr - median).max(axis=2)
    mask = (dist <= tolerance).astype(np.uint8) * 255
    # Morphological opening: drop candidate blobs thinner than ~40px (white desk tops, papers) so only open background is fitted.
    m = Image.fromarray(mask).filter(ImageFilter.MinFilter(21)).filter(ImageFilter.MaxFilter(21))
    core = np.asarray(m) > 0
    if core.mean() < 0.05:
        return None, '背景区域太小，未处理'
    ys, xs = np.nonzero(core)
    # Sub-sample for the fit; a quadratic surface per channel captures vignette-style lighting.
    step = max(1, len(ys) // 20000)
    ys, xs = ys[::step], xs[::step]
    yn, xn = ys / h - .5, xs / w - .5
    basis = np.stack([np.ones_like(yn), xn, yn, xn * xn, yn * yn, xn * yn], axis=1)
    yy, xx = (np.arange(h) / h - .5)[:, None], (np.arange(w) / w - .5)[None, :]
    full = np.stack([np.ones((h, w)), np.broadcast_to(xx, (h, w)), np.broadcast_to(yy, (h, w)), np.broadcast_to(xx * xx, (h, w)), np.broadcast_to(yy * yy, (h, w)), xx * yy], axis=2)
    out = arr.astype(np.float64).copy()
    for c in range(3):
        coef, *_ = np.linalg.lstsq(basis, arr[ys, xs, c].astype(np.float64), rcond=None)
        surface = full @ coef
        out[..., c] += paper[c] - surface
    return np.clip(out + .5, 0, 255).astype(np.uint8), f'背景占比 {core.mean():.0%}'


def process(path, paper, tolerance, dry_run):
    import numpy as np
    from PIL import Image
    image = Image.open(path)
    alpha = image.getchannel('A') if image.mode in ('RGBA', 'LA') else None
    arr = np.asarray(image.convert('RGB')).astype(np.int16)
    before_median, before_ptp = edge_stats(arr)
    result, note = flatten(arr, paper, tolerance)
    if result is None:
        return {'file': path.name, 'skipped': note}
    after_median, after_ptp = edge_stats(result.astype(np.int16))
    report = {'file': path.name, 'note': note,
              'before': {'edge_median': [int(v) for v in before_median], 'corner_spread': int(before_ptp)},
              'after': {'edge_median': [int(v) for v in after_median], 'corner_spread': int(after_ptp)}}
    if not dry_run:
        backup = path.parent / 'original' / path.name
        backup.parent.mkdir(exist_ok=True)
        if not backup.exists():
            shutil.copy2(path, backup)
        out = Image.fromarray(result)
        if alpha is not None:
            out.putalpha(alpha)
        target = path if path.suffix.lower() == '.png' else path.with_suffix('.png')
        out.save(target, 'PNG', optimize=True)
        report['written'] = target.name
    return report


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('images', nargs='+')
    p.add_argument('--paper', default='#F7F6F2')
    p.add_argument('--tolerance', type=int, default=8, help='与边缘中值相差不超过此值的像素视为背景（默认 8）')
    p.add_argument('--dry-run', action='store_true', help='只报告，不写文件')
    args = p.parse_args()
    try:
        import numpy  # noqa: F401
        from PIL import Image  # noqa: F401
    except ImportError:
        p.exit(1, '需要 Pillow 和 numpy；没有时改用 image.edge_fade 轻微淡出边缘，或在生图工具里重生成纯色背景\n')
    paper = parse_color(args.paper)
    import json
    for name in args.images:
        path = Path(name)
        if not path.is_file():
            p.exit(1, f'找不到图片：{name}\n')
        print(json.dumps(process(path, paper, args.tolerance, args.dry_run), ensure_ascii=False))


if __name__ == '__main__':
    main()
