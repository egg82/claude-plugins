# Confluence publishing: mechanics and gotchas

Atlassian-converter behaviour, not site-specific.

## Silent content loss in the markdown converter

- **Blank line before AND after every fenced code block.** The converter drops the text immediately after a closing
  fence when no blank line follows; whole sentences vanished. Author the repo markdown this way too.
- **It eats the space between bold text and a following link or inline code.** `**Label:** [text](url)` becomes
  `<strong>Label:</strong><a ...>` and renders "Label:text". Read the storage back after every create and fix
  `</strong><a` to `</strong> <a` (same for `</strong><code>`).
- **In-page `#slug` links resolve to nothing.** Headings get ids of the form `<PageTitle>-<HeadingNoSpaces>`. Convert each to
  `<ac:link ac:anchor="The fix"><ac:plain-text-link-body><![CDATA[jump to the fix]]></ac:plain-text-link-body></ac:link>`
  (anchor = the heading text) and check `body.view`: the rendered `href` should match a heading `id`.
- The converter flattens nested bullets under a list item and restarts numbered lists split by an image or fence. Fix in storage.
- It mangles `<ac:image>` into a plain `<img src="filename">`. An attachment on the same page still resolves; an image from another page does not,
  and cross-page refs cannot be verified through the MCP (the markdown read-back shows a bare filename either way): spot-check in a browser.

## Layout

- One paragraph = one line (Confluence reflows; hard-wrapped paragraphs risk odd conversion).
- Strip the leading `# Title` when publishing (the title renders itself) and any `[[_TOC_]]` line (literal text in Confluence).
  A section inside a larger page starts at H2.
- The table of contents is the `toc` macro, storage format only:
  `<ac:structured-macro ac:name="toc" ac:schema-version="1"><ac:parameter ac:name="maxLevel">2</ac:parameter></ac:structured-macro>`.
  A landing page can list its children with the `children` macro instead of a hand-kept list.

## Publish recipe

1. `confluence_create_page` with `content_format: markdown`, body = draft minus the H1 and TOC line.
2. `confluence_get_page` with `convert_to_markdown: false` to read the storage, then `confluence_update_page` with
   `content_format: storage`, inserting the `toc` macro after the intro. **Updates replace the whole body**, so keep the local `.md`
   authoritative and re-derive. A read-back with `convert_to_markdown: true` shows code macros as `Defaultbash...`: that is
   re-serialization, not the page.
- Hand-authored code macro: `<ac:structured-macro ac:name="code" ac:schema-version="1"><ac:parameter ac:name="language">bash</ac:parameter><ac:plain-text-body><![CDATA[ ... ]]></ac:plain-text-body></ac:structured-macro>`;
  literal characters inside CDATA, `&lt; &gt; &amp;` in ordinary text, `language: none` for non-shell blocks.
- **Long opaque strings (a multi-KB URL, a token-like query): edit through the REST API, not by retyping.** A storage update
  re-sends the whole body and one wrong character is invisible on review. Script it: GET `/rest/api/content/<id>?expand=body.storage,version`,
  save a snapshot, apply assert-exactly-once replacements, PUT with `version+1`, GET again and compare each long value to its source
  byte for byte. Read credentials inside the script; never print them.

## Placement

- `confluence_get_page` returns no ancestors: use REST `GET /rest/api/content/<id>?expand=ancestors` (last entry is the parent).
  `confluence_get_space_page_tree` can fail on a large space with `'<' not supported between instances of 'int' and 'str'`.
- Order with `confluence_move_page` (`position: above/below/append`); cross-link related pages by `viewpage.action?pageId=` URL in both directions.
- **Write access is not ownership.** Edit a page only if it is in your own area or you created or fully rewrote it; for anyone
  else's page draft the change for its owner.

## Attachments (the MCP cannot upload)

- `confluence_upload_attachment` returns a generic "Failed to upload attachment" (sometimes wrapped in "uploaded successfully") for a
  hosted connector (no shared filesystem) and for a LOCAL `mcp-atlassian` alike; it is neither path nor size. Use the REST API with the
  same credential, `POST /rest/api/content/<id>/child/attachment`, multipart `file=@...`, header `X-Atlassian-Token` set to `nocheck`.
  Re-uploading a filename returns 400; a new version goes to `.../child/attachment/<attachment-id>/data`.
  Pass the token via a mode-0600 curl `--config` file written by a script and deleted on exit, never on argv or screen.
- Embed video with the `multimedia` macro (`<ri:attachment ri:filename="..."/>` in its `name` parameter) and confirm `body.view` renders a `<video>` tag.
