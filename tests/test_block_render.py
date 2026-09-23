import md2mu as mu

from . import default_renderer

class TestRenderDocument:
    def _render(self, content):
        blocks = mu.parse_blocks(content)
        return mu.render_document(blocks, default_renderer(), mu.TITLE_COLOR, mu.SECTION_COLOR)
 
    def test_heading_uses_title_color_for_level_one(self):
        out = self._render("# Title\n")
        assert out == "> `c`F000Title`f\n`a\n"
 
    def test_heading_uses_section_color_for_level_two(self):
        out = self._render("## Section\n")
        assert out == ">> `c`F8f0Section`f\n`a\n"
 
    def test_heading_glues_to_next_block_with_no_blank_line(self):
        out = self._render("## Section\n\nSome text.\n")
        lines = out.split("\n")
        assert lines[:3] == [">> `c`F8f0Section`f", "`a", "Some text."]
 
    def test_blank_line_between_ordinary_blocks(self):
        out = self._render("First paragraph.\n\nSecond paragraph.\n")
        assert out == "First paragraph.\n\nSecond paragraph.\n"
 
    def test_blank_line_between_bullets(self):
        out = self._render("- one\n- two\n")
        assert out == "\u2022 one\n\n\u2022 two\n"
 
    def test_image_gallery_has_no_blank_lines_between_images(self):
        out = self._render("![a](x.jpg)\n\n![b](y.jpg)\n")
        lines = out.rstrip("\n").split("\n")
        assert len(lines) == 2
        assert all(line.startswith("`(") for line in lines)
 
    def test_image_followed_by_non_image_gets_blank_line(self):
        out = self._render("![a](x.jpg)\n\nSome text.\n")
        lines = out.rstrip("\n").split("\n")
        assert lines[0].startswith("`(")
        assert lines[1] == ""
        assert lines[2] == "Some text."
 
    def test_caption_paragraph_is_centered(self):
        out = self._render("Caption: a photo of something.\n")
        assert out == "`cCaption: a photo of something.\n`a\n"
 
    def test_non_caption_paragraph_is_not_centered(self):
        out = self._render("Not a caption: just prose.\n")
        assert out == "Not a caption: just prose.\n"
 
    def test_output_has_single_trailing_newline(self):
        out = self._render("# Title\n\nBody.\n\n\n")
        assert out.endswith("Body.\n")
        assert not out.endswith("Body.\n\n")