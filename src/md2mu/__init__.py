"""
md2mu - Convert a Markdown (.md) file into a Micron (.mu) file.

Micron is the lightweight hypertext markup used by Reticulum / NomadNet
pages. This converter was built by reverse-engineering a matched pair of
example files (a newsletter written in Markdown, and the same newsletter
hand-converted to Micron), so it follows the specific formatting
conventions used there:

  Markdown                          Micron
  ------------------------------    ---------------------------------
  # Heading 1                       > `c`F<title-color>Heading 1`f  + `a
  ## Heading 2                      >> `c`F<section-color>Heading 2`f + `a
  ### Heading 3                     >>> `c`F<section-color>Heading 3`f + `a
  > blockquote (joined into one     plain left-aligned paragraph
    paragraph, source line wraps
    are collapsed)
  - bullet / * bullet / + bullet    single-line-per-item paragraphs
                                       prefixed with the bullet glyph "\u2022"
  **bold**                          `!bold`!
  *italic*                          `*italic`*
  _underline_                       `_underline`_   (NOTE: single
                                       underscores map to *underline* in
                                       this convention, not italics)
  [text](url)                       `[text`url]`   (a bare, "resetting"
                                       backtick always follows the
                                       closing `]`; if the very next
                                       character in the source is a
                                       literal ")" it is escaped as
                                       "\\)" so it can't be misread as
                                       the micron "close image" token)
  ![alt](path)                      `(alt`w=<width>`a=<align>`:<path>)
                                       consecutive image-only lines are
                                       grouped together with no blank
                                       line between them (a "gallery");
                                       every other paragraph is
                                       separated from its neighbours by
                                       exactly one blank line.
  A paragraph beginning with the    centered, e.g.
    literal text "Caption:"           `cCaption: ...`
                                       `a
  A bare "[...]" aside that is      removed entirely (treated as an
    NOT a real markdown link          internal/editorial note, not
    (i.e. not followed by "(url)")    meant for publication)

Because the example ".mu" file was a *hand-edited* deliverable (not a
byte-for-byte mechanical export), this script won't reproduce it letter
for letter -- a couple of things in that file were manual editorial
choices (a capitalized word here, a dropped review-note there). What it
does do is apply the underlying rules consistently across an entire
document, so you get the same house style throughout.

Usage:
    python3 md2mu input.md
    python3 md2mu input.md -o output.mu
    python3 md2mu input.md --image-prefix /media/site/img/ --image-ext webp
    python3 md2mu input.md --no-image-remap
"""

import re
from pathlib import Path, PurePosixPath

import click

# --------------------------------------------------------------------------
# Configuration defaults (all overridable from the command line -- see the
# click options on main() below).
# --------------------------------------------------------------------------

TITLE_COLOR = "000"     # `F color used for the level-1 (page title) heading
SECTION_COLOR = "8f0"   # `F color used for level-2 / level-3 headings
IMAGE_WIDTH = "80"      # `w= value used for images
IMAGE_ALIGN = "c"       # `a= value used for images
BULLET_GLYPH = "\u2022"  # "•"

DEFAULT_IMAGE_PREFIX = PurePosixPath("/media/")
DEFAULT_IMAGE_EXT = "webp"


# --------------------------------------------------------------------------
# Inline formatting: bold / italic / underline / links / literal backticks
# --------------------------------------------------------------------------

_INLINE_TOKEN_RE = re.compile(
    r"""
    (?P<img>   !\[(?P<img_alt>[^\]]*)\]\((?P<img_path>[^)]+)\)   ) |
    (?P<link>  \[(?P<link_text>[^\]]+)\]\((?P<link_url>[^)]+)\)  ) |
    (?P<bold>  \*\*(?P<bold_text>[^*]+)\*\*                      ) |
    (?P<under> (?<!\w)_(?P<under_text>[^_\n]+)_(?!\w)            ) |
    (?P<ital>  (?<!\*)\*(?P<ital_text>[^*\n]+)\*(?!\*)           )
    """,
    re.VERBOSE,
)


def escape_literal(text):
    """Escape characters that are meaningful to Micron if they show up in
    plain prose (currently just the backtick, which starts every Micron
    control sequence)."""
    return text.replace("`", r"\`")


