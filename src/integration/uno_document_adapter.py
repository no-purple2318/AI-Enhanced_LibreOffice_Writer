"""Adapter converting LibreOffice UNO XTextDocument structures and ODT files into domain Document models."""

import os
import xml.etree.ElementTree as ET
import zipfile
from datetime import datetime
from typing import Any, List, Optional

from src.models.document import Document, Formatting, Heading, Paragraph
from src.utils.logging import get_logger

logger = get_logger("ai_writer.uno_adapter")


class UNODocumentAdapter:
    """Extracts text, paragraphs, headings, and formatting from a LibreOffice UNO XTextDocument or .odt file."""

    @classmethod
    def to_domain_document(cls, x_text_document: Any) -> Optional[Document]:
        """Convert a live UNO XTextDocument component into our domain Document model."""
        if not x_text_document:
            return None

        try:
            file_name = "Untitled.odt"
            file_path = ""
            if hasattr(x_text_document, "hasLocation") and x_text_document.hasLocation():
                url = x_text_document.getLocation()
                file_path = url.replace("file://", "")
                file_name = os.path.basename(file_path)

            doc = Document(
                fileName=file_name,
                filePath=file_path,
                fileType="odt",
                uno_component=x_text_document,
            )

            paragraphs: List[Paragraph] = []
            headings: List[Heading] = []
            char_offset = 0

            x_text = x_text_document.getText()
            enum = x_text.createEnumeration()

            p_id = 0
            while enum.hasMoreElements():
                elem = enum.nextElement()
                if hasattr(elem, "supportsService") and elem.supportsService("com.sun.star.text.Paragraph"):
                    p_text = elem.getString()
                    p_style = "Standard"
                    if hasattr(elem, "ParaStyleName"):
                        p_style = elem.ParaStyleName

                    formatting = cls._extract_formatting(elem)
                    p_len = len(p_text)
                    paragraph_obj = Paragraph(
                        id=p_id,
                        text=p_text,
                        startPosition=char_offset,
                        endPosition=char_offset + p_len,
                        style=p_style,
                        formatting=formatting,
                        uno_paragraph_ref=elem,
                    )
                    paragraphs.append(paragraph_obj)

                    if "Heading" in p_style or "Title" in p_style:
                        level = 1
                        for digit in p_style:
                            if digit.isdigit():
                                level = int(digit)
                                break
                        heading_obj = Heading(
                            id=p_id,
                            text=p_text,
                            level=level,
                            position=char_offset,
                            formatting=formatting,
                        )
                        headings.append(heading_obj)

                    char_offset += p_len + 1
                    p_id += 1

            doc.paragraphs = paragraphs
            doc.headings = headings
            doc.create_revision()
            return doc

        except Exception as e:
            logger.error(f"Error adapting UNO document: {e}", exc_info=True)
            return None

    @classmethod
    def _extract_formatting(cls, uno_element: Any) -> Formatting:
        """Extract font, size, weight, and layout formatting from UNO element."""
        fmt = Formatting()
        try:
            if hasattr(uno_element, "CharFontName"):
                fmt.fontFamily = str(uno_element.CharFontName)
            if hasattr(uno_element, "CharHeight"):
                fmt.fontSize = float(uno_element.CharHeight)
            if hasattr(uno_element, "CharWeight"):
                fmt.bold = float(uno_element.CharWeight) > 100.0
            if hasattr(uno_element, "CharPosture"):
                fmt.italic = int(uno_element.CharPosture) > 0
            if hasattr(uno_element, "CharUnderline"):
                fmt.underline = int(uno_element.CharUnderline) > 0
            if hasattr(uno_element, "ParaAdjust"):
                adjust_map = {0: "LEFT", 1: "RIGHT", 2: "BLOCK", 3: "CENTER"}
                fmt.alignment = adjust_map.get(int(uno_element.ParaAdjust), "LEFT")
            if hasattr(uno_element, "ParaTopMargin"):
                fmt.spacingBefore = float(uno_element.ParaTopMargin) / 100.0
            if hasattr(uno_element, "ParaBottomMargin"):
                fmt.spacingAfter = float(uno_element.ParaBottomMargin) / 100.0
        except Exception as e:
            logger.debug(f"Could not read all formatting properties: {e}")
        return fmt

    @classmethod
    def from_odt_file(cls, file_path: str) -> Optional[Document]:
        """Extract text, paragraphs, headings, and formatting directly from an .odt archive."""
        if not os.path.exists(file_path):
            logger.error(f"ODT file not found: {file_path}")
            return None

        try:
            with zipfile.ZipFile(file_path, "r") as zf:
                if "content.xml" not in zf.namelist():
                    logger.error("Invalid ODT archive: missing content.xml")
                    return None
                content_xml = zf.read("content.xml")

            root = ET.fromstring(content_xml)
            ns = {
                "text": "urn:oasis:names:tc:opendocument:xmlns:text:1.0",
                "office": "urn:oasis:names:tc:opendocument:xmlns:office:1.0",
                "style": "urn:oasis:names:tc:opendocument:xmlns:style:1.0",
            }

            doc = Document(
                fileName=os.path.basename(file_path),
                filePath=file_path,
                fileType="odt",
            )

            paragraphs: List[Paragraph] = []
            headings: List[Heading] = []
            char_offset = 0
            p_id = 0

            body = root.find(".//office:body/office:text", ns)
            if body is not None:
                for elem in body:
                    tag = elem.tag.split("}")[-1] if "}" in elem.tag else elem.tag
                    if tag in ("p", "h"):
                        p_text = "".join(elem.itertext()).strip()
                        if not p_text:
                            continue

                        style_name = elem.attrib.get(f"{{{ns['text']}}}style-name", "Standard")
                        level = 1
                        if tag == "h":
                            level_attr = elem.attrib.get(f"{{{ns['text']}}}outline-level", "1")
                            level = int(level_attr) if level_attr.isdigit() else 1
                            style_name = f"Heading {level}"

                        p_len = len(p_text)
                        paragraph_obj = Paragraph(
                            id=p_id,
                            text=p_text,
                            startPosition=char_offset,
                            endPosition=char_offset + p_len,
                            style=style_name,
                            formatting=Formatting(),
                        )
                        paragraphs.append(paragraph_obj)

                        if tag == "h" or "Heading" in style_name or "Title" in style_name:
                            heading_obj = Heading(
                                id=p_id,
                                text=p_text,
                                level=level,
                                position=char_offset,
                                formatting=Formatting(bold=True),
                            )
                            headings.append(heading_obj)

                        char_offset += p_len + 1
                        p_id += 1

            doc.paragraphs = paragraphs
            doc.headings = headings
            doc.create_revision()
            return doc

        except Exception as e:
            logger.error(f"Error parsing ODT file {file_path}: {e}")
            return None

    @classmethod
    def from_plain_text(
        cls, text: str, fileName: str = "Sample.odt"
    ) -> Document:
        """Create a synthetic domain Document from plain text string for testing and simulation."""
        doc = Document(fileName=fileName, fileType="odt", raw_text=text)
        paragraphs: List[Paragraph] = []
        headings: List[Heading] = []

        lines = text.split("\n")
        offset = 0
        for idx, line in enumerate(lines):
            line_len = len(line)
            style = "Standard"
            if line.startswith("# "):
                style = "Heading 1"
                headings.append(
                    Heading(
                        id=idx,
                        text=line[2:],
                        level=1,
                        position=offset,
                        formatting=Formatting(fontSize=16.0, bold=True),
                    )
                )
            elif line.startswith("## "):
                style = "Heading 2"
                headings.append(
                    Heading(
                        id=idx,
                        text=line[3:],
                        level=2,
                        position=offset,
                        formatting=Formatting(fontSize=14.0, bold=True),
                    )
                )

            p = Paragraph(
                id=idx,
                text=line,
                startPosition=offset,
                endPosition=offset + line_len,
                style=style,
                formatting=Formatting(),
            )
            paragraphs.append(p)
            offset += line_len + 1

        doc.paragraphs = paragraphs
        doc.headings = headings
        doc.create_revision()
        return doc

