"""
Generate Dabba App Icons & Splash Screens for Android Capacitor Projects
"""
import os
from PIL import Image, ImageDraw, ImageFont

PLUM = (30, 18, 51)       # #1E1233
CHILI = (216, 57, 31)     # #D8391F
MANGO = (255, 194, 51)    # #FFC233
WHITE = (255, 255, 255)

MIPMAP_SIZES = {
    'mipmap-mdpi': (48, 108),
    'mipmap-hdpi': (72, 162),
    'mipmap-xhdpi': (96, 216),
    'mipmap-xxhdpi': (144, 324),
    'mipmap-xxxhdpi': (192, 432)
}

def create_customer_icon(size):
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    # Background circle
    draw.ellipse([2, 2, size - 2, size - 2], fill=PLUM, outline=CHILI, width=max(2, size // 24))
    # Dabba lunchbox / 'D' symbol
    # Inner Mango shape
    pad = size // 4
    draw.rounded_rectangle([pad, pad, size - pad, size - pad], radius=size // 8, fill=CHILI)
    inner_pad = pad + size // 10
    draw.rounded_rectangle([inner_pad, inner_pad, size - inner_pad, size - inner_pad], radius=size // 12, fill=MANGO)
    return img

def create_rider_icon(size):
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    # Background circle
    draw.ellipse([2, 2, size - 2, size - 2], fill=PLUM, outline=MANGO, width=max(2, size // 24))
    # Delivery scooter / Rider badge
    pad = size // 4
    draw.ellipse([pad, pad, size - pad, size - pad], fill=CHILI)
    # Inner wheel & handlebar accents
    w_size = size // 8
    draw.ellipse([size // 3 - w_size // 2, size * 2 // 3 - w_size // 2, size // 3 + w_size // 2, size * 2 // 3 + w_size // 2], fill=MANGO)
    draw.ellipse([size * 2 // 3 - w_size // 2, size * 2 // 3 - w_size // 2, size * 2 // 3 + w_size // 2, size * 2 // 3 + w_size // 2], fill=MANGO)
    draw.rectangle([size // 3, size * 7 // 12, size * 2 // 3, size * 2 // 3], fill=MANGO)
    return img

def create_splash(is_rider=False):
    width, height = 1080, 1920
    img = Image.new('RGB', (width, height), PLUM)
    draw = ImageDraw.Draw(img)
    
    cx, cy = width // 2, height // 2 - 100
    r = 180
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=CHILI, outline=MANGO, width=12)
    inner_r = 130
    draw.ellipse([cx - inner_r, cy - inner_r, cx + inner_r, cy + inner_r], fill=PLUM)
    
    # Emblem
    box_r = 70
    draw.rounded_rectangle([cx - box_r, cy - box_r, cx + box_r, cy + box_r], radius=24, fill=MANGO)
    
    # Accent ring
    draw.ellipse([cx - 30, cy - 30, cx + 30, cy + 30], fill=CHILI)
    return img

def generate_assets_for_app(res_dir, is_rider=False):
    os.makedirs(res_dir, exist_ok=True)
    icon_fn = create_rider_icon if is_rider else create_customer_icon
    
    for mipmap, (icon_sz, fg_sz) in MIPMAP_SIZES.items():
        m_dir = os.path.join(res_dir, mipmap)
        os.makedirs(m_dir, exist_ok=True)
        
        # Launcher icon
        icon = icon_fn(icon_sz)
        icon.save(os.path.join(m_dir, 'ic_launcher.png'))
        icon.save(os.path.join(m_dir, 'ic_launcher_round.png'))
        
        # Foreground
        fg = icon_fn(fg_sz)
        fg.save(os.path.join(m_dir, 'ic_launcher_foreground.png'))
    
    # Splash screens
    splash_img = create_splash(is_rider)
    drawables = ['drawable', 'drawable-port', 'drawable-land']
    for d in drawables:
        d_dir = os.path.join(res_dir, d)
        os.makedirs(d_dir, exist_ok=True)
        splash_img.save(os.path.join(d_dir, 'splash.png'))

if __name__ == '__main__':
    base = os.path.dirname(os.path.abspath(__file__))
    cust_res = os.path.join(base, 'customer-app', 'android', 'app', 'src', 'main', 'res')
    deli_res = os.path.join(base, 'delivery-app', 'android', 'app', 'src', 'main', 'res')
    
    print("Generating Customer App icons...")
    generate_assets_for_app(cust_res, is_rider=False)
    print("Generating Delivery App icons...")
    generate_assets_for_app(deli_res, is_rider=True)
    print("Done!")

