"""MEBDF Serializer - Convert AST back to MEBDF markdown string.

This module converts the AST produced by MebdfParser back into
valid MEBDF markdown text.
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


class MebdfSerializer:
    """Serialize AST back to MEBDF markdown string."""

    def serialize(self, document: DocumentNode) -> str:
        """Serialize AST back to MEBDF string.

        Args:
            document: Root document node.

        Returns:
            MEBDF markdown string.
        """
        parts: list[str] = []

        for child in document.children:
            result = self._serialize_node(child)
            if result:
                parts.append(result)

        return "\n\n".join(parts)

    def _serialize_node(self, node) -> str:
        """Serialize a single AST node."""
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
            if node.anchor_id is None:
                return "{^}"
            return f"{{^ {node.anchor_id}}}"

        elif isinstance(node, EmbeddedObjectNode):
            if node.object_id is None:
                return f"{{^= {node.object_type}}}"
            return f"{{^= {node.object_id} {node.object_type}}}"

        elif isinstance(node, FormattingNode):
            props = self._serialize_properties(node.properties)
            inner = self._serialize_inline_list(node.content)
            return f"{{!{props}}}{inner}{{/!}}"

        elif isinstance(node, BlockFormattingNode):
            props = self._serialize_properties(node.properties)
            return f"{{!{props}}}"

        elif isinstance(node, HeadingNode):
            prefix = "#" * node.level
            anchor = f"{{^ {node.anchor_id}}}" if node.anchor_id else ""
            content = self._serialize_inline_list(node.content)
            if anchor:
                return f"{prefix} {anchor}{content}"
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
        parts: list[str] = []
        for node in nodes:
            parts.append(self._serialize_node(node))
        return "".join(parts)

    def _serialize_properties(self, properties: dict[str, str | bool]) -> str:
        """Serialize formatting properties to string."""
        parts: list[str] = []
        for key, value in properties.items():
            if value is True:
                parts.append(key)
            elif value is False:
                parts.append(f"{key}:false")
            else:
                parts.append(f"{key}:{value}")
        return ", ".join(parts)
