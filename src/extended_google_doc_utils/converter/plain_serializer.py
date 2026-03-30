"""Plain Markdown Serializer - Convert AST to standard markdown without MEBDF markers.

This module converts the AST produced by MebdfParser into plain/standard
markdown, stripping all MEBDF-specific syntax ({!...}{/!}, {^ ...}, {^= ...}).
"""

from __future__ import annotations

from extended_google_doc_utils.converter.mebdf_parser import (
    AnchorNode,
    BlockFormattingNode,
    BoldNode,
    CodeBlockNode,
    CodeSpanNode,
    DocumentNode,
    EmbeddedObjectNode,
    FormattingNode,
    HeadingNode,
    ItalicNode,
    LinkNode,
    ListItemNode,
    ListNode,
    ParagraphNode,
    TextNode,
)


class PlainMarkdownSerializer:
    """Serialize AST to plain/standard markdown, stripping MEBDF markers."""

    def serialize(self, document: DocumentNode) -> str:
        """Serialize AST to plain markdown string.

        Args:
            document: Root document node.

        Returns:
            Plain markdown string with no MEBDF markers.
        """
        parts: list[str] = []

        for child in document.children:
            result = self._serialize_node(child)
            if result:
                parts.append(result)

        return "\n\n".join(parts)

    def _serialize_node(self, node) -> str:
        """Serialize a single AST node to plain markdown."""
        if isinstance(node, TextNode):
            return node.content

        elif isinstance(node, BoldNode):
            inner = self._serialize_inline_list(node.content)
            return f"**{inner}**"

        elif isinstance(node, ItalicNode):
            inner = self._serialize_inline_list(node.content)
            return f"*{inner}*"

        elif isinstance(node, CodeSpanNode):
            return f"`{node.content}`"

        elif isinstance(node, CodeBlockNode):
            lang = node.language or ""
            return f"```{lang}\n{node.content}\n```"

        elif isinstance(node, LinkNode):
            return f"[{node.text}]({node.url})"

        elif isinstance(node, AnchorNode):
            # Strip anchors entirely in plain markdown
            return ""

        elif isinstance(node, EmbeddedObjectNode):
            # Replace with placeholder
            return "[image]"

        elif isinstance(node, FormattingNode):
            # Strip MEBDF formatting wrapper, emit child text only
            return self._serialize_inline_list(node.content)

        elif isinstance(node, BlockFormattingNode):
            # Strip block formatting directives entirely
            return ""

        elif isinstance(node, HeadingNode):
            prefix = "#" * node.level
            # No anchor marker in plain markdown
            content = self._serialize_inline_list(node.content)
            return f"{prefix} {content}"

        elif isinstance(node, ParagraphNode):
            return self._serialize_inline_list(node.content)

        elif isinstance(node, ListNode):
            items: list[str] = []
            for i, item in enumerate(node.items):
                if isinstance(item, ListItemNode):
                    indent = "  " * item.indent_level
                    content = self._serialize_inline_list(item.content)
                    if node.ordered:
                        items.append(f"{indent}{i + 1}. {content}")
                    else:
                        items.append(f"{indent}- {content}")
            return "\n".join(items)

        elif isinstance(node, ListItemNode):
            # Shouldn't be called directly, but handle it
            content = self._serialize_inline_list(node.content)
            indent = "  " * node.indent_level
            return f"{indent}- {content}"

        return ""

    def _serialize_inline_list(self, nodes: list) -> str:
        """Serialize a list of inline nodes."""
        return "".join(self._serialize_node(node) for node in nodes)
