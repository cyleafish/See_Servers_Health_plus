import matplotlib.font_manager as fm

# 列出系統所有字體並找含中文字體關鍵字的字體名稱
for font in fm.fontManager.ttflist:
    if 'Noto' in font.name or 'WenQuanYi' in font.name or 'SimSun' in font.name or 'Heiti' in font.name or 'Arial Unicode' in font.name:
        print(font.name)

