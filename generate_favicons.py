"""
Generates crisp, high-resolution multi-format icons for FMCSA HOS Truck Planner.
Generates:
- favicon.ico (multi-size: 16x16, 32x32, 48x48)
- favicon-16x16.png
- favicon-32x32.png
- apple-touch-icon.png (180x180)
- android-chrome-192x192.png (192x192)
- android-chrome-512x512.png (512x512)
"""

from PIL import Image, ImageDraw


def draw_master_canvas() -> Image.Image:
    """Renders a master 1024x1024 anti-aliased icon image."""
    W = 1024
    img = Image.new("RGBA", (W, W), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    pad = int(W * 0.04)  # 40px
    corner_radius = int(W * 0.22)  # 225px
    stroke_w = int(W * 0.045)  # 46px

    # Outer Squircle / Rounded Rectangle
    # Background: Deep Navy #0f172a, Outline: Royal Blue #2563eb
    draw.rounded_rectangle(
        [(pad, pad), (W - pad, W - pad)],
        radius=corner_radius,
        fill=(15, 23, 42, 255),
        outline=(37, 99, 235, 255),
        width=stroke_w,
    )

    # Top Inner Glow / Header accent
    glow_pad = pad + stroke_w
    draw.rounded_rectangle(
        [(glow_pad, glow_pad), (W - glow_pad, int(W * 0.46))],
        radius=int(corner_radius * 0.75),
        fill=(30, 58, 138, 90),
    )

    # Scale factor for truck icon (Base 24x24 viewBox mapped into canvas)
    scale = (W * 0.62) / 24.0
    ox = W * 0.17
    oy = W * 0.23

    truck_stroke = int(2.5 * scale)

    # 1. Trailer Body Interior & Outline
    draw.rounded_rectangle(
        [(ox + 2 * scale, oy + 5.5 * scale), (ox + 14 * scale, oy + 18 * scale)],
        radius=int(2 * scale),
        fill=(37, 99, 235, 80),
        outline=(255, 255, 255, 255),
        width=truck_stroke,
    )

    # 2. Chassis bar between wheels
    draw.line(
        [(ox + 9.5 * scale, oy + 18 * scale), (ox + 15 * scale, oy + 18 * scale)],
        fill=(96, 165, 250, 255),
        width=truck_stroke,
    )

    # 3. Cab & Windshield
    cab_poly = [
        (ox + 14 * scale, oy + 8 * scale),
        (ox + 17.5 * scale, oy + 8 * scale),
        (ox + 21 * scale, oy + 12.5 * scale),
        (ox + 21 * scale, oy + 18 * scale),
        (ox + 14 * scale, oy + 18 * scale),
    ]
    draw.polygon(cab_poly, fill=(59, 130, 246, 90))
    draw.line(
        [
            (ox + 14 * scale, oy + 8 * scale),
            (ox + 17.5 * scale, oy + 8 * scale),
            (ox + 21 * scale, oy + 12.5 * scale),
            (ox + 21 * scale, oy + 18 * scale),
            (ox + 19 * scale, oy + 18 * scale),
        ],
        fill=(255, 255, 255, 255),
        width=truck_stroke,
        joint="curve",
    )

    # Windshield / Window outline
    draw.polygon(
        [
            (ox + 15.5 * scale, oy + 9.5 * scale),
            (ox + 17.2 * scale, oy + 9.5 * scale),
            (ox + 19.8 * scale, oy + 13.0 * scale),
            (ox + 15.5 * scale, oy + 13.0 * scale),
        ],
        fill=(15, 23, 42, 255),
    )

    # 4. Wheels: circle at (7, 18.5) and (17, 18.5)
    wheel_r = 2.6 * scale
    for cx_val in [7.0, 17.0]:
        cx = ox + cx_val * scale
        cy = oy + 18.5 * scale
        draw.ellipse(
            [(cx - wheel_r, cy - wheel_r), (cx + wheel_r, cy + wheel_r)],
            fill=(15, 23, 42, 255),
            outline=(96, 165, 250, 255),
            width=int(2.4 * scale),
        )
        hub_r = 0.95 * scale
        draw.ellipse(
            [(cx - hub_r, cy - hub_r), (cx + hub_r, cy + hub_r)],
            fill=(255, 255, 255, 255),
        )

    # 5. Top Right Green Compliance Shield Badge
    shield_cx = W * 0.77
    shield_cy = W * 0.23
    shield_r = W * 0.105
    draw.ellipse(
        [(shield_cx - shield_r, shield_cy - shield_r), (shield_cx + shield_r, shield_cy + shield_r)],
        fill=(16, 185, 129, 255),  # Emerald Green #10b981
        outline=(15, 23, 42, 255),
        width=int(W * 0.022),
    )

    # White Checkmark inside shield
    chk_w = int(W * 0.022)
    p1 = (shield_cx - shield_r * 0.45, shield_cy)
    p2 = (shield_cx - shield_r * 0.10, shield_cy + shield_r * 0.35)
    p3 = (shield_cx + shield_r * 0.45, shield_cy - shield_r * 0.35)
    draw.line([p1, p2, p3], fill=(255, 255, 255, 255), width=chk_w, joint="curve")

    return img


def main():
    master = draw_master_canvas()

    sizes = {
        "frontend/public/android-chrome-512x512.png": 512,
        "frontend/public/android-chrome-192x192.png": 192,
        "frontend/public/apple-touch-icon.png": 180,
        "frontend/public/favicon-32x32.png": 32,
        "frontend/public/favicon-16x16.png": 16,
    }

    for path, sz in sizes.items():
        resized = master.resize((sz, sz), Image.Resampling.LANCZOS)
        resized.save(path, format="PNG")
        print(f"Generated: {path} ({sz}x{sz})")

    # Multi-resolution ICO file (16, 32, 48)
    img16 = master.resize((16, 16), Image.Resampling.LANCZOS)
    img32 = master.resize((32, 32), Image.Resampling.LANCZOS)
    img48 = master.resize((48, 48), Image.Resampling.LANCZOS)
    img16.save(
        "frontend/public/favicon.ico",
        format="ICO",
        sizes=[(16, 16), (32, 32), (48, 48)],
        append_images=[img32, img48],
    )
    print("Generated: frontend/public/favicon.ico (16, 32, 48)")


if __name__ == "__main__":
    main()
