import md2mu as mu

class TestStripCommentsAndNotes:
    def test_strips_html_comment(self):
        content = "before\n<!-- a comment\nspanning lines -->\nafter"
        assert mu.strip_comments_and_notes(content) == "before\n\nafter"
 
    def test_strips_bare_bracket_note(self):
        content = "Some text. [An internal note.] More text."
        assert mu.strip_comments_and_notes(content) == "Some text. More text."
 
    def test_real_markdown_link_is_not_stripped(self):
        content = "Read [the docs](https://example.com) for more."
        assert mu.strip_comments_and_notes(content) == content
 
    def test_image_markup_is_not_stripped(self):
        content = "![alt text](photos/x.jpg)"
        assert mu.strip_comments_and_notes(content) == content