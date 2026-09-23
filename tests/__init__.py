from pathlib import Path

import md2mu as mu

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"

def default_renderer():
    """An image-markup renderer using the script's built-in defaults
    (remap on, DEFAULT_IMAGE_PREFIX / DEFAULT_IMAGE_EXT)."""
    mapper = mu.make_image_path_mapper(mu.DEFAULT_IMAGE_PREFIX, mu.DEFAULT_IMAGE_EXT, remap=True)
    return mu.make_image_markup_renderer(mapper)

def render(text):
    return mu.render_inline(text, default_renderer())
