#!/usr/bin/env python3
"""Make an offline, single-page presentation from an existing PDF using Poppler."""
import argparse
import base64
import html
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile


def convert(source, output, title=None):
    source, output = Path(source).resolve(), Path(output).resolve()
    if source == output:
        raise ValueError('输出 HTML 不能覆盖源 PDF。')
    if output.suffix.lower() != '.html':
        raise ValueError('输出文件须使用 .html 扩展名。')
    for tool in ('pdfinfo', 'pdftocairo'):
        if not shutil.which(tool):
            raise ValueError(f'缺少 {tool}；请安装 Poppler。')
    info = subprocess.run(['pdfinfo', str(source)], capture_output=True, text=True,
                          check=True, env={**os.environ, 'LC_ALL': 'C'}).stdout
    match = re.search(r'^Pages:\s+(\d+)', info, re.MULTILINE)
    if not match or int(match[1]) < 1:
        raise ValueError('无法读取 PDF 页数。')
    count = int(match[1])
    pages = []
    with tempfile.TemporaryDirectory(prefix='pdf-slides-') as tmp:
        for n in range(1, count + 1):
            svg = Path(tmp) / 'page.svg'
            subprocess.run(['pdftocairo', '-svg', '-f', str(n), '-l', str(n),
                            str(source), str(svg)], capture_output=True, check=True)
            # SVG keeps glyph outlines and vector diagrams sharp at presentation size.
            # Loaded as an image, it cannot execute scripts or fetch external resources.
            pages.append('data:image/svg+xml;base64,' +
                         base64.b64encode(svg.read_bytes()).decode('ascii'))
            print(f'已转换 {n}/{count}', flush=True)
    template = (Path(__file__).resolve().parent.parent / 'assets/pdf-player.html').read_text()
    document = template.replace('@@TITLE@@', html.escape(title or source.stem))
    document = document.replace('@@PAGES@@', json.dumps(pages, separators=(',', ':')))
    output.parent.mkdir(parents=True, exist_ok=True)
    # Leave any existing deliverable intact if conversion fails midway.
    with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=output.parent,
                                     suffix='.tmp', delete=False) as stream:
        temporary = Path(stream.name)
        stream.write(document)
    try:
        temporary.replace(output)
    finally:
        temporary.unlink(missing_ok=True)
    return {'output': str(output), 'pages': count, 'bytes': output.stat().st_size}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('pdf')
    parser.add_argument('--out', required=True)
    parser.add_argument('--title')
    args = parser.parse_args()
    try:
        print(json.dumps(convert(args.pdf, args.out, args.title), ensure_ascii=False))
    except (ValueError, OSError, subprocess.CalledProcessError) as exc:
        parser.exit(1, f'转换失败：{exc}\n')


if __name__ == '__main__':
    main()
