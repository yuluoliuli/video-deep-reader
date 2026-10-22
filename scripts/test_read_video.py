"""Offline behavior checks; no media download and no file deletion."""
import unittest
from unittest.mock import patch
import read_video as r


class EvidenceTests(unittest.TestCase):
    def test_coverage_does_not_double_count_or_exceed_duration(self):
        self.assertEqual(r.coverage([{'start': 0, 'end': 8}, {'start': 3, 'end': 20}], 10), 1)
        self.assertEqual(r.coverage([{'start': 2, 'end': 4}, {'start': 6, 'end': 8}], 10), .4)

    def test_bad_segments_excluded_original_words_preserved(self):
        rows = r.normalize([{'from': 1, 'to': 3, 'content': 'ego net'}, {'start': 2, 'end': 1, 'text': 'bad'}, {'start': float('nan'), 'end': 5, 'text': 'bad'}])
        self.assertEqual(rows, [{'start': 1., 'end': 3., 'text': 'ego net'}])

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
