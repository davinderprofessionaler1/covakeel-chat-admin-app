"""Export a saved, source-cited answer without another model call."""

from datetime import datetime, timezone
from html import escape
from io import BytesIO
import re
from urllib.parse import urlparse
from xml.sax.saxutils import escape as xml_escape
from zipfile import ZIP_DEFLATED, ZipFile
from zoneinfo import ZoneInfo

import fitz


def _source_rows(sources):
    rows = {}
    for source in sources:
        metadata = source.metadata or {}
        citation = str(metadata.get("citation_id") or len(rows) + 1)
        row = rows.setdefault(citation, {
            "number": citation,
            "title": metadata.get("title") or source.filename or "Library document",
            "filename": source.filename or metadata.get("filename") or "",
            "pages": set(),
            "url": "",
        })
        if metadata.get("page"):
            row["pages"].add(str(metadata["page"]))
        url = metadata.get("source_url") or ""
        parsed = urlparse(url)
        if parsed.scheme == "https" and parsed.netloc and not parsed.username and not parsed.password:
            row["url"] = url
    return [rows[key] for key in sorted(rows, key=lambda value: (not value.isdigit(), int(value) if value.isdigit() else value))]


def _inline_html(value, source_urls):
    """Render safe inline emphasis and link citations to actual source URLs."""
    safe = escape(value.strip())
    safe = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", safe)
    safe = re.sub(r"\*([^*]+)\*", r"<em>\1</em>", safe)

    def cite(match):
        number = match.group(1)
        url = source_urls.get(number)
        label = f"[{number}]"
        return f'<a href="{escape(url, quote=True)}">{label}</a>' if url else label

    return re.sub(r"\[(\d+)\]", cite, safe)


def _html_answer(text, rows):
    source_urls = {row["number"]: row["url"] for row in rows if row["url"]}
    output = []
    for block in re.split(r"\n\s*\n", text.strip()):
        lines = [line.strip() for line in block.splitlines() if line.strip()]
        if not lines:
            continue
        if len(lines) == 1 and re.fullmatch(r"-{3,}|_{3,}", lines[0]):
            output.append("<hr>")
            continue
        if all(line.startswith(">") for line in lines):
            output.append("<blockquote>" + "<br>".join(_inline_html(line.lstrip("> "), source_urls) for line in lines) + "</blockquote>")
            continue
        if len(lines) == 1:
            line = lines[0]
            if line.startswith("#") or (line.startswith("**") and line.endswith("**") and len(line) > 4):
                heading = re.sub(r"^#{1,4}\s+|^\*\*|\*\*$", "", line)
                output.append(f"<h2>{_inline_html(heading, source_urls)}</h2>")
                continue
        unordered = [re.match(r"^(?:[-*•])\s+(.+)$", line) for line in lines]
        numbered = [re.match(r"^\d+[.)]\s+(.+)$", line) for line in lines]
        if all(unordered):
            output.append("<ul>" + "".join(f"<li>{_inline_html(m.group(1), source_urls)}</li>" for m in unordered) + "</ul>")
        elif all(numbered):
            output.append("<ol>" + "".join(f"<li>{_inline_html(m.group(1), source_urls)}</li>" for m in numbered) + "</ol>")
        elif len(lines) >= 2 and all(line.startswith("|") and line.endswith("|") for line in lines):
            table_rows = []
            for index, line in enumerate(lines):
                cells = [cell.strip() for cell in line.strip("|").split("|")]
                if all(re.fullmatch(r":?-{3,}:?", cell) for cell in cells):
                    continue
                tag = "th" if index == 0 else "td"
                table_rows.append("<tr>" + "".join(f"<{tag}>{_inline_html(cell, source_urls)}</{tag}>" for cell in cells) + "</tr>")
            output.append("<table>" + "".join(table_rows) + "</table>")
        else:
            output.append("<p>" + "<br>".join(_inline_html(line, source_urls) for line in lines) + "</p>")
    return "\n".join(output)


