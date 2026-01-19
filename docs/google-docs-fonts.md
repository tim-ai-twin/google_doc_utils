# Google Docs API Font Reference

This document explains how fonts work in the Google Docs API, including available fonts, font weights, and common pitfalls.

## Key Concept: Font Family vs Font Weight

**The most important thing to understand:** In the Google Docs API, font family and font weight are specified **separately**. You cannot specify a font variant like "Roboto Light" as the font family name.

### Correct Usage

```python
'weightedFontFamily': {
    'fontFamily': 'Roboto',  # Just the family name
    'weight': 300            # Weight as a number (300 = Light)
}
```

### Incorrect Usage

```python
# WRONG - This will fall back to Arial!
'weightedFontFamily': {
    'fontFamily': 'Roboto Light',  # This is NOT a valid font family
    'weight': 400
}
```

## Font Weight Values

Font weights must be multiples of 100 between 100 and 900:

| Weight | Common Name |
|--------|-------------|
| 100 | Thin |
| 200 | Extra Light / Ultra Light |
| 300 | Light |
| 400 | Normal / Regular (default) |
| 500 | Medium |
| 600 | Semi Bold / Demi Bold |
| 700 | Bold |
| 800 | Extra Bold / Ultra Bold |
| 900 | Black / Heavy |

### Font Weight Resolution Rules

The rendered font weight is determined by combining `weight` with the text's `bold` property:

1. If text is bold AND weight < 400 → rendered weight is **400**
2. If text is bold AND 400 ≤ weight < 700 → rendered weight is **700**
3. If weight ≥ 700 → rendered weight equals the specified weight
4. If text is not bold → rendered weight equals the specified weight

This means applying bold to text with weight 300 will render as weight 400, not 300.

## Available Fonts

### Source 1: Google Docs Font Menu

All fonts shown in the Google Docs font dropdown menu are available. This includes:
- System fonts like Arial, Times New Roman, Georgia
- A curated selection of Google Fonts

### Source 2: Google Fonts Library

Any font from [Google Fonts](https://fonts.google.com/) can be used, even if not shown in the default menu. This includes 1500+ font families.

**Important:** Not all Google Fonts support all weights. Check the font's page on Google Fonts to see which weights are available.

### Fallback Behavior

**If the font name is unrecognized, the text is rendered in Arial.**

The API does NOT throw an error for invalid font names. It silently falls back to Arial. This makes debugging font issues tricky.

## Common Font Families and Their Weights

### Roboto (Sans-serif)
Available weights: 100, 300, 400, 500, 700, 900

```python
# Roboto Thin
{'fontFamily': 'Roboto', 'weight': 100}

# Roboto Light
{'fontFamily': 'Roboto', 'weight': 300}

# Roboto Regular
{'fontFamily': 'Roboto', 'weight': 400}

# Roboto Medium
{'fontFamily': 'Roboto', 'weight': 500}

# Roboto Bold
{'fontFamily': 'Roboto', 'weight': 700}

# Roboto Black
{'fontFamily': 'Roboto', 'weight': 900}
```

### Open Sans (Sans-serif)
Available weights: 300, 400, 500, 600, 700, 800

### Lato (Sans-serif)
Available weights: 100, 300, 400, 700, 900

**Note:** Some fonts like Lato have known issues where certain weights (e.g., 500) may not render correctly.

### Montserrat (Sans-serif)
Available weights: 100, 200, 300, 400, 500, 600, 700, 800, 900

### Source Code Pro (Monospace)
Available weights: 200, 300, 400, 500, 600, 700, 900

## System Fonts (Always Available)

These fonts are pre-installed on most operating systems and always work:

- **Arial** - Sans-serif (default fallback)
- **Times New Roman** - Serif
- **Georgia** - Serif
- **Verdana** - Sans-serif
- **Courier New** - Monospace
- **Comic Sans MS** - Casual

## Troubleshooting

### Font Shows as Arial

1. **Check the font family name** - Must be exact (case-sensitive for some fonts)
2. **Don't include weight in family name** - "Roboto", not "Roboto Light"
3. **Verify font exists** - Check [Google Fonts](https://fonts.google.com/) or Google Docs menu
4. **Check weight availability** - Not all fonts support all weights

### Font Weight Not Applying

1. **Check bold property** - Bold text overrides weights < 700
2. **Verify weight is supported** - Check font's available weights on Google Fonts
3. **Use multiples of 100** - Values like 350 are invalid

### Testing Font Availability

You can test if a font is available by:
1. Opening Google Docs in a browser
2. Clicking the font dropdown → "More fonts"
3. Searching for the font name
4. If it appears, it's available via the API

## API Code Examples

### Setting Font Family and Weight

```python
{
    "updateTextStyle": {
        "range": {"startIndex": 1, "endIndex": 10},
        "textStyle": {
            "weightedFontFamily": {
                "fontFamily": "Roboto",
                "weight": 300
            }
        },
        "fields": "weightedFontFamily"
    }
}
```

### Setting Font Size

```python
{
    "updateTextStyle": {
        "range": {"startIndex": 1, "endIndex": 10},
        "textStyle": {
            "fontSize": {
                "magnitude": 14,
                "unit": "PT"
            }
        },
        "fields": "fontSize"
    }
}
```

### Combined Font Styling

```python
{
    "updateTextStyle": {
        "range": {"startIndex": 1, "endIndex": 10},
        "textStyle": {
            "weightedFontFamily": {
                "fontFamily": "Montserrat",
                "weight": 600
            },
            "fontSize": {
                "magnitude": 16,
                "unit": "PT"
            },
            "foregroundColor": {
                "color": {
                    "rgbColor": {"red": 0.2, "green": 0.2, "blue": 0.8}
                }
            }
        },
        "fields": "weightedFontFamily,fontSize,foregroundColor"
    }
}
```

## References

- [WeightedFontFamily API Documentation](https://developers.google.com/resources/api-libraries/documentation/docs/v1/java/latest/com/google/api/services/docs/v1/model/WeightedFontFamily.html)
- [Google Docs API - Format Text](https://developers.google.com/workspace/docs/api/how-tos/format-text)
- [Google Fonts](https://fonts.google.com/)
- [Google Fonts Developer API](https://developers.google.com/fonts/docs/developer_api)
