"""Shared, offline-only input checks for the HTML slide workflow."""
import io
import json
import struct
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent
ASSETS = SKILL / 'assets'
LAYOUTS = {'cover', 'scene', 'split', 'triad', 'journey', 'architecture', 'flow',
           'domains', 'formula', 'table', 'relations', 'closing', 'reading'}
EMBED_FORMATS = ('webp', 'jpeg', 'keep')
PAPER_RGB = (0xF7, 0xF6, 0xF2)


def local_path(root, value):
    if not isinstance(value, str) or not value.strip():
        raise ValueError('文件路径必须为项目内相对路径')
    p = Path(value)
    if p.is_absolute() or '://' in value:
        raise ValueError(f'请先将素材复制到项目内，不能引用绝对路径或网址：{value}')
    result = (root / p).resolve()
    if not result.is_relative_to(root.resolve()):
        raise ValueError(f'素材不能越出项目目录：{value}')
    return result


def number(value, default, low, high, label):
    if value is None:
        return default
    if isinstance(value, bool) or not isinstance(value, (float, int)) or not low <= value <= high:
        raise ValueError(f'{label} 必须在 {low}–{high} 之间')
    return value


def presentation_mode(deck):
    mode = deck.get('presentation_mode', 'speech')
    if not isinstance(mode, str) or mode not in {'speech', 'reading'}:
        raise ValueError('presentation_mode 可选 speech（演讲型）/ reading（阅读型）')
    return mode


def slide_images(slide):
    """Normalize single and multiple illustrations without accepting ignored fields."""
    if 'images' in slide:
        if 'image' in slide:
            raise ValueError('image 与 images 只能选一个')
        if slide.get('layout') != 'reading':
            raise ValueError('多配图 images 使用 reading 版式')
        images = slide['images']
        if not isinstance(images, list) or not 1 <= len(images) <= 3:
            raise ValueError('images 需要 1–3 张配图；更多场景请拆页')
    else:
        images = [slide.get('image')]
    if any(not isinstance(im, dict) for im in images):
        raise ValueError('每页需要 image 对象或 reading.images（含 src、alt）')
    sources = [im.get('src') for im in images]
    if any(isinstance(src, str) and sources.count(src) > 1 for src in sources):
        raise ValueError('同页多配图须对应不同内容，不能重复同一 src 凑面积')
    return images


def reading_composition(slide):
    images = slide_images(slide)
    choice = slide.get('composition', 'half_lr' if len(images) == 1 else 'half_tb')
    if not isinstance(choice, str) or choice not in {'half_lr', 'half_tb', 'half_diagonal', 'quarter'}:
        raise ValueError('reading.composition 可选 half_lr / half_tb / half_diagonal / quarter')
    if choice in {'half_lr', 'quarter'} and len(images) != 1:
        raise ValueError(f'{choice} 需要一张配图')
    if choice == 'half_diagonal' and len(images) != 2:
        raise ValueError('half_diagonal 需要两张对角配图')
    blocks = slide.get('blocks', [])
    if not isinstance(blocks, list):
        raise ValueError('reading.blocks 需要模块数组')
    if choice == 'half_diagonal' and len(blocks) != 2:
        raise ValueError('half_diagonal 需要两个内容模块，分别填入另外两个分区')
    if choice == 'quarter' and len(blocks) != 3:
        raise ValueError('quarter 需要三个内容模块，分别填入其余三个分区')
    if choice in {'half_diagonal', 'quarter'} and any(b.get('span', 1) != 1 for b in blocks if isinstance(b, dict)):
        raise ValueError('对角与四分之一版式的模块各占一格，不设置 span: 2')
    return choice


