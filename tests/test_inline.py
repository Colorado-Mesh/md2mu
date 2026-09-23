import pytest
 
import md2mu as mu
from . import default_renderer, render

class TestEscapeLiteral:
    def test_escapes_backtick(self):
        assert mu.escape_literal("a`b") == r"a\`b"
 
    def test_noop_without_backtick(self):
        assert mu.escape_literal("plain text, nothing special") == "plain text, nothing special"
 
    def test_escapes_multiple_backticks(self):
        assert mu.escape_literal("`a`b`") == r"\`a\`b\`"
 
 
class TestRenderInlineEmphasis:
    @pytest.mark.parametrize(
        "markdown, expected",
        [
            ("**bold**", "`!bold`!"),
            ("*italic*", "`*italic`*"),
            ("_underline_", "`_underline`_"),
        ],
    )
    def test_basic_emphasis(self, markdown, expected):
        assert render(markdown) == expected
 
    def test_preserves_surrounding_text(self):
        assert render("before **bold** after") == "before `!bold`! after"
 
    def test_multiple_spans_in_one_string(self):
        result = render("**bold** and *italic* and _under_")
        assert result == "`!bold`! and `*italic`* and `_under`_"
 
    def test_bold_is_not_split_into_two_italics(self):
        assert render("**bold text**") == "`!bold text`!"
 
    def test_underscore_inside_word_is_not_emphasis(self):
        # Underscores flanked by word characters (e.g. filenames,
        # identifiers) must not be mistaken for underline-emphasis.
        text = "event_2026-09-17_JohnC_2_web.jpg"
        assert render(text) == text
 
    def test_plain_text_with_no_markup_is_unchanged(self):
        text = "Nothing fancy here, just prose."
        assert render(text) == text
 
    def test_literal_backtick_in_prose_is_escaped(self):
        assert render("some `code`-like text") == r"some \`code\`-like text"
 
 
class TestRenderInlineLinks:
    def test_basic_link(self):
        assert render("[text](https://example.com)") == "`[text`https://example.com]`"
 
    def test_link_followed_by_period_is_not_escaped(self):
        result = render("see [here](https://x.example) please.")
        assert result == "see `[here`https://x.example]` please."
 
    def test_link_followed_by_space_is_not_escaped(self):
        result = render("[here](https://x.example) continues")
        assert result == "`[here`https://x.example]` continues"
 
    def test_link_followed_by_close_paren_is_escaped(self):
        # Otherwise the bare backtick after `]` combined with a raw ")"
        # would read as Micron's "close image" token.
        result = render("(see [here](https://x.example))")
        assert result == r"(see `[here`https://x.example]`\)"
 
    def test_link_text_with_backtick_is_escaped(self):
        result = render("[a`b](https://x.example)")
        assert result == r"`[a\`b`https://x.example]`"
 
    def test_link_at_end_of_string(self):
        assert render("go here: [link](https://x.example)") == "go here: `[link`https://x.example]`"
 
 
class TestImageMarkup:
    def test_default_remap_changes_dir_and_extension(self):
        renderer = default_renderer()
        result = renderer("A caption", "photos/foo_bar.jpg")
        assert result == "`(A caption`w=80`a=c`:/media/foo_bar.webp)"
 
    def test_no_remap_passes_path_through_unchanged(self):
        mapper = mu.make_image_path_mapper(mu.PurePosixPath("/whatever"), "png", remap=False)
        renderer = mu.make_image_markup_renderer(mapper)
        result = renderer("Alt", "photos/foo.jpg")
        assert result == "`(Alt`w=80`a=c`:photos/foo.jpg)"
 
    def test_empty_ext_keeps_original_extension(self):
        mapper = mu.make_image_path_mapper(mu.PurePosixPath("/img"), "", remap=True)
        renderer = mu.make_image_markup_renderer(mapper)
        result = renderer("Alt", "photos/foo.jpeg")
        assert result == "`(Alt`w=80`a=c`:/img/foo.jpeg)"
 
    def test_custom_prefix_and_extension(self):
        mapper = mu.make_image_path_mapper(mu.PurePosixPath("/assets/img"), "png", remap=True)
        renderer = mu.make_image_markup_renderer(mapper)
        result = renderer("Alt", "nested/dir/photo.jpg")
        assert result == "`(Alt`w=80`a=c`:/assets/img/photo.png)"
 
    def test_inline_image_inside_prose(self):
        renderer = default_renderer()
        result = mu.render_inline("before ![alt](photos/x.jpg) after", renderer)
        assert result == "before `(alt`w=80`a=c`:/media/x.webp) after"