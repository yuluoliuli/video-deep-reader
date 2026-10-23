"""Offline behavior checks; no media download and no file deletion."""
import unittest
import contextlib
import io
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch
import read_video as r


class EvidenceTests(unittest.TestCase):
    def new_directory(self):
        # Retain fixtures and evidence; never recursively delete a user's files.
        return Path(tempfile.mkdtemp(prefix='video-deep-reader-test-'))

    def test_coverage_does_not_double_count_or_exceed_duration(self):
        self.assertEqual(r.coverage([{'start': 0, 'end': 8}, {'start': 3, 'end': 20}], 10), 1)
        self.assertEqual(r.coverage([{'start': 2, 'end': 4}, {'start': 6, 'end': 8}], 10), .4)

    def test_bad_segments_excluded_original_words_preserved(self):
        rows = r.normalize([{'from': 1, 'to': 3, 'content': 'ego net'}, {'start': 2, 'end': 1, 'text': 'bad'}, {'start': float('nan'), 'end': 5, 'text': 'bad'}])
        self.assertEqual(rows, [{'start': 1., 'end': 3., 'text': 'ego net'}])

    def test_one_malformed_segment_does_not_discard_valid_subtitles(self):
        rows = r.normalize([
            {'start': 0, 'end': 2, 'text': 'original words'},
            {'start': 'not-a-number', 'end': 4, 'text': 'broken'},
            None,
            {'start': 4, 'end': 6, 'text': 'remaining words'},
        ])
        self.assertEqual([s['text'] for s in rows], ['original words', 'remaining words'])

    def test_nontext_subtitle_content_is_not_fabricated_as_words(self):
        rows = r.normalize([{'start': 0, 'end': 1, 'text': None}, {'start': 1, 'end': 2, 'text': False}, {'start': 2, 'end': 3, 'text': 'actual words'}])
        self.assertEqual([s['text'] for s in rows], ['actual words'])

    def test_skipped_malformed_rows_are_reported_as_partial(self):
        root = self.new_directory()
        video = root / 'fixture.mp4'
        video.write_bytes(b'probe is mocked; no media decoder invoked')
        subtitles = root / 'subtitles.json'
        subtitles.write_text(json.dumps([{'start': 0, 'end': 10, 'text': 'valid words'}, {'start': 'broken', 'end': 5, 'text': 'unreadable row'}]), encoding='utf-8')
        out = root / 'output'
        with patch.object(sys, 'argv', ['read_video.py', str(video), '--subtitle', str(subtitles), '--frames', '0', '--out', str(out)]), patch.object(r, 'probe', return_value=10), contextlib.redirect_stdout(io.StringIO()):
            result = r.main()
        self.assertEqual(result, 2, 'Skipping damaged evidence must be visible even when surviving timestamps cover the duration')
        manifest = json.loads((out / 'manifest.json').read_text())
        self.assertTrue(manifest['warnings'])
        self.assertEqual(json.loads((out / 'segments.json').read_text())[0]['text'], 'valid words')

    def test_invalid_cli_timestamp_has_argument_error_without_traceback(self):
        out = self.new_directory() / 'output'
        with patch.object(sys, 'argv', ['read_video.py', 'fixture.mp4', '--times', 'not-a-time', '--out', str(out)]), contextlib.redirect_stderr(io.StringIO()) as errors:
            with self.assertRaises(SystemExit) as raised:
                r.main()
        self.assertEqual(raised.exception.code, 2)
        self.assertNotIn('Traceback', errors.getvalue())
        self.assertFalse(out.exists())

    def test_malformed_cookie_is_rejected_without_leaking_its_value(self):
        root = self.new_directory()
        cookie = root / 'cookie.txt'
        cookie.write_text('SESSDATA=private-sentinel\nunexpected-header', encoding='utf-8')
        out = root / 'output'
        with patch.object(sys, 'argv', ['read_video.py', 'BV1toJR6HEVy', '--cookie-file', str(cookie), '--frames', '0', '--out', str(out)]), patch.object(r, 'open_request', side_effect=ValueError("Invalid header value b'SESSDATA=private-sentinel\\nunexpected-header'")) as opener, contextlib.redirect_stdout(io.StringIO()) as output:
            result = r.main()
        self.assertEqual(result, 1)
        self.assertNotIn('private-sentinel', output.getvalue())
        self.assertNotIn('private-sentinel', (out / 'manifest.json').read_text())
        opener.assert_not_called()

    def test_frames_zero_does_not_download_video_for_url_focus(self):
        out = self.new_directory() / 'output'
        metadata = {'title': 'fixture', 'duration': 10, 'bvid': 'BV1toJR6HEVy', 'cid': 1}
        with patch.object(sys, 'argv', ['read_video.py', 'BV1toJR6HEVy', '--frames', '0', '--out', str(out)]), \
             patch.object(r, 'remote', return_value=(metadata, 5)), \
             patch.object(r, 'api', return_value={'subtitle': {'subtitles': [{'subtitle_url': 'https://example.org/subtitle', 'lan': 'zh-CN'}]}}) as api, \
             patch.object(r, 'request', return_value={'body': [{'from': 0, 'to': 10, 'content': 'fixture words'}]}), \
             patch.object(r, 'download') as download, patch.object(r, 'frames') as frames, \
             contextlib.redirect_stdout(io.StringIO()):
            result = r.main()
        self.assertEqual(result, 0)
        self.assertEqual([c.args[0] for c in api.call_args_list], ['/x/player/v2'])
        download.assert_not_called()
        frames.assert_not_called()
        self.assertEqual(json.loads((out / 'frames.json').read_text()), [])

    def test_frame_timeout_preserves_other_frames_and_their_manifest(self):
        root = self.new_directory()
        calls = []

        def extract(args, **kwargs):
            calls.append(args)
            if len(calls) == 2:
                raise subprocess.TimeoutExpired('ffmpeg', 60)
            Path(args[-1]).write_bytes(b'fixture frame')
            return subprocess.CompletedProcess(args, 0)

        with patch.object(r.subprocess, 'run', side_effect=extract):
            result = r.frames(root / 'video.mp4', root / 'frames', [1, 2, 3], [])
        self.assertEqual([f['status'] for f in result], ['ok', 'failed', 'ok'])
        self.assertEqual(result[1]['error'], 'TimeoutExpired')
        self.assertTrue(Path(result[0]['path']).is_file())
        self.assertTrue(Path(result[2]['path']).is_file())

    def test_focus_clamped_and_deduplicated_without_uniform_frames(self):
        self.assertEqual(r.plan(10, 0, [-3, 0, 12, 12]), [0, 9.9])

    def test_frame_budget_spans_runtime(self):
        points = r.plan(460, 12, [])
        self.assertEqual(len(points), 12)
        self.assertLess(points[0], 30)
        self.assertGreater(points[-1], 430)

    def test_selected_page_duration_and_focus(self):
        data = {'title': 'test', 'pages': [{'cid': 1, 'duration': 10}, {'cid': 2, 'duration': 99}]}
        with patch.object(r, 'api', return_value=data):
            meta, focus = r.remote('https://www.bilibili.com/video/BV1toJR6HEVy/?p=2&t=01:20', None, '')
            self.assertEqual((meta['cid'], meta['duration'], meta['page'], focus), (2, 99, 2, 80))
            with self.assertRaises(ValueError):
                r.remote('BV1toJR6HEVy', 3, '')

    def test_foreign_host_not_treated_as_bilibili(self):
        with self.assertRaises(ValueError):
            r.remote('https://bilibili.com.example.org/video/BV1toJR6HEVy', None, '')

    def test_credentials_only_sent_to_api(self):
        with patch.object(r, 'open_request') as open_url:
            r.request('https://cdn.example.org/file', 'SESSDATA=sentinel', binary=True)
            self.assertFalse(open_url.call_args.args[0].has_header('Cookie'))
            r.request('https://api.bilibili.com/x/test', 'SESSDATA=sentinel', binary=True)
            self.assertEqual(open_url.call_args.args[0].get_header('Cookie'), 'SESSDATA=sentinel')

    def test_redirect_drops_credentials(self):
        req = r.Request('https://api.bilibili.com/x/test', headers={'Cookie': 'SESSDATA=sentinel', 'Authorization': 'sentinel'})
        new = r.SafeRedirect().redirect_request(req, None, 302, 'Found', {}, 'https://example.org/file')
        self.assertFalse(new.has_header('Cookie'))
        self.assertFalse(new.has_header('Authorization'))


if __name__ == '__main__':
    unittest.main()
