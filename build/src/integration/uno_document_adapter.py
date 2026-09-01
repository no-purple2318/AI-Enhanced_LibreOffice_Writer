"""Adapter converting LibreOffice UNO XTextDocument structures into domain Document models."""

import os
from datetime import datetime
from typing import Any, List, Optional

from src.models.document import Document, Formatting, Heading, Paragraph
from src.utils.logging import get_logger

logger = get_logger("ai_writer.uno_adapter")


class UNODocumentAdapter:
    """Extracts text, paragraphs, headings, and formatting from a LibreOffice UNO XTextDocument."""

    @classmethod
    def to_domain_document(cls, x_text_document: Any) -> Optional[Document]:
        """Convert a live UNO XTextDocument component into our domain Document model."""
        if not x_text_document:
            return None

        try:
            # Extract basic document metadata
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

            # Enumerate paragraphs through XEnumerationAccess
            x_text = x_text_document.getText()
            enum = x_text.createEnumeration()

            p_id = 0
            while enum.hasMoreElements():
                elem = enum.nextElement()
                # Check if it supports Paragraph service
                if hasattr(elem, "supportsService") and elem.supportsService("com.sun.star.text.Paragraph"):
                    p_text = elem.getString()
                    p_style = "Standard"
                    if hasattr(elem, "ParaStyleName"):
                        p_style = elem.ParaStyleName

                    # Extract paragraph & character formatting
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

                    # Detect Headings
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

                    char_offset += p_len + 1  # include newline
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
                # 150 = BOLD in LibreOffice (com.sun.star.awt.FontWeight.BOLD = 150)
                fmt.bold = float(uno_element.CharWeight) > 100.0
            if hasattr(uno_element, "CharPosture"):
                # com.sun.star.awt.FontSlant.ITALIC = 2
                fmt.italic = int(uno_element.CharPosture) > 0
            if hasattr(uno_element, "CharUnderline"):
                # com.sun.star.awt.FontUnderline.NONE = 0
                fmt.underline = int(uno_element.CharUnderline) > 0
            if hasattr(uno_element, "ParaAdjust"):
                # 0: LEFT, 1: RIGHT, 2: BLOCK/JUSTIFIED, 3: CENTER
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
