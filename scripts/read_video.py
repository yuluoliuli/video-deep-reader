"""Evidence acquisition only. No LLM, automatic deletion, or persistent services."""
import argparse
import json
import math
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from urllib.parse import parse_qs, urlencode, urlparse
from urllib.request import Request, urlopen, HTTPRedirectHandler, build_opener


class SafeRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        redirected = super().redirect_request(req, fp, code, msg, headers, newurl)
        if redirected is not None:
            # Never forward a credential header on redirects, even to the same host.
            redirected.remove_header('Cookie')
            redirected.remove_header('Authorization')
        return redirected


def open_request(req, timeout=35):
    return build_opener(SafeRedirect()).open(req, timeout=timeout)


def save(path, data):
    Path(path).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')


def request(url, cookie='', binary=False):
    headers = {'User-Agent': 'Mozilla/5.0', 'Referer': 'https://www.bilibili.com/'}
    # Credentials stay on the Bilibili API host, never on CDN/media hosts.
    if cookie and urlparse(url).scheme == 'https' and urlparse(url).hostname == 'api.bilibili.com':
        if any(ord(ch) < 32 or ord(ch) == 127 for ch in cookie):
            raise ValueError('Credential header must be a single line without control characters')
        headers['Cookie'] = cookie
    r = open_request(Request(url, headers=headers), timeout=35)
    if binary:
        return r
    with r:
        return json.load(r)


def api(path, params, cookie):
    r = request('https://api.bilibili.com' + path + '?' + urlencode(params), cookie)
    if r.get('code') != 0:
        raise RuntimeError('Bilibili API code=' + str(r.get('code')))
    return r.get('data') or {}


def normalize(rows, warnings=None):
    result = []
    invalid = 0
    for s in rows:
        if not isinstance(s, dict):
            invalid += 1
            continue
        try:
            start, end = float(s.get('start', s.get('from', 0))), float(s.get('end', s.get('to', 0)))
        except (TypeError, ValueError):
            invalid += 1
            continue
        text = s.get('text', s.get('content', ''))
        if not isinstance(text, str):
            invalid += 1
            continue
        text = text.strip()
        if text and math.isfinite(start) and math.isfinite(end) and 0 <= start < end:
            result.append({'start': start, 'end': end, 'text': text})
        elif text:
            invalid += 1
    if invalid and warnings is not None:
        warnings.append(str(invalid) + ' malformed subtitle segments skipped; valid original text retained.')
    return sorted(result, key=lambda s: (s['start'], s['end']))


def seconds(value):
    total = 0.0
    for n in value.replace(',', '.').split(':'):
        total = total * 60 + float(n)
    if not math.isfinite(total) or total < 0:
        raise ValueError('Invalid timestamp')
    return total


def load_subtitle(path, warnings=None):
    text = Path(path).read_text(encoding='utf-8-sig')
    if Path(path).suffix.lower() == '.json':
        data = json.loads(text)
        return normalize(data if isinstance(data, list) else data.get('body', data.get('segments', [])), warnings)
    rows = []
    pattern = r'(?m)^([\d:.,]+)\s+-->\s+([\d:.,]+)[^\n]*\n(.*?)(?=\n\s*\n|\Z)'
    for m in re.finditer(pattern, text, re.S):
        rows.append({'start': seconds(m[1]), 'end': seconds(m[2]), 'text': re.sub('<[^>]+>', '', m[3]).strip()})
    return normalize(rows, warnings)


def coverage(rows, duration):
    intervals = sorted((max(0, s['start']), min(duration, s['end'])) for s in rows)
    end = covered = 0.0
    for a, b in intervals:
        if b > max(a, end):
            covered += b - max(a, end)
        end = max(end, b)
    return round(covered / duration, 4) if duration > 0 else 0


def plan(duration, count, extra):
    if not math.isfinite(duration) or duration <= 0:
        raise ValueError('Unknown or invalid duration')
    base = [duration * (i + .5) / count for i in range(count)]
    return sorted(set(round(min(max(0, t), max(0, duration - .1)), 3) for t in base + extra))


def probe(video):
    r = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'json', str(video)], capture_output=True, text=True, timeout=45)
    if r.returncode:
        raise RuntimeError('ffprobe failed')
    return float(json.loads(r.stdout)['format']['duration'])


