# Manual Logo Overrides

Place custom outlet logos here to override automated favicon fetching.

## File naming convention:
- Use the outlet's domain name
- Format: `domain-name.png` or `domain-name.svg`
- Examples:
  - `bbc.com.png`
  - `aljazeera.com.png`
  - `nytimes.com.svg`

## Logo specifications:
- **Format**: PNG or SVG (SVG preferred for scalability)
- **Size**: 32x32px minimum, 64x64px recommended
- **Background**: Transparent
- **Style**: Official logo, no text if possible (icon/mark only)
- **Color**: Full color (grayscale applied via CSS)

## How it works:
1. The system first checks for a manual logo in `/public/logos/[domain].png` or `.svg`
2. If not found, it falls back to Google Favicon service
3. Logos are automatically grayscaled by default, colored on hover

## Priority outlets for manual logos:
Consider adding manual logos for these high-visibility outlets:
- BBC (bbc.com.png)
- Al Jazeera (aljazeera.com.png)
- Reuters (reuters.com.png)
- Associated Press (apnews.com.png)
- AFP (afp.com.png)
- The Guardian (theguardian.com.png)
- CNN (cnn.com.png)
- New York Times (nytimes.com.png)
