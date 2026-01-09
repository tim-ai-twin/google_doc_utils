# Research: Google Docs to Markdown Converter

**Feature**: 126-gdoc-markdown-converter
**Date**: 2026-01-09

## Research Question 1: Heading Anchors

**Question**: Do Google Docs headings have implicit/automatic anchor IDs accessible via the API?

**Decision**: Yes - use `ParagraphStyle.headingId` for heading references

**Rationale**:
- Google Docs automatically generates a `headingId` for every paragraph styled as a heading (HEADING_1 through HEADING_6)
- Field location: `paragraph.paragraphStyle.headingId`
- Format: `h.{alphanumeric}` (e.g., `h.abc123def456`)
- Read-only property - cannot be set or modified via API

**Alternatives Considered**:
- Named Ranges: Full API support for create/delete, but adds complexity
- Bookmarks: Cannot be created via REST API (only Apps Script)

**Conclusion**: Use native `headingId` for section references. It's simpler and already exists.

---

## Research Question 2: Anchor Stability

**Question**: When content before a heading is modified, does the heading's anchor ID remain stable?

**Decision**: Generally stable with known edge cases

**Rationale**:
- Heading IDs stick to the heading element, not its position
- Inserting content above an existing heading does NOT change its ID
- **Risk factors that CAN cause ID regeneration**:
  - Significantly altering the heading's formatting
  - Copy-pasting the heading (triggers regeneration)
  - Major structural changes to the heading itself

**Implications for Design**:
- Section-level operations are safe for normal editing workflows
- Edge case: If user copy-pastes a heading, our cached anchor ID becomes invalid
- Mitigation: Return clear error when anchor ID not found, suggest re-fetching hierarchy

---

## Research Question 3: Embedded Object Representation

**Question**: How do embedded objects appear in the Google Docs API structure?

**Decision**: Multiple element types with different ID mechanisms

### Object Type Summary

| Type | Element Type | ID Field | Type Detection | Can Create via API |
|------|-------------|----------|----------------|-------------------|
| Image | `InlineObjectElement` | `inlineObjectId` | `imageProperties` present | Yes |
| Drawing | `InlineObjectElement` | `inlineObjectId` | `embeddedDrawingProperties` present | No |
| Chart | `InlineObjectElement` | `inlineObjectId` | `linkedContentReference.sheetsChartReference` | Yes |
| Equation | `equation` | **None** | `equation` key present | No |
| Video/RichLink | `RichLink` | `richLinkId` | `richLinkProperties.uri` | No |
| Smart Chips | `RichLink` | `richLinkId` | `richLinkProperties.mimeType` | No |

### Key Findings

**Images, Drawings, Charts** (InlineObjectElement):
- ID Path: `paragraph.elements[].inlineObjectElement.inlineObjectId`
- Object data in: `document.inlineObjects[id]` or `document.positionedObjects[id]`
- IDs are stable across document edits
- Cut-paste creates new ID; drag-move preserves ID

**Equations** (Special Case):
- NO object ID - identified only by position (startIndex/endIndex)
- Cannot be created via API
- Must handle differently - cannot use `{^= id equation}` pattern

**Videos and Smart Chips** (RichLink):
- ID Path: `paragraph.elements[].richLink.richLinkId`
- Type detected via `richLinkProperties.mimeType` or URL pattern
- Cannot be created programmatically via API

### Type Detection Logic

```python
def detect_embedded_type(element):
    if 'inlineObjectElement' in element:
        obj_id = element['inlineObjectElement']['inlineObjectId']
        obj = document['inlineObjects'].get(obj_id) or document['positionedObjects'].get(obj_id)
        embedded = obj['inlineObjectProperties']['embeddedObject']

        if 'linkedContentReference' in embedded:
            if 'sheetsChartReference' in embedded['linkedContentReference']:
                return 'chart', obj_id
        if 'embeddedDrawingProperties' in embedded:
            return 'drawing', obj_id
        if 'imageProperties' in embedded:
            return 'image', obj_id
        return 'embed', obj_id  # fallback

    if 'equation' in element:
        return 'equation', None  # No ID available

    if 'richLink' in element:
        rich_link = element['richLink']
        link_id = rich_link.get('richLinkId')
        props = rich_link.get('richLinkProperties', {})
        uri = props.get('uri', '')
        mime = props.get('mimeType', '')

        if 'youtube.com' in uri or 'youtu.be' in uri:
            return 'video', link_id
        return 'embed', link_id  # Generic smart chip

    return None, None
```

### Design Implications

1. **Equations require special handling**: Since equations have no ID, we cannot use the standard `{^= id type}` placeholder. Options:
   - Use positional marker: `{^= equation}` (no ID)
   - Treat as inline content that must be preserved by position
   - **Recommendation**: Use `{^= equation}` without ID; match by position during import

2. **Positioned vs Inline objects**: Both use the same ID mechanism, just stored in different maps (`inlineObjects` vs `positionedObjects`). Our placeholder syntax handles both.

3. **ID Stability**: For section-level updates, we must be careful not to delete/recreate objects. The API preserves objects if we update around them.

---

## Research Question 4: Partial Document Updates

**Question**: Can we update a section without affecting other content?

**Decision**: Yes, via `batchUpdate` with careful index management

**Rationale**:
- Google Docs API uses character indices for all operations
- `DeleteContentRangeRequest` removes content between indices
- `InsertTextRequest` adds content at an index
- Embedded objects at specific indices are preserved if not in deleted range

**Section Update Strategy**:
1. Get document to find section boundaries (heading indices)
2. Calculate range: from heading start to next same-or-higher heading start
3. Delete content in range (excluding embedded objects to preserve)
4. Insert new content at start index
5. Apply formatting via subsequent requests

**Embedded Object Preservation**:
- If placeholder `{^= id type}` is in the new content at same relative position
- Match by ID, calculate new index, ensure object isn't deleted
- More complex: may need to extract objects, delete section, reinsert with objects

---

## Summary of Design Decisions

| Area | Decision | Rationale |
|------|----------|-----------|
| Heading anchors | Use `paragraphStyle.headingId` | Native, stable, no setup needed |
| Section boundaries | Parse by heading level | Standard document structure |
| Images/Drawings/Charts | `{^= objectId type}` | Stable IDs via `inlineObjectId` |
| Equations | `{^= equation}` (no ID) | No ID available; match by position |
| Videos/Smart Chips | `{^= richLinkId video}` or `{^= richLinkId embed}` | Use `richLinkId` |
| Section updates | Index-based batchUpdate | API requirement |
