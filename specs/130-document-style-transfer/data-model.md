# Data Model: Document Style Transfer

**Feature**: 130-document-style-transfer
**Date**: 2026-01-19

## Entity Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                      DocumentStyles                              │
│  (Complete style snapshot of a document)                        │
├─────────────────────────────────────────────────────────────────┤
│  document_id: str                                               │
│  document_properties: DocumentProperties                        │
│  effective_styles: dict[NamedStyleType, EffectiveStyle]        │
└─────────────────────────────────────────────────────────────────┘
                              │
              ┌───────────────┴───────────────┐
              ▼                               ▼
┌─────────────────────────┐     ┌─────────────────────────────────┐
│  DocumentProperties     │     │  EffectiveStyle                  │
│  (Page-level settings)  │     │  (Visible style for a type)      │
├─────────────────────────┤     ├─────────────────────────────────┤
│  background_color: RGB? │     │  style_type: NamedStyleType      │
│  margin_top_pt: float?  │     │  text_style: TextStyleProperties │
│  margin_bottom_pt: float│     │  paragraph_style: ParaStyleProps │
│  margin_left_pt: float? │     │  source: StyleSource             │
│  margin_right_pt: float?│     └─────────────────────────────────┘
│  page_width_pt: float?  │                    │
│  page_height_pt: float? │         ┌──────────┴──────────┐
└─────────────────────────┘         ▼                     ▼
                          ┌─────────────────┐  ┌──────────────────┐
                          │TextStyleProps   │  │ParaStyleProps    │
                          ├─────────────────┤  ├──────────────────┤
                          │font_family: str?│  │alignment: str?   │
                          │font_size_pt:flt?│  │line_spacing: flt?│
                          │font_weight: int?│  │space_before_pt:? │
                          │text_color: RGB? │  │space_after_pt: ? │
                          │highlight: RGB?  │  │indent_start_pt:? │
                          │bold: bool?      │  │indent_end_pt: ?  │
                          │italic: bool?    │  │first_line_ind:?  │
                          │underline: bool? │  └──────────────────┘
                          └─────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                    StyleTransferOptions                          │
│  (Configuration for transfer operation)                          │
├─────────────────────────────────────────────────────────────────┤
│  include_document_properties: bool = True                        │
│  include_effective_styles: bool = True                           │
│  style_types: list[NamedStyleType]? = None  # None = all        │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                    StyleTransferResult                           │
│  (Summary of transfer operation)                                 │
├─────────────────────────────────────────────────────────────────┤
│  success: bool                                                   │
│  document_properties_applied: bool                               │
│  styles_applied: dict[NamedStyleType, StyleApplicationResult]   │
│  total_paragraphs_updated: int                                   │
│  errors: list[str]                                               │
└─────────────────────────────────────────────────────────────────┘
```

## Enumerations

### NamedStyleType

The 9 Google Docs named style types:

```python
class NamedStyleType(str, Enum):
    NORMAL_TEXT = "NORMAL_TEXT"
    TITLE = "TITLE"
    SUBTITLE = "SUBTITLE"
    HEADING_1 = "HEADING_1"
    HEADING_2 = "HEADING_2"
    HEADING_3 = "HEADING_3"
    HEADING_4 = "HEADING_4"
    HEADING_5 = "HEADING_5"
    HEADING_6 = "HEADING_6"
```

### StyleSource

Indicates where the effective style was derived from:

```python
class StyleSource(str, Enum):
    PARAGRAPH_SAMPLE = "paragraph_sample"    # From actual paragraph in document
    STYLE_DEFINITION = "style_definition"    # Fallback to named style definition
```

## Entity Definitions

### RGBColor

```python
@dataclass(frozen=True)
class RGBColor:
    """RGB color with values 0.0-1.0."""
    red: float
    green: float
    blue: float

    def to_hex(self) -> str:
        """Convert to hex string like '#FF0000'."""
        r = int(self.red * 255)
        g = int(self.green * 255)
        b = int(self.blue * 255)
        return f"#{r:02x}{g:02x}{b:02x}"

    @classmethod
    def from_hex(cls, hex_str: str) -> "RGBColor":
        """Parse hex string like '#FF0000' or 'FF0000'."""
        hex_str = hex_str.lstrip('#')
        r = int(hex_str[0:2], 16) / 255
        g = int(hex_str[2:4], 16) / 255
        b = int(hex_str[4:6], 16) / 255
        return cls(red=r, green=g, blue=b)
