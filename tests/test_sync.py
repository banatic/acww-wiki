import contextlib
import io
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import sync


class SnapshotTests(unittest.TestCase):
    def run_accept(self, root, incoming, old, revision_files):
        source = root/'upstream'/'wiki'
        snap = root/'site'/'source'
        content = root/'site'/'content'
        for base, files in ((source, incoming), (snap, old), (content, {'about.md':'# 번역'})):
            base.mkdir(parents=True, exist_ok=True)
            for rel, value in files.items():
                p = base/rel; p.parent.mkdir(parents=True, exist_ok=True)
                p.write_text(value, encoding='utf-8')
        def git_output(args, **kwargs):
            if args[1] == 'rev-parse': return 'abc123\n'
            if args[1] == 'show': return '2026-09-12T00:00:00+09:00\n'
            return '\n'.join('wiki/'+p for p in revision_files)
        def git_show(args, **kwargs):
            rel = args[-1].split(':wiki/',1)[1]
            return SimpleNamespace(returncode=0, stdout=revision_files[rel].encode('utf-8'))
        with patch.multiple(sync, ROOT=root/'site', SNAP=snap, CONTENT=content, LIVE=source), \
             patch('sys.argv', ['sync.py','--accept','--revision','abc123']), \
             patch.object(sync.subprocess, 'check_output', side_effect=git_output), \
             patch.object(sync.subprocess, 'run', side_effect=git_show), \
             contextlib.redirect_stdout(io.StringIO()):
            result = sync.main()
        return result, snap

    def test_tsv_changes_and_deletions_are_frozen(self):
        with tempfile.TemporaryDirectory() as temp:
            new = {'README.md':'# Source\n', 'data.tsv':'name\tvalue\nnew\t2\n'}
            old = {'README.md':'# Source\n', 'data.tsv':'old\t1\n', 'removed.tsv':'old\n'}
            result, snap = self.run_accept(Path(temp), new, old, new)
            self.assertEqual(result, 0)
            self.assertFalse((snap/'removed.tsv').exists())
            self.assertEqual((snap/'data.tsv').read_text(encoding='utf-8'), new['data.tsv'])
            manifest = json.loads((snap/'SNAPSHOT.json').read_text(encoding='utf-8'))
            self.assertEqual(set(manifest['files']), set(new))

    def test_wrong_revision_bytes_do_not_change_snapshot(self):
        with tempfile.TemporaryDirectory() as temp:
            new = {'README.md':'# Incoming\n', 'data.tsv':'changed\n'}
            old = {'README.md':'# Old\n', 'data.tsv':'old\n'}
            result, snap = self.run_accept(Path(temp), new, old, new | {'data.tsv':'other\n'})
            self.assertEqual(result, 1)
            self.assertEqual(sync.md_files(snap), old)
            self.assertFalse((snap/'SNAPSHOT.json').exists())

    def test_missing_revision_file_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            old = {'README.md':'# Source\n'}
            result, snap = self.run_accept(Path(temp), old, old, old | {'missing.tsv':'row\n'})
            self.assertEqual(result, 1)
            self.assertFalse((snap/'SNAPSHOT.json').exists())


if __name__ == '__main__':
    unittest.main()