def frames(video, out, times, rows):
    out.mkdir(parents=True, exist_ok=True)
    results = []
    for t in times:
        dest = out / ('frame-%010.3f.jpg' % t)
        if dest.exists():
            raise RuntimeError('Frame already exists; use a new frame output directory')
        item = {'time': t, 'path': str(dest.resolve()), 'status': 'failed', 'nearby_subtitles': [s for s in rows if s['start'] <= t + 5 and s['end'] >= t - 5], 'visual_review': 'not_reviewed'}
        try:
            r = subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-n', '-ss', str(t), '-i', str(video), '-frames:v', '1', '-vf', 'scale=1280:-2', '-q:v', '3', str(dest)], capture_output=True, timeout=60)
            if r.returncode == 0 and dest.is_file() and dest.stat().st_size:
                item['status'] = 'ok'
        except (subprocess.TimeoutExpired, OSError) as e:
            item['error'] = type(e).__name__
        results.append(item)
    return results


def download(url, target, max_mb):
    limit, size = max_mb * 1024 * 1024, 0
    with request(url, binary=True) as response, target.open('xb') as f:
        if int(response.headers.get('Content-Length', '0')) > limit:
            raise RuntimeError('Media exceeds download size limit')
        while True:
            chunk = response.read(1024 * 1024)
            if not chunk:
                break
            size += len(chunk)
            if size > limit:
                raise RuntimeError('Media exceeds download size limit; partial file retained')
            f.write(chunk)


