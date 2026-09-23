# md2mu
A custom Markdown to Micron converter for Colorado Mesh newsletters

## Getting Started

- Install [uv](https://docs.astral.sh/uv/getting-started/installation/)
- Run `uv sync` to install dependencies
- Run `md2mu` with `uv run md2mu`

## Usage

```
Usage: md2mu [OPTIONS] INPUT_PATH

  Convert INPUT_PATH, a Markdown (.md) file, into a Micron (.mu) file.

Options:
  -o, --output FILE     Path to write the .mu file to (default: same name as
                        INPUT_PATH, with a .mu extension).
  --image-prefix TEXT   Directory prefix used to rewrite image paths.
                        [default: /media/cmesh-blog/img]
  --image-ext TEXT      File extension to rewrite images to, without the dot.
                        Pass an empty string to keep each image's original
                        extension.  [default: webp]
  --no-image-remap      Leave image paths exactly as written in the Markdown
                        source instead of remapping directory/extension.
  --title-color TEXT    3-digit hex color for the level-1 heading.  [default:
                        000]
  --section-color TEXT  3-digit hex color for level-2/3 headings.  [default:
                        8f0]
  -h, --help            Show this message and exit.
```