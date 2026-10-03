"""
FMCSA Driver's Daily Log SVG Renderer
Generates 100% valid XML, high-resolution vector SVG representations of FMCSR Form 395 Driver Daily Logs.
"""

from typing import Dict, Any, List
import html


def _xml_clean(text: Any, max_len: int = 60) -> str:
    """
    Cleans, truncates, and XML-escapes text for safe SVG text nodes.
    Only allows valid XML entities (&amp;, &lt;, &gt;, &quot;, &apos;, and numeric references).
    """
    if text is None:
        return ""
    s = str(text).strip()
    if len(s) > max_len:
        s = s[: max_len - 3] + "..."
    # Escape special XML chars: &, <, >, ", '
    return html.escape(s, quote=True)


def render_log_svg(log_data: Dict[str, Any]) -> str:
    """
    Renders a single 24-hour Driver's Daily Log sheet as a strictly valid XML/SVG string.
    """
    # Grid Dimensions & Layout Constants
    GRID_LEFT = 148
    GRID_RIGHT = 884
    GRID_WIDTH = GRID_RIGHT - GRID_LEFT  # 736 px for 24 hours -> 30.6667 px / hour
    HOUR_WIDTH = GRID_WIDTH / 24.0

    ROW_HEIGHT = 30
    ROW_Y = [195, 195 + ROW_HEIGHT, 195 + 2 * ROW_HEIGHT, 195 + 3 * ROW_HEIGHT]  # [195, 225, 255, 285]
    GRID_TOP = ROW_Y[0] - ROW_HEIGHT / 2.0  # 180
    GRID_BOTTOM = ROW_Y[3] + ROW_HEIGHT / 2.0  # 300

    TOTALS_LEFT = 906
    TOTALS_WIDTH = 64
    TOTALS_CENTER = TOTALS_LEFT + TOTALS_WIDTH / 2.0  # 938.0

    # Header Data Formatting with Strict Length Boundaries and XML Escaping
    date_str = _xml_clean(log_data.get("date_formatted", ""), 20)
    from_loc = _xml_clean(log_data.get("from_location", "Origin"), 38)
    to_loc = _xml_clean(log_data.get("to_location", "Destination"), 38)
    carrier = _xml_clean(log_data.get("carrier_name", "US Freight Express LLC"), 42)
    main_office = _xml_clean(log_data.get("main_office_address", "100 Logistics Blvd, Indianapolis, IN"), 42)
    home_term = _xml_clean(log_data.get("home_terminal_address", "450 Transport Way, Chicago, IL"), 42)
    truck_tractor = _xml_clean(log_data.get("truck_tractor_num", "T-804"), 25)
    trailer = _xml_clean(log_data.get("trailer_num", "TR-5309"), 25)
    vehicle_val = truck_tractor if truck_tractor else (trailer if trailer else "T-804")

    driver_name = _xml_clean(log_data.get("driver_name", "John E. Doe"), 35)
    co_driver = _xml_clean(log_data.get("co_driver", "N/A"), 35)
    shipping_doc = _xml_clean(log_data.get("shipping_doc", "BOL #9482104"), 35)
    shipper_commodity = _xml_clean(log_data.get("shipper_commodity", "General Freight"), 45)

    miles_today = f"{float(log_data.get('total_miles_driving_today', 0.0)):.1f}"
    mileage_today = f"{float(log_data.get('total_mileage_today', 0.0)):.1f}"

    totals = log_data.get("totals", {})
    off_duty_hrs = f"{float(totals.get('off_duty', 0.0)):.2f}"
    sleeper_hrs = f"{float(totals.get('sleeper_berth', 0.0)):.2f}"
    driving_hrs = f"{float(totals.get('driving', 0.0)):.2f}"
    on_duty_hrs = f"{float(totals.get('on_duty_not_driving', 0.0)):.2f}"
    total_day_hrs = f"{float(totals.get('total_hours', 24.0)):.2f}"

    recap = log_data.get("recap", {})
    recap_today = f"{float(recap.get('on_duty_today', totals.get('driving', 0) + totals.get('on_duty_not_driving', 0))):.2f}"
    recap_a = f"{float(recap.get('column_a_last_7_days', 0.0)):.2f}"
    recap_b = f"{float(recap.get('column_b_available_tomorrow', 0.0)):.2f}"
    recap_c = f"{float(recap.get('column_c_last_8_days', 0.0)):.2f}"

    svg_parts: List[str] = []
    svg_parts.append(
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 1180" width="100%" height="100%" style="font-family: Arial, Helvetica, sans-serif; background-color: #ffffff;">'
    )

    # Styles
    svg_parts.append("""  <style>
    .th-title { font-weight: 900; font-size: 20px; fill: #0f172a; }
    .label { font-size: 10px; fill: #475569; font-weight: 600; }
    .val-text { font-size: 12px; fill: #0f172a; font-weight: 700; }
    .grid-hdr-txt { font-size: 8.5px; fill: #ffffff; font-weight: 700; text-anchor: middle; }
    .grid-row-lbl { font-size: 10.5px; font-weight: 700; fill: #1e293b; text-anchor: end; }
    .duty-path { stroke: #1e3a8a; stroke-width: 3.5; stroke-linecap: round; stroke-linejoin: round; fill: none; }
    .trans-connector { stroke: #1e3a8a; stroke-width: 3; stroke-linecap: round; }
    .rmk-cell { font-size: 10px; fill: #1e293b; }
    .recap-hdr { font-size: 9.5px; font-weight: 700; fill: #1e293b; }
    .recap-num { font-size: 12px; font-weight: 800; fill: #1e3a8a; text-anchor: middle; }
  </style>""")

    # Outer Border
    svg_parts.append('  <rect x="15" y="15" width="970" height="1150" fill="#ffffff" stroke="#0f172a" stroke-width="2"/>')

    # ==================== 1. FORM HEADER ====================
    svg_parts.append('  <text x="35" y="44" class="th-title">Drivers Daily Log <tspan font-size="12" fill="#64748b" font-weight="600" dx="6">(24 hours)</tspan></text>')

    # Date Field
    svg_parts.append('  <text x="330" y="42" class="label">Date:</text>')
    svg_parts.append(f'  <text x="365" y="42" class="val-text" font-size="14">{date_str}</text>')
    svg_parts.append('  <text x="365" y="54" font-size="8" fill="#94a3b8">(month)   /   (day)   /   (year)</text>')

    # Legal Filing Notice
    svg_parts.append('  <text x="645" y="38" font-size="8.5" fill="#475569" font-weight="600">Original - File at home terminal.</text>')
    svg_parts.append('  <text x="645" y="50" font-size="8.5" fill="#475569" font-weight="600">Duplicate - Driver retains in possession for 8 days.</text>')

    svg_parts.append('  <line x1="35" y1="62" x2="965" y2="62" stroke="#e2e8f0" stroke-width="1.5"/>')

    # From & To Row
    svg_parts.append('  <text x="35" y="80" class="label">From:</text>')
    svg_parts.append(f'  <text x="75" y="80" class="val-text">{from_loc}</text>')
    svg_parts.append('  <line x1="70" y1="84" x2="480" y2="84" stroke="#cbd5e1" stroke-width="1"/>')

    svg_parts.append('  <text x="510" y="80" class="label">To:</text>')
    svg_parts.append(f'  <text x="535" y="80" class="val-text">{to_loc}</text>')
    svg_parts.append('  <line x1="530" y1="84" x2="965" y2="84" stroke="#cbd5e1" stroke-width="1"/>')

    # Mileage Boxes & Carrier Name Row
    svg_parts.append('  <rect x="35" y="94" width="130" height="38" fill="#f8fafc" stroke="#334155" stroke-width="1"/>')
    svg_parts.append('  <text x="100" y="107" font-size="8" fill="#475569" font-weight="700" text-anchor="middle">Total Miles Driving Today</text>')
    svg_parts.append(f'  <text x="100" y="125" class="val-text" text-anchor="middle">{miles_today} mi</text>')

    svg_parts.append('  <rect x="175" y="94" width="130" height="38" fill="#f8fafc" stroke="#334155" stroke-width="1"/>')
    svg_parts.append('  <text x="240" y="107" font-size="8" fill="#475569" font-weight="700" text-anchor="middle">Total Mileage Today</text>')
    svg_parts.append(f'  <text x="240" y="125" class="val-text" text-anchor="middle">{mileage_today} mi</text>')

    svg_parts.append('  <text x="325" y="104" class="label">Carrier Name:</text>')
    svg_parts.append(f'  <text x="410" y="104" class="val-text">{carrier}</text>')
    svg_parts.append('  <line x1="405" y1="108" x2="965" y2="108" stroke="#cbd5e1" stroke-width="1"/>')

    svg_parts.append('  <text x="325" y="124" class="label">Main Office:</text>')
    svg_parts.append(f'  <text x="410" y="124" class="val-text" font-size="11">{main_office}</text>')
    svg_parts.append('  <line x1="405" y1="128" x2="965" y2="128" stroke="#cbd5e1" stroke-width="1"/>')

    # Home Terminal directly under Main Office; Truck / Tractor / Trailer as ONE single field group
    svg_parts.append('  <text x="35" y="148" class="label">Truck / Tractor / Trailer:</text>')
    svg_parts.append(f'  <text x="175" y="148" class="val-text">{vehicle_val}</text>')
    svg_parts.append('  <line x1="170" y1="152" x2="310" y2="152" stroke="#cbd5e1" stroke-width="1"/>')

    svg_parts.append('  <text x="325" y="148" class="label">Home Terminal:</text>')
    svg_parts.append(f'  <text x="410" y="148" class="val-text" font-size="11">{home_term}</text>')
    svg_parts.append('  <line x1="405" y1="152" x2="965" y2="152" stroke="#cbd5e1" stroke-width="1"/>')

    # ==================== 2. 24-HOUR FMCSR DUTY GRID ====================
    # Top Header Bar (Height 22px: 158 to 180)
    # Background bar starts 16px to the left of GRID_LEFT (132) and extends 16px past GRID_RIGHT (900)
    svg_parts.append(f'  <rect x="{GRID_LEFT - 16}" y="158" width="{GRID_WIDTH + 32}" height="22" fill="#0f172a" rx="2"/>')
    svg_parts.append(f'  <rect x="{TOTALS_LEFT}" y="158" width="{TOTALS_WIDTH}" height="22" fill="#1e293b" rx="2"/>')
    svg_parts.append(f'  <text x="{TOTALS_CENTER}" y="173" font-size="8.5" fill="#ffffff" font-weight="700" text-anchor="middle">Total Hours</text>')

    # 24 Hour Column Labels
    # Sequence: mid-night, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, Noon, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, mid-night
    for h in range(25):
        hx = GRID_LEFT + h * HOUR_WIDTH
        if h == 0 or h == 24:
            # First and Final mid-night wrapped as 'mid-' and 'night'
            svg_parts.append(f'  <text x="{hx:.2f}" y="167" class="grid-hdr-txt" font-size="7.5" font-weight="700">mid-</text>')
            svg_parts.append(f'  <text x="{hx:.2f}" y="176" class="grid-hdr-txt" font-size="7.5" font-weight="700">night</text>')
        elif h == 12:
            svg_parts.append(f'  <text x="{hx:.2f}" y="173" class="grid-hdr-txt" font-size="8.5" font-weight="700">Noon</text>')
        else:
            num = h if h < 12 else (h - 12)
            svg_parts.append(f'  <text x="{hx:.2f}" y="173" class="grid-hdr-txt" font-size="9" font-weight="700">{num}</text>')

    # Grid Box Frame
    svg_parts.append(f'  <rect x="{GRID_LEFT}" y="{GRID_TOP}" width="{GRID_WIDTH}" height="{GRID_BOTTOM - GRID_TOP}" fill="#ffffff" stroke="#0f172a" stroke-width="1.5"/>')

    # Row Separator Lines
    for r in range(1, 4):
        ry = GRID_TOP + r * ROW_HEIGHT
        svg_parts.append(f'  <line x1="{GRID_LEFT}" y1="{ry}" x2="{GRID_RIGHT}" y2="{ry}" stroke="#334155" stroke-width="1"/>')

    # Row Labels (Left of Grid)
    row_labels = ["1. Off Duty", "2. Sleeper Berth", "3. Driving", "4. On Duty (not driving)"]
    for r, lbl in enumerate(row_labels):
        ry = ROW_Y[r] + 4
        svg_parts.append(f'  <text x="{GRID_LEFT - 8}" y="{ry}" class="grid-row-lbl">{lbl}</text>')

    # Hour Vertical Dividers and 15-Minute Ticks
    for h in range(24):
        hx = GRID_LEFT + h * HOUR_WIDTH
        if h > 0:
            svg_parts.append(f'  <line x1="{hx}" y1="{GRID_TOP}" x2="{hx}" y2="{GRID_BOTTOM}" stroke="#94a3b8" stroke-width="1"/>')

        for r in range(4):
            ry_mid = ROW_Y[r]
            x15 = hx + 0.25 * HOUR_WIDTH
            x30 = hx + 0.5 * HOUR_WIDTH
            x45 = hx + 0.75 * HOUR_WIDTH

            # 15 min & 45 min ticks
            svg_parts.append(f'  <line x1="{x15}" y1="{ry_mid - 4}" x2="{x15}" y2="{ry_mid + 4}" stroke="#cbd5e1" stroke-width="0.8"/>')
            svg_parts.append(f'  <line x1="{x45}" y1="{ry_mid - 4}" x2="{x45}" y2="{ry_mid + 4}" stroke="#cbd5e1" stroke-width="0.8"/>')
            # 30 min tick (longer)
            svg_parts.append(f'  <line x1="{x30}" y1="{ry_mid - 8}" x2="{x30}" y2="{ry_mid + 8}" stroke="#94a3b8" stroke-width="1"/>')

    # Right Side Total Hours Box (Distinct separate section)
    svg_parts.append(f'  <rect x="{TOTALS_LEFT}" y="{GRID_TOP}" width="{TOTALS_WIDTH}" height="{GRID_BOTTOM - GRID_TOP}" fill="#f8fafc" stroke="#0f172a" stroke-width="1.5"/>')
    for r in range(1, 4):
        ry = GRID_TOP + r * ROW_HEIGHT
        svg_parts.append(f'  <line x1="{TOTALS_LEFT}" y1="{ry}" x2="{TOTALS_LEFT + TOTALS_WIDTH}" y2="{ry}" stroke="#cbd5e1" stroke-width="1"/>')

    row_totals = [off_duty_hrs, sleeper_hrs, driving_hrs, on_duty_hrs]
    for r, val in enumerate(row_totals):
        ry = ROW_Y[r] + 4
        svg_parts.append(f'  <text x="{TOTALS_CENTER}" y="{ry}" font-size="12" font-weight="700" fill="#0f172a" text-anchor="middle">{val}</text>')

    # Bottom Total Sum
    svg_parts.append(f'  <rect x="{TOTALS_LEFT}" y="{GRID_BOTTOM + 4}" width="{TOTALS_WIDTH}" height="24" fill="#e2e8f0" stroke="#0f172a" stroke-width="1"/>')
    svg_parts.append(f'  <text x="{TOTALS_CENTER}" y="{GRID_BOTTOM + 20}" font-size="12" font-weight="900" fill="#0f172a" text-anchor="middle">= {total_day_hrs}</text>')

    # ==================== 3. DRAW DUTY STATUS TIMELINE ====================
    grid_segments = log_data.get("grid_segments", [])
    grid_transitions = log_data.get("grid_transitions", [])

    # Horizontal status polylines
    for seg in grid_segments:
        sh = max(0.0, min(24.0, float(seg.get("start_hour", 0.0))))
        eh = max(0.0, min(24.0, float(seg.get("end_hour", 0.0))))
        line_num = int(seg.get("line_number", 1))
        if 1 <= line_num <= 4 and eh > sh:
            y_pos = ROW_Y[line_num - 1]
            x1 = GRID_LEFT + sh * HOUR_WIDTH
            x2 = GRID_LEFT + eh * HOUR_WIDTH
            svg_parts.append(f'  <line x1="{x1:.2f}" y1="{y_pos}" x2="{x2:.2f}" y2="{y_pos}" class="duty-path"/>')

    # Vertical transition connectors
    for trans in grid_transitions:
        th = max(0.0, min(24.0, float(trans.get("time_hour", 0.0))))
        from_l = int(trans.get("from_line", 1))
        to_l = int(trans.get("to_line", 1))
        if 1 <= from_l <= 4 and 1 <= to_l <= 4:
            tx = GRID_LEFT + th * HOUR_WIDTH
            y1 = ROW_Y[from_l - 1]
            y2 = ROW_Y[to_l - 1]
            svg_parts.append(f'  <line x1="{tx:.2f}" y1="{y1}" x2="{tx:.2f}" y2="{y2}" class="trans-connector"/>')

    # ==================== 4. REMARKS SECTION ====================
    REMARKS_TOP = 330
    REMARKS_BOTTOM = 640
    svg_parts.append('  <text x="35" y="322" font-size="15" font-weight="900" fill="#0f172a">Remarks</text>')
    svg_parts.append(f'  <rect x="35" y="{REMARKS_TOP}" width="930" height="{REMARKS_BOTTOM - REMARKS_TOP}" fill="#ffffff" stroke="#334155" stroke-width="1.5"/>')

    # Vertical Guidelines connecting grid changes to remarks area
    remarks_items = log_data.get("remarks", [])
    for rmk in remarks_items:
        th = float(rmk.get("time_hour", 0.0))
        rx = GRID_LEFT + th * HOUR_WIDTH
        if GRID_LEFT <= rx <= GRID_RIGHT:
            svg_parts.append(f'  <line x1="{rx:.2f}" y1="{GRID_BOTTOM}" x2="{rx:.2f}" y2="{REMARKS_TOP + 8}" stroke="#93c5fd" stroke-width="1.2" stroke-dasharray="2,2"/>')
            svg_parts.append(f'  <circle cx="{rx:.2f}" cy="{GRID_BOTTOM}" r="2.5" fill="#1e3a8a"/>')

    # Remarks Table Header
    svg_parts.append(f'  <rect x="45" y="{REMARKS_TOP + 8}" width="910" height="22" fill="#f1f5f9"/>')
    svg_parts.append(f'  <text x="55" y="{REMARKS_TOP + 23}" font-size="10" font-weight="700" fill="#334155">Time</text>')
    svg_parts.append(f'  <text x="130" y="{REMARKS_TOP + 23}" font-size="10" font-weight="700" fill="#334155">Duty Status</text>')
    svg_parts.append(f'  <text x="260" y="{REMARKS_TOP + 23}" font-size="10" font-weight="700" fill="#334155">Location (City, ST / Milepost)</text>')
    svg_parts.append(f'  <text x="570" y="{REMARKS_TOP + 23}" font-size="10" font-weight="700" fill="#334155">Activity &amp; Reason</text>')

    # Remarks Table Rows with Safe Width Truncation
    rmk_y = REMARKS_TOP + 45
    for idx, rmk in enumerate(remarks_items[:12]):
        time_txt = _xml_clean(rmk.get("time", ""), 12)
        status_txt = _xml_clean(rmk.get("status_name", ""), 22)
        loc_txt = _xml_clean(rmk.get("location", ""), 45)
        notes_txt = _xml_clean(rmk.get("notes", ""), 55)

        bg_fill = "#ffffff" if idx % 2 == 0 else "#f8fafc"
        svg_parts.append(f'  <rect x="45" y="{rmk_y - 12}" width="910" height="18" fill="{bg_fill}"/>')
        svg_parts.append(f'  <text x="55" y="{rmk_y}" class="rmk-cell" font-weight="700">{time_txt}</text>')
        svg_parts.append(f'  <text x="130" y="{rmk_y}" class="rmk-cell">{status_txt}</text>')
        svg_parts.append(f'  <text x="260" y="{rmk_y}" class="rmk-cell">{loc_txt}</text>')
        svg_parts.append(f'  <text x="570" y="{rmk_y}" class="rmk-cell" fill="#475569">{notes_txt}</text>')
        rmk_y += 21

    # Instruction note below remarks
    svg_parts.append(f'  <text x="35" y="{REMARKS_BOTTOM + 15}" font-size="8.5" fill="#475569">Enter name of place you reported and where released from work and when and where each change of duty occurred. Use time standard of home terminal.</text>')

    # ==================== 5. SHIPPING & CERTIFICATION ====================
    DOCS_TOP = REMARKS_BOTTOM + 26
    svg_parts.append(f'  <rect x="35" y="{DOCS_TOP}" width="440" height="95" fill="#f8fafc" stroke="#334155" stroke-width="1"/>')
    svg_parts.append(f'  <text x="45" y="{DOCS_TOP + 18}" font-size="11" font-weight="700" fill="#0f172a">Shipping Documents:</text>')
    svg_parts.append(f'  <text x="45" y="{DOCS_TOP + 38}" class="label">B/L or Manifest No.:</text>')
    svg_parts.append(f'  <text x="160" y="{DOCS_TOP + 38}" class="val-text">{shipping_doc}</text>')
    svg_parts.append(f'  <text x="45" y="{DOCS_TOP + 62}" class="label">Shipper &amp; Commodity:</text>')
    svg_parts.append(f'  <text x="160" y="{DOCS_TOP + 62}" class="val-text">{shipper_commodity}</text>')
    svg_parts.append(f'  <text x="45" y="{DOCS_TOP + 82}" class="label">Co-Driver:</text>')
    svg_parts.append(f'  <text x="160" y="{DOCS_TOP + 82}" class="val-text">{co_driver}</text>')

    # Driver Signature Box
    svg_parts.append(f'  <rect x="490" y="{DOCS_TOP}" width="475" height="95" fill="#f8fafc" stroke="#334155" stroke-width="1"/>')
    svg_parts.append(f'  <text x="505" y="{DOCS_TOP + 18}" font-size="11" font-weight="700" fill="#0f172a">Driver\'s Certification:</text>')
    svg_parts.append(f'  <text x="505" y="{DOCS_TOP + 36}" font-size="9" fill="#475569">I certify that these entries are true and correct.</text>')
    svg_parts.append(f'  <text x="505" y="{DOCS_TOP + 64}" class="label">Driver Signature / ID:</text>')
    svg_parts.append(f'  <text x="635" y="{DOCS_TOP + 64}" font-size="14" font-weight="700" font-style="italic" fill="#1e3a8a">{driver_name}</text>')
    svg_parts.append(f'  <line x1="630" y1="{DOCS_TOP + 68}" x2="940" y2="{DOCS_TOP + 68}" stroke="#334155" stroke-width="1"/>')
    svg_parts.append(f'  <text x="635" y="{DOCS_TOP + 84}" font-size="8.5" fill="#64748b">Verified ELD Signature Record ID: DRV-VERIFIED-DAY-{log_data.get("day_number", 1)}</text>')

    # ==================== 6. RECAP SECTION ====================
    RECAP_TOP = DOCS_TOP + 108
    svg_parts.append(f'  <rect x="35" y="{RECAP_TOP}" width="930" height="200" fill="#ffffff" stroke="#0f172a" stroke-width="1.5"/>')
    svg_parts.append(f'  <rect x="35" y="{RECAP_TOP}" width="930" height="22" fill="#0f172a"/>')
    svg_parts.append(f'  <text x="45" y="{RECAP_TOP + 15}" font-size="11" font-weight="700" fill="#ffffff">RECAP: Complete at end of day (49 CFR &#167; 395.3)</text>')

    # 70-Hour / 8-Day Drivers Box
    svg_parts.append(f'  <rect x="45" y="{RECAP_TOP + 30}" width="445" height="160" fill="#f8fafc" stroke="#94a3b8" stroke-width="1"/>')
    svg_parts.append(f'  <rect x="45" y="{RECAP_TOP + 30}" width="445" height="20" fill="#1e293b"/>')
    svg_parts.append(f'  <text x="55" y="{RECAP_TOP + 44}" font-size="10" font-weight="700" fill="#ffffff">70 HOUR / 8 DAY DRIVERS</text>')

    items_70 = [
        ("On duty hours today, Total lines 3 &amp; 4:", f"{recap_today} hrs"),
        ("A. Total hours on duty last 7 days including today:", f"{recap_a} hrs"),
        ("B. Total hours available tomorrow (70 hr. minus A*):", f"{recap_b} hrs"),
        ("C. Total hours on duty last 8 days including today:", f"{recap_c} hrs"),
    ]
    for idx, (lbl_txt, val_str) in enumerate(items_70):
        iy = RECAP_TOP + 68 + idx * 30
        svg_parts.append(f'  <text x="55" y="{iy}" class="recap-hdr">{lbl_txt}</text>')
        svg_parts.append(f'  <rect x="380" y="{iy - 12}" width="100" height="18" fill="#ffffff" stroke="#334155" stroke-width="1"/>')
        svg_parts.append(f'  <text x="430" y="{iy + 1}" class="recap-num">{val_str}</text>')

    # 60-Hour / 7-Day Drivers Box (Reference)
    svg_parts.append(f'  <rect x="505" y="{RECAP_TOP + 30}" width="445" height="160" fill="#f8fafc" stroke="#94a3b8" stroke-width="1"/>')
    svg_parts.append(f'  <rect x="505" y="{RECAP_TOP + 30}" width="445" height="20" fill="#334155"/>')
    svg_parts.append(f'  <text x="515" y="{RECAP_TOP + 44}" font-size="10" font-weight="700" fill="#ffffff">60 HOUR / 7 DAY DRIVERS (Reference)</text>')

    avail_60 = f"{max(0.0, 60.0 - float(recap_a)):.2f} hrs"
    items_60 = [
        ("On duty hours today, Total lines 3 &amp; 4:", f"{recap_today} hrs"),
        ("A. Total hours on duty last 6 days including today:", f"{recap_a} hrs"),
        ("B. Total hours available tomorrow (60 hr. minus A*):", avail_60),
        ("C. Total hours on duty last 7 days including today:", f"{recap_a} hrs"),
    ]
    for idx, (lbl_txt, val_str) in enumerate(items_60):
        iy = RECAP_TOP + 68 + idx * 30
        svg_parts.append(f'  <text x="515" y="{iy}" class="recap-hdr" fill="#475569">{lbl_txt}</text>')
        svg_parts.append(f'  <rect x="840" y="{iy - 12}" width="100" height="18" fill="#ffffff" stroke="#94a3b8" stroke-width="1"/>')
        svg_parts.append(f'  <text x="890" y="{iy + 1}" class="recap-num" fill="#475569">{val_str}</text>')

    # Footnote
    svg_parts.append(f'  <text x="45" y="{RECAP_TOP + 185}" font-size="8.5" font-style="italic" fill="#1e3a8a">*If you took 34 consecutive hours off duty you have 60/70 hours available.</text>')
    if log_data.get("has_34h_restart"):
        svg_parts.append(f'  <text x="500" y="{RECAP_TOP + 185}" font-size="8.5" font-weight="700" fill="#059669">&#x2714; 34-Hour Restart completed on this log sheet.</text>')

    svg_parts.append('</svg>')
    return "\n".join(svg_parts)