def export_pdf(answer, sources, question=None, generated_at=None):
    rows = _source_rows(sources)
    query = f'<section class="query"><h2>Query</h2><p>{escape(question)}</p></section>' if question else ""
    html = query + '<section class="response"><h2>Response</h2>' + _html_answer(answer, rows) + "</section>"
    if rows:
        html += '<section class="sources"><h2>Cited sources</h2>'
        for row in rows:
            details = f'<strong>{escape(str(row["title"]))}</strong>'
            if row["pages"]:
                pages = ", ".join(sorted(row["pages"], key=lambda p: int(p) if p.isdigit() else p))
                details += "<br>Page " + escape(pages)
            if row["url"]:
                details += ' · <a href="' + escape(row["url"], quote=True) + '">Open official document</a>'
            elif row["filename"]:
                details += " · " + escape(row["filename"])
            html += '<p class="source-item"><span class="source-number">[' + escape(row["number"]) + "]</span> " + details + "</p>"
        html += "</section>"
    css = """
        body { font-family: sans-serif; font-size: 10.5pt; color: #17372c; }
        h2 { font-size: 14pt; color: #17372c; margin: 0 0 11pt; }
        section.query { margin: 0 0 23pt; }
        section.query h2, section.response > h2, section.sources h2 {
            border-bottom: 1pt solid #d7ba74; padding-bottom: 7pt; margin-bottom: 14pt;
        }
        section.response h2 { font-size: 11.5pt; margin: 15pt 0 7pt; }
        section.response > h2 { font-size: 14pt; margin: 0 0 14pt; }
        p { line-height: 1.48; margin: 0 0 11pt; }
        ul, ol { margin: 0 0 12pt 17pt; padding: 0; }
        li { line-height: 1.43; margin: 0 0 6pt; }
        a { color: #855d12; text-decoration: underline; }
        table { border-collapse: collapse; margin: 6pt 0 12pt; width: 100%; font-size: 9.5pt; }
        th, td { border: .5pt solid #cbd5ce; padding: 5pt; text-align: left; }
        th { background: #e9ede7; }
        section.sources { margin-top: 20pt; }
        section.sources .source-item { margin-bottom: 9pt; }
        .source-number { color: #855d12; }
        hr { border: 0; border-top: .7pt solid #d7ba74; margin: 13pt 0; }
        blockquote { border-left: 2pt solid #d7ba74; margin: 10pt 0; padding-left: 10pt; }
    """
    story = fitz.Story(html, user_css=css)
    page_size = fitz.Rect(0, 0, 595, 842)

    def page_rect(_number, _filled):
        return page_size, fitz.Rect(48, 74, 547, 755), fitz.Identity

    document = story.write_with_links(page_rect)
    try:
        now = generated_at or datetime.now(timezone.utc)
        if now.tzinfo is None:
            now = now.replace(tzinfo=timezone.utc)
        stamp = now.astimezone(ZoneInfo("Asia/Kolkata")).strftime("%d %b %Y, %I:%M %p IST")
        for index, page in enumerate(document):
            page.insert_text((48, 43), "CoVakeel", fontsize=15, fontname="hebo", color=(0.10, 0.24, 0.19))
            page.insert_text((454, 42), "LEGAL RESEARCH", fontsize=7.5, fontname="hebo", color=(0.58, 0.41, 0.16))
            page.draw_line((48, 53), (547, 53), color=(0.82, 0.72, 0.48), width=0.8)
            page.draw_line((48, 775), (547, 775), color=(0.82, 0.72, 0.48), width=0.6)
            page.insert_text((48, 790), f"Downloaded {stamp}", fontsize=8, color=(0.33, 0.42, 0.37))
            page.insert_text((515, 790), f"{index + 1} / {len(document)}", fontsize=8, color=(0.33, 0.42, 0.37))
            page.insert_text((48, 804), "AI research aid. Verify the cited law and effective date before relying on this answer.", fontsize=7.2, color=(0.33, 0.42, 0.37))
        document.set_metadata({"title": "CoVakeel legal research answer", "creator": "CoVakeel"})
        return document.tobytes()
    finally:
        document.close()


def _docx_paragraph(value, bold=False):
    runs = []
    for index, part in enumerate(re.split(r"\*\*([^*]+)\*\*", value)):
        if not part:
            continue
        runs.append(
            "<w:r>" + ("<w:rPr><w:b/></w:rPr>" if bold or index % 2 else "")
            + '<w:t xml:space="preserve">' + xml_escape(part) + "</w:t></w:r>"
        )
    return "<w:p>" + "".join(runs) + "</w:p>"


def export_docx(answer, sources):
    paragraphs = [_docx_paragraph("CoVakeel answer", bold=True)]
    for line in answer.splitlines():
        paragraphs.append(_docx_paragraph(line))
    rows = _source_rows(sources)
    if rows:
        paragraphs.append(_docx_paragraph("Cited sources", bold=True))
        for row in rows:
            details = f"[{row['number']}] {row['title']}"
            if row["pages"]:
                details += " — page " + ", ".join(sorted(row["pages"], key=lambda p: int(p) if p.isdigit() else p))
            if row["url"]:
                details += " — " + row["url"]
            paragraphs.append(_docx_paragraph(details))
    document = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
        "<w:body>" + "".join(paragraphs) + "<w:sectPr/></w:body></w:document>"
    )
    output = BytesIO()
    with ZipFile(output, "w", ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", '<?xml version="1.0" encoding="UTF-8"?>'
            '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
            '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
            '<Default Extension="xml" ContentType="application/xml"/>'
            '<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
            '</Types>')
        archive.writestr("_rels/.rels", '<?xml version="1.0" encoding="UTF-8"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>'
            '</Relationships>')
        archive.writestr("word/document.xml", document)
    return output.getvalue()
