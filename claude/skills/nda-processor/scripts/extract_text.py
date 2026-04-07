#!/usr/bin/env python
"""
Extract plain text from a DOCX document.xml file.

Usage:
    python extract_text.py <path-to-document.xml>

Reads the Word XML, extracts text from all <w:t> elements, and prints
plain text with paragraph breaks. This avoids loading verbose XML into
LLM context -- only the human-readable text matters for NDA review.

Handles:
- Regular text runs (<w:t> inside <w:r> inside <w:p>)
- Tab characters (<w:tab/>) rendered as tab stops
- Line breaks within paragraphs (<w:br/>)
- Deleted text in tracked changes (skipped -- extracts current text only)
- Unicode entities (&#x201C; etc.) resolved by the XML parser

Does NOT handle:
- Images, charts, embedded objects
- Table cell boundaries (text from tables flows as paragraphs)
- Comments (extracts document body text only)
"""

import sys
import xml.etree.ElementTree as ET


# Word ML namespace
W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"


def extract_text(xml_path: str) -> str:
    """Extract all text from a DOCX document.xml file.

    Args:
        xml_path: Path to the unpacked word/document.xml

    Returns:
        Plain text with paragraphs separated by blank lines.
    """
    tree = ET.parse(xml_path)
    root = tree.getroot()

    paragraphs = []

    for p_elem in root.iter(f"{{{W_NS}}}p"):
        runs_text = []

        # Skip text inside <w:del> elements (tracked deletions)
        del_elements = set()
        for del_elem in p_elem.iter(f"{{{W_NS}}}del"):
            del_elements.add(del_elem)

        for child in p_elem.iter():
            # Check if this element is inside a deletion
            skip = False
            for del_elem in del_elements:
                if _is_descendant(child, del_elem):
                    skip = True
                    break
            if skip:
                continue

            # Text content
            if child.tag == f"{{{W_NS}}}t":
                if child.text:
                    runs_text.append(child.text)
            # Tab stop
            elif child.tag == f"{{{W_NS}}}tab":
                runs_text.append("\t")
            # Line break within paragraph
            elif child.tag == f"{{{W_NS}}}br":
                runs_text.append("\n")

        line = "".join(runs_text).strip()
        if line:
            paragraphs.append(line)

    return "\n\n".join(paragraphs)


def _is_descendant(element, ancestor):
    """Check if element is a descendant of ancestor using a simple approach.

    Since ElementTree doesn't track parent references, we check by iterating
    the ancestor's descendants. This is O(n) per call but acceptable for
    the small number of <w:del> elements in typical NDAs.
    """
    if element is ancestor:
        return True
    for child in ancestor.iter():
        if child is element:
            return True
    return False


def main():
    if len(sys.argv) != 2:
        print("Usage: python extract_text.py <document.xml>", file=sys.stderr)
        sys.exit(1)

    xml_path = sys.argv[1]

    try:
        text = extract_text(xml_path)
    except FileNotFoundError:
        print(f"Error: File not found: {xml_path}", file=sys.stderr)
        sys.exit(1)
    except ET.ParseError as e:
        print(f"Error: Failed to parse XML: {e}", file=sys.stderr)
        sys.exit(1)

    print(text)


if __name__ == "__main__":
    main()