def render_inline(text, image_markup_renderer):
    """Convert the inline Markdown formatting inside `text` (bold, italic,
    underline, links, and -- defensively -- inline images) into Micron
    control sequences, and escape any stray literal backticks in the
    surrounding prose.
    """
    out = []
    pos = 0
    for m in _INLINE_TOKEN_RE.finditer(text):
        start, end = m.span()
        if start > pos:
            out.append(escape_literal(text[pos:start]))

        if m.group("img"):
            out.append(image_markup_renderer(m.group("img_alt"), m.group("img_path")))
            pos = end
        elif m.group("link"):
            link_text = escape_literal(m.group("link_text"))
            link_url = m.group("link_url")
            out.append("`[{}`{}]`".format(link_text, link_url))
            # A closing backtick was just emitted as a "reset" token. If the
            # very next raw character is a literal ")" it would otherwise
            # read as the Micron "close image" sequence ( `) ), so escape it.
            if end < len(text) and text[end] == ")":
                out.append(r"\)")
                end += 1
            pos = end
        elif m.group("bold"):
            out.append("`!{}`!".format(escape_literal(m.group("bold_text"))))
            pos = end
        elif m.group("under"):
            out.append("`_{}`_".format(escape_literal(m.group("under_text"))))
            pos = end
        elif m.group("ital"):
            out.append("`*{}`*".format(escape_literal(m.group("ital_text"))))
            pos = end

    out.append(escape_literal(text[pos:]))
    return "".join(out)

def make_image_path_mapper(prefix, ext, remap):
    """Build a function that maps a Markdown image path (as a string) to
    the path that should be written into the Micron output (as a string).

    `prefix` is a PurePosixPath directory; `ext` is a file extension
    (without the leading dot) or "" to keep the original extension.
    """
    def mapper(path):
        source = PurePosixPath(path)
        if not remap:
            return str(source)
        filename = source.name
        if ext:
            filename = PurePosixPath(filename).with_suffix("." + ext.lstrip(".")).name
        return str(prefix / filename)
    return mapper


def make_image_markup_renderer(path_mapper):
    def render(alt, path):
        mapped = path_mapper(path)
        alt = escape_literal(alt.strip())
        return "`({}`w={}`a={}`:{})".format(alt, IMAGE_WIDTH, IMAGE_ALIGN, mapped)
    return render

_HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)$")
_BULLET_RE = re.compile(r"^[-*+]\s+(.*)$")
_IMAGE_LINE_RE = re.compile(r"^!\[[^\]]*\]\([^)]+\)$")
_BLOCKQUOTE_RE = re.compile(r"^>\s?(.*)$")
_BARE_BRACKET_NOTE_RE = re.compile(r"[ \t]?\[[^\[\]]*\](?!\()")
_HTML_COMMENT_RE = re.compile(r"<!--.*?-->", re.DOTALL)


def strip_comments_and_notes(content):
    content = _HTML_COMMENT_RE.sub("", content)
    content = _BARE_BRACKET_NOTE_RE.sub("", content)
    return content


def parse_blocks(content):
    lines = content.split("\n")
    n = len(lines)
    i = 0
    blocks = []

    while i < n:
        raw = lines[i]
        stripped = raw.strip()

        if stripped == "":
            i += 1
            continue

        m = _HEADING_RE.match(stripped)
        if m:
            level = len(m.group(1))
            text = m.group(2).strip()
            blocks.append({"type": "heading", "level": level, "text": text})
            i += 1
            continue

        if stripped.startswith(">"):
            quote_lines = []
            while i < n and lines[i].strip().startswith(">"):
                qm = _BLOCKQUOTE_RE.match(lines[i].strip())
                quote_lines.append(qm.group(1).strip() if qm else "")
                i += 1
            blocks.append({"type": "blockquote", "text": " ".join(quote_lines).strip()})
            continue

        if _IMAGE_LINE_RE.match(stripped):
            images = [stripped]
            j = i + 1
            while True:
                k = j
                while k < n and lines[k].strip() == "":
                    k += 1
                if k < n and _IMAGE_LINE_RE.match(lines[k].strip()):
                    images.append(lines[k].strip())
                    j = k + 1
                else:
                    break
            blocks.append({"type": "image_group", "items": images})
            i = j
            continue

        bm = _BULLET_RE.match(stripped)
        if bm:
            text_lines = [bm.group(1).strip()]
            i += 1
            while i < n and lines[i].strip() != "" and not _is_block_start(lines[i].strip()):
                text_lines.append(lines[i].strip())
                i += 1
            blocks.append({"type": "bullet", "text": " ".join(text_lines).strip()})
            continue

        # plain paragraph: preserve original line breaks (no reflow)
        para_lines = [raw.rstrip()]
        i += 1
        while i < n and lines[i].strip() != "" and not _is_block_start(lines[i].strip()):
            para_lines.append(lines[i].rstrip())
            i += 1
        blocks.append({"type": "paragraph", "lines": para_lines})

    return blocks


def _is_block_start(stripped_line):
    return bool(
        _HEADING_RE.match(stripped_line)
        or stripped_line.startswith(">")
        or _BULLET_RE.match(stripped_line)
        or _IMAGE_LINE_RE.match(stripped_line)
    )


