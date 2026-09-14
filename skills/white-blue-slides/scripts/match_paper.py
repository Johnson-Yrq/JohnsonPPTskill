#!/usr/bin/env python3
"""Flatten a generated scene image's background onto the paper colour so the frame edge disappears.

For small lighting gradients only. Fits a smooth background surface and limits the correction
over the entire image to 12 RGB levels per channel; larger changes require image-tool editing.
Transparent assets are reported and left intact. Always inspect the rendered result.

Usage: python3 match_paper.py images/01.png --deck deck.json --dry-run
An explicit --paper '#RRGGBB' overrides --deck; without either, legacy #F7F6F2 is used.
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
    max_adjustment = 0
    for c in range(3):
        coef, *_ = np.linalg.lstsq(basis, arr[ys, xs, c].astype(np.float64), rcond=None)
        surface = full @ coef
        max_adjustment = max(max_adjustment, float(np.abs(paper[c] - surface).max()))
        out[..., c] += paper[c] - surface
    if max_adjustment > 12:
        return None, f'预计色彩改动 {max_adjustment:.1f} 超过 12 级，交由生图工具修正底色'
    return np.clip(out + .5, 0, 255).astype(np.uint8), f'背景占比 {core.mean():.0%}'


def process(path, paper, tolerance, dry_run):
    import numpy as np
    from PIL import Image
    image = Image.open(path)
    alpha = image.convert('RGBA').getchannel('A') if 'A' in image.getbands() or 'transparency' in image.info else None
    alpha_min = alpha.getextrema()[0] if alpha is not None else 255
    report = {'file': path.name, 'paper': list(paper), 'alpha_channel': alpha is not None, 'has_transparency': alpha_min < 255}
    if alpha_min < 255:
        return dict(report, skipped='已有实际透明像素；保持原图，在页面和导出稿中检查透明边缘')
    if min(image.size) < 21:
        return dict(report, skipped='图片太小，无法可靠拟合背景')
    arr = np.asarray(image.convert('RGB')).astype(np.int16)
    before_median, before_ptp = edge_stats(arr)
    report['before'] = {'edge_median': [int(v) for v in before_median], 'corner_spread': int(before_ptp),
                        'paper_delta': int(np.abs(before_median - paper).max())}
    result, note = flatten(arr, paper, tolerance)
    if result is None:
        return dict(report, skipped=note)
    after_median, after_ptp = edge_stats(result.astype(np.int16))
    report.update(note=note, after={'edge_median': [int(v) for v in after_median], 'corner_spread': int(after_ptp),
                                  'paper_delta': int(np.abs(after_median - paper).max())})
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
    p.add_argument('--paper', help='显式纸色；优先于 --deck')
    p.add_argument('--deck', help='从项目已选风格和 theme.paper 解析纸色')
    p.add_argument('--tolerance', type=int, default=8, help='与边缘中值相差不超过此值的像素视为背景（默认 8）')
    p.add_argument('--dry-run', action='store_true', help='只报告，不写文件')
    args = p.parse_args()
    if not 1 <= args.tolerance <= 24:
        p.error('--tolerance 须为 1–24；明显底色差异请使用生图工具修正')
    try:
        import numpy  # noqa: F401
        from PIL import Image  # noqa: F401
    except ImportError:
        p.exit(1, '需要 Pillow 和 numpy；没有时改用 image.edge_fade 轻微淡出边缘，或在生图工具里重生成纯色背景\n')
    try:
        from common import load_deck
        from style_packs import paper_color
        paper = parse_color(args.paper or (paper_color(load_deck(args.deck, layouts=None)[0]) if args.deck else '#F7F6F2'))
    except (ValueError, OSError) as exc:
        p.exit(1, str(exc) + '\n')
    import json
    for name in args.images:
        path = Path(name)
        if not path.is_file():
            p.exit(1, f'找不到图片：{name}\n')
        print(json.dumps(process(path, paper, args.tolerance, args.dry_run), ensure_ascii=False))


if __name__ == '__main__':
    main()
