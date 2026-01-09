# Google Docs API – Embedded Object Representation

Google Docs represents embedded objects (images, drawings, charts, equations, videos, etc.) in a structured way. Embedded content can appear **inline** (as part of a paragraph’s elements) or as **positioned** (anchored to a paragraph but not in the text flow). Inline objects show up as a `ParagraphElement` of type **InlineObjectElement** in `document.body.content[].paragraph.elements[]`【5†L1219-L1227】, whereas positioned objects are referenced by an ID in the paragraph’s `positionedObjectIds` list (with details in a separate `positionedObjects` map)【5†L1118-L1126】. In both cases, the actual object data resides in the document’s `inlineObjects` or `positionedObjects` section, keyed by a unique object ID【2†L678-L687】【2†L689-L697】. Below, each object type is explained with its identifying fields, JSON structure, and behavior:

## Images

- **Element Type:** *InlineObjectElement* – An inline image is represented as a paragraph element of type `inlineObjectElement`, containing an `inlineObjectId`【9†L2219-L2227】. (If the image is set to wrap text or fixed position, it will instead be listed in the parent paragraph’s `positionedObjectIds` and appear in the `positionedObjects` map.) In both cases, the element refers to an object in the document’s `inlineObjects` (for inline) or `positionedObjects` (for positioned) collection.
- **ID Field Path:** `document.body.content[].paragraph.elements[].inlineObjectElement.inlineObjectId` → *InlineObject ID*. This ID corresponds to an entry in the `document.inlineObjects` map (its key and the object’s `objectId`)【9†L2219-L2227】【7†L5760-L5768】. For positioned images, the ID appears in the paragraph’s `positionedObjectIds` and is the key in `document.positionedObjects`. These IDs are unique within the document and are used to reference and update the object’s properties.
- **Type Detection:** In the referenced object’s data, the presence of an **`imageProperties`** field indicates a regular image【7†L5841-L5847】. An embedded image’s JSON will include `"embeddedObject": { ... "imageProperties": {...} }`. This section provides image-specific data such as a `contentUri` (a temporary URL to retrieve the image binary) and possibly a `sourceUri` (if the image was inserted from an external source)【7†L5938-L5946】. There will be **no** `linkedContentReference` present for a normal uploaded image (i.e. it's not linked to external content).
- **Object Properties:** Image objects include metadata like **size** (width/height in points) under the `embeddedObject.size` field【7†L5821-L5829】, and they may have margins and an `embeddedObjectBorder` if a border is applied【7†L5817-L5825】【7†L5841-L5847】. The `title` and `description` fields serve as the image’s alt text (combined in the UI)【7†L5851-L5859】. For inline images, positioning is implicit (they move with text). If the image is a positioned object, its `PositionedObjectProperties` will include a `positioning` sub-object (with properties like `layout` mode, and offset distances) to define how it’s anchored and wrapped relative to the paragraph【4†L119-127】【4†L69-L77】.
- **Example JSON:** A minimal inline image representation – the paragraph element references an `inlineObjectId`, and the `inlineObjects` entry contains the image’s properties:

  ```json
  {
    "paragraph": {
      "elements": [
        {
          "inlineObjectElement": { "inlineObjectId": "image123" }
        }
      ]
    },
    "inlineObjects": {
      "image123": {
        "objectId": "image123",
        "inlineObjectProperties": {
          "embeddedObject": {
            "title": "Sample Image",
            "description": "An example inline image",
            "size": {
              "width": { "magnitude": 160, "unit": "PT" },
              "height": { "magnitude": 120, "unit": "PT" }
            },
            "imageProperties": {
              "contentUri": "https://docs.google.com/document/d/...?export=download&id=...",
              "sourceUri": "https://example.com/image.png"
            }
          }
        }
      }
    }
  }
  ```

- **Stability Notes:** The `inlineObjectId`/`objectId` for an image is **stable across document edits** – it will remain the same even if you edit text around the image or move it within the document (without cutting it)【31†L1-L4】. This stability allows you to store and later match the image by ID. However, inserting a *new* copy of the same image file creates a separate object with a new ID (IDs are tied to the object instance, not the underlying file). If an object is **cut** from the document and then pasted elsewhere, Google Docs treats it as a new insertion – effectively deleting the old object and creating a new one – so it will receive a new ID. (In contrast, simply dragging an image to a new position in the doc keeps the same object and ID.)
- **API Operations:** You *can* create and manipulate images via the Docs API. For example, an image can be inserted with an `InsertInlineImageRequest` (providing an image URL or base64 content and a location index)【32†L13-L16】. You can also delete an image by deleting the containing paragraph element or, for positioned images, using a `DeletePositionedObjectRequest` (specifying the object’s ID)【29†L201-L209】. There is no direct “replace image file” request; to replace an image’s content, you would delete the image and insert a new one (or insert the new image and remove the old). The object’s ID is tied to its lifetime in the document – if you replace an image by insertion/deletion, the replacement will have a new ID.

## Drawings (Embedded Google Drawings)

- **Element Type:** *InlineObjectElement* – An embedded Google Drawing (created via **Insert > Drawing** in Docs) appears similar to an image in the JSON structure. If inline, it will be a paragraph element with an `inlineObjectId` referencing an entry in `inlineObjects`. (It can also be positioned; in that case it would use `positionedObjectIds` and `positionedObjects` similarly to images.)
- **ID Field Path:** Same structure as images. Use `paragraph.elements[].inlineObjectElement.inlineObjectId` to find the object’s ID, which keys into `document.inlineObjects` (or `positionedObjects` if anchored) to get the drawing’s details. The `objectId` inside that entry will match the inlineObjectId【9†L2219-L2227】. This ID should remain consistent for that drawing within the document’s lifetime.
- **Type Detection:** In the InlineObject’s `embeddedObject`, a drawing is indicated by the presence of **`embeddedDrawingProperties`** instead of `imageProperties`. The Docs API uses a union field for object type: if `embeddedDrawingProperties` is present (it’s usually an empty object `{}`), it means the object is an embedded drawing created in the doc【7†L5841-L5847】【7†L5926-L5934】. Unlike images, you will **not** see an `imageProperties` section with a content URI for a drawing – the drawing’s content is not exposed as an image file via the API. (The drawing is stored vectorially and can be edited in Docs, but the API does not provide its internal shape data.)
- **Object Properties:** Embedded drawings have a similar structure to images in terms of alt text and size. You can set a **title/description** for the drawing (alt text) and see a `size` field for its dimensions【7†L5821-L5829】. However, the `embeddedDrawingProperties` itself has no subfields (it’s just a marker type)【7†L5926-L5934】. Other properties like margins or border might appear if applicable (though drawings typically don’t have an image border setting exposed). If the drawing is positioned (wrapped text), it will have `PositionedObjectProperties` with positioning info just like a positioned image. Essentially, aside from the type marker, treat the drawing’s `embeddedObject` similarly to an image’s, but without image-specific data.
- **Example JSON:** An inline drawing represented in JSON – note the `embeddedDrawingProperties` field marking it as a drawing, and no `imageProperties` or content URI:

  ```json
  {
    "paragraph": {
      "elements": [
        {
          "inlineObjectElement": { "inlineObjectId": "draw456" }
        }
      ]
    },
    "inlineObjects": {
      "draw456": {
        "objectId": "draw456",
        "inlineObjectProperties": {
          "embeddedObject": {
            "title": "Embedded Drawing",
            "embeddedDrawingProperties": {},
            "size": {
              "width": { "magnitude": 200, "unit": "PT" },
              "height": { "magnitude": 100, "unit": "PT" }
            }
          }
        }
      }
    }
  }
  ```

- **Stability Notes:** The drawing’s object ID behaves like an image’s ID – stable as long as that drawing remains in the document. Editing the drawing’s contents (e.g. modifying shapes or text within the drawing via the Google Docs UI) does not change its object ID. As with other objects, copying the drawing creates a new object (new ID), and cutting then pasting it will generate a new ID because the API treats that as remove-and-insert. One limitation to note: the Docs API does **not provide the internal content** of drawings, so you cannot programmatically alter the drawing itself (e.g. change a shape’s color)【20†L97-L105】【20†L147-L155】. The drawing is effectively an opaque object – you can only move it or delete it as a whole.
- **API Operations:** Currently, there is *no direct request to create a new drawing* via the API. Drawings must be created in the Docs editor (or potentially copied from one doc to another by duplicating the JSON, though no official support exists for that). You **can** delete or reposition a drawing via the API by treating it like an image object (e.g. use `DeletePositionedObjectRequest` for a positioned drawing, or delete the paragraph element for an inline drawing). If you need to preserve a drawing during an export/import round-trip, the recommended approach is to leave it untouched or treat it as an opaque item – the API will preserve it as long as you don’t remove that object or its reference in the document structure.

## Charts (Linked Google Sheets Charts)

- **Element Type:** *InlineObjectElement* – A chart embedded from Google Sheets appears as an inline object (or positioned object) much like an image. The paragraph will contain an `inlineObjectElement` with an ID referencing the chart object in `inlineObjects`【9†L2219-L2227】, unless the chart is set to wrap/floating (then it would use `positionedObjectIds` similarly).
- **ID Field Path:** `paragraph.elements[].inlineObjectElement.inlineObjectId` → keys into the `document.inlineObjects` map, where the `objectId` and properties of the chart reside. (For a wrapped chart, use the ID in `positionedObjectIds` to find it in `document.positionedObjects` – the internal structure of the object is the same.) Each chart has a unique object ID that remains consistent while the chart stays in the document.
- **Type Detection:** A **linked Google Sheets chart** is indicated by a **`linkedContentReference`** within the `embeddedObject`. Specifically, the `linkedContentReference.sheetsChartReference` will be populated with the source spreadsheet and chart IDs【13†L6126-L6135】【13†L6144-L6152】. In addition, the object will include `imageProperties` for the chart’s rendered image. In JSON, you’ll see something like: `"linkedContentReference": { "sheetsChartReference": { "spreadsheetId": "...", "chartId": 123456 } }` alongside an `imageProperties` block【7†L5839-L5847】【13†L6127-L6135】. This combination tells you the object is a live linked chart (the imageProperties give the last known image snapshot, and the linked reference points to the source data). If the `linkedContentReference` is present, the object is not just a static image – it’s a chart linked to Google Sheets. (If a chart is *unlinked* via the Docs UI, that reference would be removed and it would become a regular image object.)
- **Object Properties:** In addition to the standard alt text (`title/description`) and size, chart objects carry the **sheetsChartReference** info as described. The `imageProperties` sub-object contains a `contentUri` that can be used to fetch the rendered chart image (valid for a short time)【7†L5938-L5946】. Charts do not have an `embeddedDrawingProperties` field – they use the imageProperties for the visual, plus the linked reference for the data link. You might also see a `contentUri` and a `sourceUri` (the sourceUri may point to an image of the chart or the Sheets URL, although in practice Google usually provides the contentUri for the image and uses the linked reference for the actual link). Layout-wise, charts can be inline or positioned just like images; if positioned, there will be positioning data (offsets, layout mode) in `PositionedObjectPositioning`.
- **Example JSON:** An embedded chart (inline) with a linked Sheets reference – note both the `sheetsChartReference` and the `imageProperties`:

  ```json
  {
    "paragraph": {
      "elements": [
        {
          "inlineObjectElement": { "inlineObjectId": "chart789" }
        }
      ]
    },
    "inlineObjects": {
      "chart789": {
        "objectId": "chart789",
        "inlineObjectProperties": {
          "embeddedObject": {
            "title": "Sales Chart",
            "linkedContentReference": {
              "sheetsChartReference": {
                "spreadsheetId": "1A2B3C...SpreadsheetID",
                "chartId": 567890
              }
            },
            "imageProperties": {
              "contentUri": "https://docs.google.com/document/d/.../chart?oid=chart789&...",
              "brightness": 0,
              "contrast": 0
            },
            "size": {
              "width": { "magnitude": 400, "unit": "PT" },
              "height": { "magnitude": 300, "unit": "PT" }
            }
          }
        }
      }
    }
  }
  ```

- **Stability Notes:** The object ID for a chart behaves like that of images/drawings – it’s stable through edits. Even if you update the chart’s data in Google Sheets and use the **Update** button in Docs (or via API, if supported) to refresh the chart image, the object remains the same (same ID). If you cut and paste the chart within the doc, it will be reinserted as a new object (thus a new ID). If you copy-paste the chart (duplicating it), the duplicate gets a new ID and typically retains the *same linked reference* (pointing to the same source chart). One thing to note is that if the user **unlinks** the chart (converting it to a static image), the object ID stays, but the `linkedContentReference` is removed – at that point it becomes just an image object (so your type detection should check for the presence of the linked reference).
- **API Operations:** Google Docs API supports inserting linked charts. You can use an `InsertInlineSheetsChartRequest` (in newer client libraries; in the REST API it’s part of batchUpdate) by specifying the spreadsheetId, chartId, and a location – this will insert a new chart object (the API returns the new objectId in the response)【18†L99-L107】【18†L153-L161】. You can refresh a linked chart via `RefreshSheetsChartRequest` (to pull the latest data) – this uses the object’s ID to update it. Deleting a chart can be done by deleting the inlineObject element or using `DeletePositionedObjectRequest` if it’s a positioned chart. There isn’t a direct “replace chart with another” request; instead you would insert a new chart and remove the old, or use `ReplaceAllText` and `RefreshSheetsChart` combinations if automating updates. The chart’s ID will remain consistent unless the chart is removed/reinserted, as discussed.

## Equations

- **Element Type:** *Equation* – Equations in Google Docs are handled as their own paragraph element type (not as an inlineObject). In the document body, an equation appears as a `paragraph.elements[]` item with `"equation": {}`【5†L1225-L1233】. It does not have an inlineObjectId or any object entry in `inlineObjects`; it’s a distinct element type like a special text run. Essentially, it behaves like an embedded block within the text for rendering a math formula.
- **ID Field Path:** *N/A* – Equations do **not** have a persistent object ID exposed. The `Equation` element in the JSON has no identifier field (only optional suggestion IDs for edits)【9†L2188-L2197】【9†L2199-L2207】. This means you cannot reference a specific equation by an ID the way you can for images or charts. The equation is identified only by its position (startIndex/endIndex in the document) if needed.
- **Type Detection:** You can detect an equation by the presence of the `"equation": {}` object in a ParagraphElement【5†L1225-L1233】. In a fetched document JSON, an equation element will typically appear simply as `"equation": {}` with no further content – the formula’s details are not given as text or MathML. Google Docs stores the equation in an internal format that isn’t exposed via the Docs API. So if an element has the `equation` key, that element is a math equation. (It’s distinct from an image – equations are not images, even though they render visually; they’re a separate element type.)
- **Object Properties:** There is very little metadata provided for equations. The JSON for an equation contains only suggestion metadata (in case the equation insertion or deletion is part of a suggestion)【9†L2188-L2197】. You won’t find alt text, size, or any formatting properties specific to the equation content. Equations are inline with the text (they behave somewhat like a big text character). If you need to treat an equation as an opaque placeholder, the only info you have is that there *is* an equation at that location. Its contents (the actual LaTeX or equation structure) are not available via the API.
- **Example JSON:** An example of an equation element in a paragraph (here, the equation is a standalone element in the paragraph’s elements array):

  ```json
  {
    "paragraph": {
      "elements": [
        {
          "equation": {}
        }
      ]
    }
  }
  ```

- **Stability Notes:** Since equations don’t have an external ID, their “stability” is tied to the document structure indices. An equation will remain in place as the document is edited, just like a block of text. If the user moves an equation (e.g. by cut-paste of the equation or the surrounding text), there’s no persistent ID to track – you would detect it in the new location by scanning the content again.
- **API Operations:** The Docs API **does not support creating new equations** programmatically as of now【22†L147-L155】. You can retrieve equations (they’ll appear in `documents.get` responses as shown), and you can move or delete them by manipulating the document’s text ranges (for example, a `DeleteContentRangeRequest` can remove an equation if you know its indices). But there’s no insertion request that takes a LaTeX string or similar to create an equation. Therefore, treat equations as read-only via the API; preserve them as placeholders and avoid delete/reinsert flows.

## Videos (YouTube/Media Smart Chips)

- **Element Type:** *RichLink* – Google Docs can display certain external content (like YouTube videos or other link previews) as **smart chips**, which appear in the document as a RichLink element【5†L1245-L1251】. A YouTube video link, for example, when converted to a preview chip, will be represented as a `paragraph.elements[]` item with `"richLink": { ... }`.
- **ID Field Path:** `paragraph.elements[].richLink.richLinkId` – Each RichLink element has a `richLinkId` field【10†L2407-L2415】.
- **Type Detection:** For YouTube videos, `richLinkProperties.uri` contains a YouTube URL, and `richLinkProperties.title` is typically the video’s title【10†L2455-L2463】【10†L2463-L2470】. The `mimeType` is often empty for external links; for Drive-hosted videos, `mimeType` may indicate a video type (e.g. `video/mp4`)【10†L2477-L2483】.
- **Object Properties:** RichLink provides `title`, `uri`, and sometimes `mimeType`【10†L2455-L2463】【10†L2475-L2483】. No size/layout fields are exposed.
- **Example JSON:**

  ```json
  {
    "paragraph": {
      "elements": [
        {
          "richLink": {
            "richLinkId": "link1",
            "richLinkProperties": {
              "title": "How to Use Google Docs API (YouTube)",
              "uri": "https://www.youtube.com/watch?v=ABCDEFGHIJK",
              "mimeType": ""
            }
          }
        }
      ]
    }
  }
  ```

- **Stability Notes:** Treat `richLinkId` as stable while the chip remains; copy/cut-paste may yield a new ID.
- **API Operations:** There is no official Docs API request to insert RichLink smart chips directly; insert the URL text/hyperlink and rely on Docs UI behavior to “chip” it【24†L159-L167】.

## Other Linked Embeds (Drive Files, Sheets, Slides, etc.)

- **Element Type:** *RichLink* – Drive file chips and other smart chips also appear as RichLink elements【10†L2401-L2409】【10†L2451-L2459】.
- **ID Field Path:** `paragraph.elements[].richLink.richLinkId`.
- **Type Detection:** Use `richLinkProperties.mimeType` to distinguish Drive file types【10†L2475-L2483】 (e.g., `application/vnd.google-apps.spreadsheet` for Sheets).
- **Example JSON:**

  ```json
  {
    "paragraph": {
      "elements": [
        {
          "richLink": {
            "richLinkId": "link3",
            "richLinkProperties": {
              "title": "Budget Q1 2025",
              "uri": "https://docs.google.com/spreadsheets/d/ABCDE12345/edit",
              "mimeType": "application/vnd.google-apps.spreadsheet"
            }
          }
        }
      ]
    }
  }
  ```

- **Stability Notes:** Same general behavior as other RichLinks.
- **API Operations:** Similar limitation: no direct RichLink chip insertion via API; insert hyperlink text and rely on Docs UI to render chips【24†L159-L167】.