def render_heading(block, title_color, section_color, image_markup_renderer):
    level = min(block["level"], 3)
    marker = ">" * level
    color = title_color if level == 1 else section_color
    text = render_inline(block["text"], image_markup_renderer)
    return ["{} `c`F{}{}`f".format(marker, color, text), "`a"]


def render_blockquote(block, image_markup_renderer):
    return [render_inline(block["text"], image_markup_renderer)]


def render_bullet(block, image_markup_renderer):
    text = render_inline(block["text"], image_markup_renderer)
    return ["{} {}".format(BULLET_GLYPH, text)]


def render_image_group(block, image_markup_renderer):
    lines = []
    for item in block["items"]:
        m = re.match(r"^!\[([^\]]*)\]\(([^)]+)\)$", item)
        assert m is not None
        alt, path = m.group(1), m.group(2)
        lines.append(image_markup_renderer(alt, path))
    return lines


def render_paragraph(block, image_markup_renderer):
    joined = " ".join(l.strip() for l in block["lines"]).strip()
    if joined.startswith("Caption:"):
        text = render_inline(joined, image_markup_renderer)
        return ["`c" + text, "`a"]
    return [render_inline(l, image_markup_renderer) for l in block["lines"]]


def render_document(blocks, image_markup_renderer, title_color, section_color):
    out_lines = []
    glue_next = False  # True right after a heading: no blank line before next block

    for block in blocks:
        if block["type"] == "heading":
            rendered = render_heading(block, title_color, section_color, image_markup_renderer)
            this_glues_next = True
        elif block["type"] == "blockquote":
            rendered = render_blockquote(block, image_markup_renderer)
            this_glues_next = False
        elif block["type"] == "bullet":
            rendered = render_bullet(block, image_markup_renderer)
            this_glues_next = False
        elif block["type"] == "image_group":
            rendered = render_image_group(block, image_markup_renderer)
            this_glues_next = False
        elif block["type"] == "paragraph":
            rendered = render_paragraph(block, image_markup_renderer)
            this_glues_next = False
        else:
            rendered = []
            this_glues_next = False

        if out_lines and not glue_next:
            out_lines.append("")

        out_lines.extend(rendered)
        glue_next = this_glues_next

    return "\n".join(out_lines).rstrip("\n") + "\n"


def convert(content, image_markup_renderer, title_color, section_color):
    """Convert Markdown source text to Micron output text."""
    content = strip_comments_and_notes(content)
    blocks = parse_blocks(content)
    return render_document(blocks, image_markup_renderer, title_color, section_color)

@click.command(context_settings={"help_option_names": ["-h", "--help"]})
@click.argument(
    "input_path",
    type=click.Path(exists=True, dir_okay=False, readable=True, path_type=Path),
)
@click.option(
    "-o", "--output", "output_path",
    type=click.Path(dir_okay=False, path_type=Path),
    default=None,
    help="Path to write the .mu file to (default: same name as INPUT_PATH, "
         "with a .mu extension).",
)
@click.option(
    "--image-prefix",
    default=str(DEFAULT_IMAGE_PREFIX),
    show_default=True,
    help="Directory prefix used to rewrite image paths.",
)
@click.option(
    "--image-ext",
    default=DEFAULT_IMAGE_EXT,
    show_default=True,
    help="File extension to rewrite images to, without the dot. Pass an "
         "empty string to keep each image's original extension.",
)
@click.option(
    "--no-image-remap", is_flag=True,
    help="Leave image paths exactly as written in the Markdown source "
         "instead of remapping directory/extension.",
)
@click.option(
    "--title-color",
    default=TITLE_COLOR,
    show_default=True,
    help="3-digit hex color for the level-1 heading.",
)
@click.option(
    "--section-color",
    default=SECTION_COLOR,
    show_default=True,
    help="3-digit hex color for level-2/3 headings.",
)
def main(input_path, output_path, image_prefix, image_ext, no_image_remap,
         title_color, section_color):
    """Convert INPUT_PATH, a Markdown (.md) file, into a Micron (.mu) file."""
    content = input_path.read_text(encoding="utf-8")

    path_mapper = make_image_path_mapper(
        PurePosixPath(image_prefix), image_ext, remap=not no_image_remap
    )
    image_markup_renderer = make_image_markup_renderer(path_mapper)

    output = convert(content, image_markup_renderer, title_color, section_color)

    if output_path is None:
        output_path = input_path.with_suffix(".mu")

    output_path.write_text(output, encoding="utf-8")

    click.echo(f"Wrote {output_path}", err=True)


if __name__ == "__main__":
    main() # pragma: no cover