def remote(source, page, cookie):
    if source.startswith('https://b23.tv/'):
        with urlopen(Request(source, headers={'User-Agent': 'Mozilla/5.0'}), timeout=25) as r:
            source = r.url
    if source.startswith(('http://', 'https://')):
        host = urlparse(source).hostname or ''
        if host != 'bilibili.com' and not host.endswith('.bilibili.com'):
            raise ValueError('Only Bilibili video URLs are supported')
    m = re.search(r'BV[0-9A-Za-z]{10}', source)
    if not m:
        raise ValueError('Expected BV id or Bilibili video URL')
    qs = parse_qs(urlparse(source).query)
    number = page if page is not None else int(qs.get('p', ['1'])[0])
    d = api('/x/web-interface/view', {'bvid': m[0]}, cookie)
    parts = d.get('pages') or []
    if not 1 <= number <= len(parts):
        raise ValueError('Requested P does not exist')
    part = parts[number - 1]
    meta = {'title': d['title'], 'description': d.get('desc', ''), 'owner': d.get('owner', {}).get('name'), 'bvid': m[0], 'cid': part['cid'], 'page': number, 'page_count': len(parts), 'part_title': part.get('part'), 'duration': part['duration'], 'url': 'https://www.bilibili.com/video/' + m[0] + '?p=' + str(number)}
    focus = seconds(qs['t'][0]) if 't' in qs else None
    return meta, focus


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('source', help='BV id, Bilibili URL, or local video')
    p.add_argument('--out', required=True, help='New output directory; existing paths are not overwritten')
    p.add_argument('--page', type=int)
    p.add_argument('--subtitle', help='Local JSON, SRT or VTT')
    p.add_argument('--cookie-file', help='Explicit existing SESSDATA or Cookie text file; never copied')
    p.add_argument('--frames', type=int, default=12)
    p.add_argument('--times', default='', help='Additional comma separated seconds or HH:MM:SS')
    p.add_argument('--frames-only', action='store_true', help='Local video supplemental frames only')
    p.add_argument('--max-mb', type=int, default=500)
    args = p.parse_args()
    if not 0 <= args.frames <= 48 or args.max_mb < 1:
        p.error('frames must be 0..48 and max-mb positive')
    try:
        extra = [seconds(t.strip()) for t in args.times.split(',') if t.strip()]
    except ValueError:
        p.error('times must contain non-negative finite seconds or HH:MM:SS timestamps')
    if len(extra) > 48:
        p.error('At most 48 supplemental timestamps per call')
    out = Path(args.out).resolve()
    try:
        out.mkdir(parents=True, exist_ok=False)
    except OSError:
        print(json.dumps({'status': 'failed', 'error': 'Output directory already exists or cannot be created'}))
        return 1
    warnings, rows, images = [], [], []
    manifest = {'status': 'incomplete', 'warnings': warnings, 'analysis_status': 'pending_host_model', 'frames': images, 'automatic_cleanup': False}
    try:
        video = Path(args.source)
        local = video.is_file()
        if args.frames_only and not local:
            raise ValueError('frames-only requires a local video')
        cookie = Path(args.cookie_file).read_text(encoding='utf-8-sig').strip() if args.cookie_file else os.environ.get('BILIBILI_SESSDATA', '').strip()
        if cookie and '=' not in cookie:
            cookie = 'SESSDATA=' + cookie
        if local:
            video = video.resolve()
            meta = {'title': video.stem, 'duration': probe(video), 'local_source': str(video)}
            focus = None
        else:
            meta, focus = remote(args.source, args.page, cookie)
        save(out / 'metadata.json', meta)
        manifest['metadata'] = meta
        if args.subtitle:
            rows = load_subtitle(args.subtitle, warnings)
            manifest['subtitle_source'] = 'user_supplied'
        elif not local:
            try:
                d = api('/x/player/v2', {'bvid': meta['bvid'], 'cid': meta['cid']}, cookie)
                tracks = d.get('subtitle', {}).get('subtitles', [])
                usable = [s for s in tracks if s.get('subtitle_url')]
                usable.sort(key=lambda s: (not s.get('lan', '').startswith(('zh', 'ai-zh')), s.get('lan', '').startswith('ai-')))
                if usable:
                    track = usable[0]
                    url = track['subtitle_url']
                    rows = normalize(request('https:' + url if url.startswith('//') else url).get('body', []), warnings)
                    manifest['subtitle_source'] = 'platform:' + track.get('lan', 'unknown')
                else:
                    warnings.append('No accessible subtitle URL: login may be required or subtitles unavailable.')
            except Exception as e:
                warnings.append('Subtitle acquisition failed: ' + type(e).__name__)
        if not rows and not args.frames_only:
            warnings.append('No transcript. Do not infer speech from frames; provide subtitles or use explicitly authorized local ASR.')
        save(out / 'segments.json', rows)
        (out / 'transcript.txt').write_text('\n'.join('[%0.2f–%0.2f] %s' % (s['start'], s['end'], s['text']) for s in rows), encoding='utf-8')
        manifest['subtitle_coverage'] = coverage(rows, float(meta['duration']))
        if rows and manifest['subtitle_coverage'] < .7:
            warnings.append('Subtitle time coverage below 70%; inspect gaps before drawing whole-video conclusions.')
        if focus is not None and (args.frames or extra):
            extra += [focus - 3, focus, focus + 3]
        if args.frames or extra:
            try:
                if not shutil.which('ffmpeg') or not shutil.which('ffprobe'):
                    raise RuntimeError('ffmpeg and ffprobe required')
                if not local:
                    d = api('/x/player/playurl', {'bvid': meta['bvid'], 'cid': meta['cid'], 'qn': 64, 'fnval': 16, 'fourk': 0}, cookie)
                    streams = d.get('dash', {}).get('video', [])
                    if not streams:
                        raise RuntimeError('No accessible DASH video; use ego playback or an authorized local file')
                    suitable = [s for s in streams if 720 <= s.get('height', 0) <= 1080] or streams
                    stream = min(suitable, key=lambda s: (s.get('bandwidth', 0)))
                    video = out / 'video-only.mp4'
                    download(stream.get('baseUrl') or stream['base_url'], video, args.max_mb)
                manifest['video_path'] = str(video.resolve())
                images.extend(frames(video, out / 'frames', plan(float(meta['duration']), args.frames, extra), rows))
                if any(f['status'] != 'ok' for f in images):
                    warnings.append('Some requested frames failed; inspect frame manifest.')
            except Exception as e:
                warnings.append('Visual acquisition incomplete: ' + type(e).__name__ + (': ' + str(e) if isinstance(e, RuntimeError) else ''))
        manifest['status'] = 'partial' if warnings else 'acquired'
        save(out / 'frames.json', images)
        save(out / 'manifest.json', manifest)
        print(json.dumps({'status': manifest['status'], 'output': str(out), 'segments': len(rows), 'frames': len(images), 'warnings': warnings}, ensure_ascii=False))
        return 0 if manifest['status'] == 'acquired' else 2
    except Exception as e:
        manifest['status'] = 'failed'
        manifest['error'] = type(e).__name__ + (': ' + str(e) if isinstance(e, (ValueError, RuntimeError)) else '')
        save(out / 'manifest.json', manifest)
        print(json.dumps({'status': 'failed', 'output': str(out), 'error': manifest['error']}, ensure_ascii=False))
        return 1


if __name__ == '__main__':
    sys.exit(main())
