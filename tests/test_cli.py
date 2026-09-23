from click.testing import CliRunner
 
import md2mu as mu
 

class TestCli:
    def test_default_output_path_is_input_with_mu_suffix(self, tmp_path):
        src = tmp_path / "input.md"
        src.write_text("# Hi\n\nHello world.\n", encoding="utf-8")
 
        result = CliRunner().invoke(mu.main, [str(src)])
 
        assert result.exit_code == 0
        out_path = tmp_path / "input.mu"
        assert out_path.exists()
        assert "Hello world." in out_path.read_text(encoding="utf-8")
 
    def test_custom_output_path(self, tmp_path):
        src = tmp_path / "input.md"
        src.write_text("# Hi\n\nHello world.\n", encoding="utf-8")
        dest = tmp_path / "custom.mu"
 
        result = CliRunner().invoke(mu.main, [str(src), "-o", str(dest)])
 
        assert result.exit_code == 0
        assert dest.exists()
 
    def test_missing_input_file_errors_cleanly(self, tmp_path):
        result = CliRunner().invoke(mu.main, [str(tmp_path / "nope.md")])
 
        assert result.exit_code != 0
        assert "does not exist" in result.output
 
    def test_no_image_remap_flag(self, tmp_path):
        src = tmp_path / "input.md"
        src.write_text("![alt](photos/x.jpg)\n", encoding="utf-8")
        dest = tmp_path / "out.mu"
 
        result = CliRunner().invoke(mu.main, [str(src), "-o", str(dest), "--no-image-remap"])
 
        assert result.exit_code == 0
        assert ":photos/x.jpg)" in dest.read_text(encoding="utf-8")
 
    def test_custom_image_prefix_and_extension(self, tmp_path):
        src = tmp_path / "input.md"
        src.write_text("![alt](photos/x.jpg)\n", encoding="utf-8")
        dest = tmp_path / "out.mu"
 
        result = CliRunner().invoke(
            mu.main,
            [str(src), "-o", str(dest), "--image-prefix", "/assets", "--image-ext", "png"],
        )
 
        assert result.exit_code == 0
        assert ":/assets/x.png)" in dest.read_text(encoding="utf-8")
 
    def test_custom_title_and_section_colors(self, tmp_path):
        src = tmp_path / "input.md"
        src.write_text("# Title\n\n## Section\n", encoding="utf-8")
        dest = tmp_path / "out.mu"
 
        result = CliRunner().invoke(
            mu.main,
            [str(src), "-o", str(dest), "--title-color", "abc", "--section-color", "def"],
        )
 
        assert result.exit_code == 0
        text = dest.read_text(encoding="utf-8")
        assert "`Fabc" in text
        assert "`Fdef" in text
 
    def test_help_exits_zero(self):
        result = CliRunner().invoke(mu.main, ["--help"])
 
        assert result.exit_code == 0
        assert "Convert INPUT_PATH" in result.output
 
    def test_writes_confirmation_to_stderr_like_channel(self, tmp_path):
        src = tmp_path / "input.md"
        src.write_text("# Hi\n", encoding="utf-8")
 
        result = CliRunner().invoke(mu.main, [str(src)])
 
        assert "Wrote" in result.output