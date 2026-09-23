import pytest

import md2mu as mu

from . import default_renderer, FIXTURES_DIR

SAMPLE_MD = """<!-- internal note: do not publish yet -->
# Test Newsletter
 
> Welcome to the test. This is
> a two-line intro that should
> collapse into one paragraph.
 
## First Section
 
- **Bold lead-in.** Some body text with a [link](https://example.com/a) in it.
- Another item with *italic* and _underline_ words.
 
![First photo](photos/one.jpg)
 
![Second photo](photos/two.jpg)
 
## Second Section
 
Caption: A caption that should be centered. [drop this internal note]
 
Plain paragraph line one
that continues on a second raw line.
 
**73**
"""
 
EXPECTED_MU = (
    "> `c`F000Test Newsletter`f\n"
    "`a\n"
    "Welcome to the test. This is a two-line intro that should collapse into one paragraph.\n"
    "\n"
    ">> `c`F8f0First Section`f\n"
    "`a\n"
    "\u2022 `!Bold lead-in.`! Some body text with a `[link`https://example.com/a]` in it.\n"
    "\n"
    "\u2022 Another item with `*italic`* and `_underline`_ words.\n"
    "\n"
    "`(First photo`w=80`a=c`:/media/one.webp)\n"
    "`(Second photo`w=80`a=c`:/media/two.webp)\n"
    "\n"
    ">> `c`F8f0Second Section`f\n"
    "`a\n"
    "`cCaption: A caption that should be centered.\n"
    "`a\n"
    "\n"
    "Plain paragraph line one\n"
    "that continues on a second raw line.\n"
    "\n"
    "`!73`!\n"
)
 
 
class TestConvertEndToEnd:
    def test_mini_newsletter_matches_expected_output(self):
        result = mu.convert(SAMPLE_MD, default_renderer(), mu.TITLE_COLOR, mu.SECTION_COLOR)
        assert result == EXPECTED_MU
 
    @pytest.mark.skipif(
        not (FIXTURES_DIR / "newsletter.md").exists(),
        reason="bundled fixtures/newsletter.md not found",
    )
    def test_full_document_regression_against_bundled_fixture(self):
        # Full-length real-world document, used as a snapshot/regression
        # test: if this starts failing, something about the conversion
        # rules has changed -- check the diff carefully before updating
        # the fixture.
        source = (FIXTURES_DIR / "newsletter.md").read_text(encoding="utf-8")
        expected = (FIXTURES_DIR / "newsletter.mu").read_text(encoding="utf-8")
        mapper = mu.make_image_path_mapper(mu.DEFAULT_IMAGE_PREFIX / "cmesh-blog/img", mu.DEFAULT_IMAGE_EXT, remap=True)
        renderer = mu.make_image_markup_renderer(mapper)
        result = mu.convert(source, renderer, mu.TITLE_COLOR, mu.SECTION_COLOR)
        assert result == expected
 