def load_deck(filename, layouts=LAYOUTS):
    """Validate the deck shell. `layouts=None` defers the layout whitelist to a Builder (see --builder)."""
    path = Path(filename).resolve()
    data = json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(data, dict) or data.get('version', 1) != 1:
        raise ValueError('需要 version: 1 的演示稿对象')
    if not isinstance(data.get('title'), str) or not data['title'].strip():
        raise ValueError('需要非空 title')
    slides = data.get('slides')
    mode = presentation_mode(data)
    if not isinstance(slides, list) or not slides:
        raise ValueError('需要非空 slides 数组')
    ids = set()
    for i, s in enumerate(slides, 1):
        if not isinstance(s, dict) or not isinstance(s.get('layout'), str) or not s['layout'].strip():
            raise ValueError(f'第 {i} 页需要 layout 字符串')
        if layouts is not None and s['layout'] not in layouts:
            raise ValueError(f'第 {i} 页 layout 无效；可选 {", ".join(sorted(layouts))}')
        if not isinstance(s.get('title'), str) or not s['title'].strip():
            raise ValueError(f'第 {i} 页缺少 title')
        sid = s.setdefault('id', f'p{i:02d}')
        if not isinstance(sid, str) or not sid or sid in ids or not all(c.isascii() and (c.isalnum() or c in '-_') for c in sid):
            raise ValueError(f'第 {i} 页 id 必须唯一，并仅用英文字母、数字、-、_')
        ids.add(sid)
        if 'presentation_mode' in s:
            raise ValueError(f'第 {i} 页不能单独设置 presentation_mode；使用根字段记录用户选择')
        if 'composition' in s and s['layout'] != 'reading':
            raise ValueError('composition 仅用于 reading 版式')
        if s['layout'] == 'reading':
            if mode != 'reading':
                raise ValueError('reading 版式需要 presentation_mode: reading；制作前先确认阅读型用途')
            reading_composition(s)
        for im in slide_images(s):
            local_path(path.parent, im.get('src'))
            if not isinstance(im.get('alt'), str) or not im['alt'].strip():
                raise ValueError(f'第 {i} 页需要有含义的 image.alt')
            if 'caption' in im and (s['layout'] != 'reading' or not isinstance(im['caption'], str) or not im['caption'].strip()):
                raise ValueError('caption 仅用于 reading 配图，须为非空字符串')
    from style_packs import resolve_style
    resolve_style(data)
    return data, path.parent


def read_raster(path):
    if not path.is_file():
        raise FileNotFoundError(f'缺少图片：{path.name}')
    content = path.read_bytes()
    if content.startswith(b'\x89PNG\r\n\x1a\n'):
        mime = 'image/png'
    elif content.startswith(b'\xff\xd8\xff'):
        mime = 'image/jpeg'
    elif content[:4] == b'RIFF' and content[8:12] == b'WEBP':
        mime = 'image/webp'
    else:
        raise ValueError(f'仅接受实际 PNG/JPEG/WebP 图片：{path.name}')
    return mime, content


def image_size(mime, data):
    """Pixel width/height from the file header, without any imaging library."""
    try:
        if mime == 'image/png':
            return struct.unpack('>II', data[16:24])
        if mime == 'image/jpeg':
            i = 2
            while i + 9 < len(data):
                if data[i] != 0xFF:
                    i += 1
                    continue
                marker = data[i + 1]
                if marker == 0xFF:
                    i += 1
                    continue
                if marker in (0xD8, 0x01) or 0xD0 <= marker <= 0xD7:
                    i += 2
                    continue
                length = struct.unpack('>H', data[i + 2:i + 4])[0]
                if marker in (0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF):
                    h, w = struct.unpack('>HH', data[i + 5:i + 9])
                    return w, h
                i += 2 + length
        if mime == 'image/webp':
            chunk = data[12:16]
            if chunk == b'VP8X':
                return int.from_bytes(data[24:27], 'little') + 1, int.from_bytes(data[27:30], 'little') + 1
            if chunk == b'VP8L':
                b = data[21:25]
                return 1 + ((b[1] & 0x3F) << 8 | b[0]), 1 + ((b[3] & 0xF) << 10 | b[2] << 2 | (b[1] & 0xC0) >> 6)
            if chunk == b'VP8 ':
                return struct.unpack('<H', data[26:28])[0] & 0x3FFF, struct.unpack('<H', data[28:30])[0] & 0x3FFF
    except (struct.error, IndexError):
        pass
    raise ValueError('无法读取图片尺寸，请确认文件未损坏')


def pillow():
    try:
        from PIL import Image
        return Image
    except ImportError:
        return None


def convert_image(mime, data, fmt, quality):
    """Re-encode a raster payload for embedding. Returns (mime, bytes, note).

    fmt: 'webp' | 'jpeg' | 'keep'. Falls back to the original bytes with a note
    when Pillow is unavailable or the conversion would not shrink the payload.
    """
    if fmt not in EMBED_FORMATS:
        raise ValueError(f'embed format 可选：{", ".join(EMBED_FORMATS)}')
    target = {'webp': 'image/webp', 'jpeg': 'image/jpeg'}.get(fmt)
    if fmt == 'keep' or mime == target:
        return mime, data, None
    Image = pillow()
    if Image is None:
        return mime, data, '未安装 Pillow，图片按原格式内嵌；安装 Pillow 或预先转成 WebP/JPEG 可大幅缩小文件'
    im = Image.open(io.BytesIO(data))
    buf = io.BytesIO()
    if fmt == 'webp':
        im.save(buf, 'WEBP', quality=quality, method=4)
    else:
        if im.mode in ('RGBA', 'LA', 'P'):
            rgba = im.convert('RGBA')
            flat = Image.new('RGB', rgba.size, PAPER_RGB)
            flat.paste(rgba, mask=rgba.getchannel('A'))
            im = flat
        im.convert('RGB').save(buf, 'JPEG', quality=quality, optimize=True)
    out = buf.getvalue()
    if len(out) >= len(data):
        return mime, data, None
    return target, out, None