```

### TextStyleProperties

Character-level formatting properties (FR-012):

```python
@dataclass(frozen=True)
class TextStyleProperties:
    """Text-level style properties for a named style."""
    font_family: str | None = None
    font_size_pt: float | None = None
    font_weight: int | None = None      # 100-900, 400=normal, 700=bold
    text_color: RGBColor | None = None
    highlight_color: RGBColor | None = None
    bold: bool | None = None
    italic: bool | None = None
    underline: bool | None = None
```

### ParagraphStyleProperties

Block-level formatting properties (FR-013):

```python
@dataclass(frozen=True)
class ParagraphStyleProperties:
    """Paragraph-level style properties for a named style."""
    alignment: str | None = None         # START, CENTER, END, JUSTIFIED
    line_spacing: float | None = None    # Multiplier (1.0 = single, 1.5 = 1.5x)
    space_before_pt: float | None = None
    space_after_pt: float | None = None
    indent_start_pt: float | None = None
    indent_end_pt: float | None = None
    first_line_indent_pt: float | None = None
```

### EffectiveStyle

The resolved/visible style for a named style type:

```python
@dataclass(frozen=True)
class EffectiveStyle:
    """Effective (visible) style for a named style type.

    Captures what the user actually sees, not just the style definition.
    If paragraphs have consistent overrides, those overrides are captured.
    """
    style_type: NamedStyleType
    text_style: TextStyleProperties
    paragraph_style: ParagraphStyleProperties
    source: StyleSource  # Where this style came from
```

### DocumentProperties

Page-level document settings:

```python
@dataclass(frozen=True)
class DocumentProperties:
    """Document-level properties (page settings)."""
    background_color: RGBColor | None = None
    margin_top_pt: float | None = None
    margin_bottom_pt: float | None = None
    margin_left_pt: float | None = None
    margin_right_pt: float | None = None
    page_width_pt: float | None = None
    page_height_pt: float | None = None
```

### DocumentStyles

Complete style snapshot of a document:

```python
@dataclass(frozen=True)
class DocumentStyles:
    """Complete style information for a document.

    Contains document-level properties and effective styles for all 9
    named style types.
    """
    document_id: str
    document_properties: DocumentProperties
    effective_styles: dict[NamedStyleType, EffectiveStyle]

    def get_style(self, style_type: NamedStyleType) -> EffectiveStyle | None:
        """Get effective style for a specific type."""
        return self.effective_styles.get(style_type)
```

### StyleTransferOptions

Configuration for transfer operation (FR-019):

```python
@dataclass(frozen=True)
class StyleTransferOptions:
    """Options controlling what gets transferred."""
    include_document_properties: bool = True
    include_effective_styles: bool = True
    style_types: list[NamedStyleType] | None = None  # None = all 9 types
```

### StyleApplicationResult

Result for a single style type:

```python
@dataclass(frozen=True)
class StyleApplicationResult:
    """Result of applying one style type to target document."""
    style_type: NamedStyleType
    paragraphs_updated: int
    success: bool = True
    error: str | None = None
```

### StyleTransferResult

Complete transfer operation result (FR-020):

```python
@dataclass(frozen=True)
class StyleTransferResult:
    """Result of a style transfer operation."""
    success: bool
    document_properties_applied: bool
    styles_applied: dict[NamedStyleType, StyleApplicationResult]
    total_paragraphs_updated: int
    errors: list[str]
```

## Validation Rules

### RGBColor
- `red`, `green`, `blue` must be in range [0.0, 1.0]
- Hex conversion must handle 6-character strings

### TextStyleProperties
- `font_weight` must be in range [100, 900] when set
- `font_weight` typically in increments of 100 (100, 200, ..., 900)

### ParagraphStyleProperties
- `alignment` must be one of: START, CENTER, END, JUSTIFIED
- `line_spacing` must be positive (typical range: 1.0-3.0)
- Spacing and indent values must be non-negative

### DocumentProperties
- Margin and page size values must be positive when set
- Typical page sizes: Letter (612×792pt), A4 (595×842pt)

### StyleTransferOptions
- If `style_types` is provided, must contain valid NamedStyleType values
- At least one of `include_document_properties` or `include_effective_styles` should be True

## State Transitions

This feature is stateless—no persistent state or transitions. Each operation:
1. Reads source document via API
2. Computes effective styles
3. Writes to target document via API
4. Returns result

## Relationships

```
DocumentStyles 1:1 DocumentProperties
DocumentStyles 1:N EffectiveStyle (exactly 9, one per NamedStyleType)
EffectiveStyle 1:1 TextStyleProperties
EffectiveStyle 1:1 ParagraphStyleProperties
StyleTransferResult 1:N StyleApplicationResult
```
