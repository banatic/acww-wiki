import unittest

from build import GRADE_INFO
from wiki_html import CitationFolder, Headings, add_source_anchors, rewrite_links, prepare_markdown
import markdown


class WikiHtmlTests(unittest.TestCase):
    def test_mismatched_table_separator_is_rendered_without_changing_cells(self):
        source = '| API | 상태 | 근거 |\n|---|---|---|---|\n| 0 | 준비 | receipt |\n'
        body = markdown.markdown(prepare_markdown(source), extensions=['tables'])
        self.assertIn('<table>', body)
        self.assertIn('<td>receipt</td>', body)
        self.assertEqual(prepare_markdown('```\n'+source+'```'), '```\n'+source+'```')

    def fold(self, body):
        return CitationFolder(GRADE_INFO).render(body)

    def test_citation_preserves_code_brackets_and_nested_link(self):
        body = '<p>결과 [H/E: <a href="report.md#part">근거</a>; <code>seen[16]</code>; [보충]]. 뒤</p>'
        folded = self.fold(body)
        self.assertIn('data-grade="H/E"', folded)
        self.assertIn('<code>seen[16]</code>; [보충]</span></span>. 뒤', folded)
        self.assertIn('href="report.md#part"', folded)
        self.assertEqual(folded.count('class="cite"'), 1)

    def test_code_and_href_are_not_citations(self):
        body = '<pre><code>[S: example]</code></pre><p><a href="x/[S:example]">link</a> [M: measured]</p>'
        folded = self.fold(body)
        self.assertIn('<code>[S: example]</code>', folded)
        self.assertIn('href="x/[S:example]"', folded)
        self.assertEqual(folded.count('class="cite"'), 1)
        self.assertIn('data-grade="M"', folded)

    def test_unclosed_citation_cannot_swallow_next_paragraph(self):
        body = '<p>[H: unfinished</p><p>다음 [E: done]</p>'
        folded = self.fold(body)
        self.assertIn('<p>[H: unfinished</p>', folded)
        self.assertEqual(folded.count('class="cite"'), 1)

    def test_english_aliases_and_duplicate_headings(self):
        original = '<h1>Title</h1><h2 id="gameplay57-the-beach">GAMEPLAY57 -- the beach</h2><h2 id="same">Same</h2><h2 id="same_1">Same</h2>'
        translated = '<h2 id="해변">해변</h2><h2 id="동일">동일</h2><h2 id="동일_1">동일</h2>'
        result = add_source_anchors(translated, original)
        for anchor in ('title', 'gameplay57----the-beach', 'gameplay57-the-beach', 'same', 'same-1', 'same_1'):
            self.assertIn(f'id="{anchor}"', result)
        self.assertEqual(Headings(result).items, Headings(translated).items)

    def test_missing_translation_section_is_rejected(self):
        with self.assertRaises(ValueError):
            add_source_anchors('<h2 id="a">A</h2>', '<h1>T</h1><h2>A</h2><h2>B</h2>')

    def test_source_anchor_cannot_silently_target_another_section(self):
        with self.assertRaises(ValueError):
            add_source_anchors('<h2 id="bar">첫째</h2><h2 id="foo">둘째</h2>',
                               '<h1>T</h1><h2 id="foo">Foo</h2><h2 id="bar">Bar</h2>')

    def test_relative_wiki_and_evidence_links(self):
        body = '<a href="../README.md">about</a><a href="town.md#town-shape">town</a><a href="../../docs/log/run.md#proof">evidence</a><a href="https://example.com/readme.md">external</a>'
        paths = {'wiki/README.md':'about.html', 'wiki/systems/town.md':'systems/town.html'}
        result = rewrite_links(body, 'wiki/systems/acre-grid.md', 'systems/acre-grid.html', paths, 'abc123')
        self.assertIn('href="../about.html"', result)
        self.assertIn('href="town.html#town-shape"', result)
        self.assertIn('href="https://github.com/banatic/acww-decomp/blob/abc123/docs/log/run.md#proof"', result)
        self.assertIn('href="https://example.com/readme.md"', result)


if __name__ == '__main__':
    unittest.main()
