import md2mu as mu

class TestParseBlocks:
    def test_heading_levels(self):
        blocks = mu.parse_blocks("# Title\n\n## Section\n\n### Sub\n")
        assert [b["type"] for b in blocks] == ["heading", "heading", "heading"]
        assert [b["level"] for b in blocks] == [1, 2, 3]
        assert [b["text"] for b in blocks] == ["Title", "Section", "Sub"]
 
    def test_blockquote_joins_wrapped_lines(self):
        content = "> line one\n> line two\n> line three\n"
        blocks = mu.parse_blocks(content)
        assert blocks == [{"type": "blockquote", "text": "line one line two line three"}]
 
    def test_bullet_with_continuation_line(self):
        content = "- first part\n  second part\n"
        blocks = mu.parse_blocks(content)
        assert blocks == [{"type": "bullet", "text": "first part second part"}]
 
    def test_bullet_stops_at_next_bullet(self):
        content = "- one\n- two\n"
        blocks = mu.parse_blocks(content)
        assert [b["text"] for b in blocks] == ["one", "two"]
 
    def test_paragraph_preserves_line_breaks(self):
        content = "line one\nline two\n"
        blocks = mu.parse_blocks(content)
        assert blocks == [{"type": "paragraph", "lines": ["line one", "line two"]}]
 
    def test_single_image_is_its_own_group(self):
        blocks = mu.parse_blocks("![a](x.jpg)\n")
        assert blocks == [{"type": "image_group", "items": ["![a](x.jpg)"]}]
 
    def test_consecutive_images_group_across_blank_lines(self):
        content = "![a](x.jpg)\n\n![b](y.jpg)\n\ntext after\n"
        blocks = mu.parse_blocks(content)
        assert blocks[0] == {"type": "image_group", "items": ["![a](x.jpg)", "![b](y.jpg)"]}
        assert blocks[1] == {"type": "paragraph", "lines": ["text after"]}
 
    def test_blank_lines_between_blocks_are_ignored(self):
        content = "# Title\n\n\n\nParagraph.\n"
        blocks = mu.parse_blocks(content)
        assert [b["type"] for b in blocks] == ["heading", "paragraph"]