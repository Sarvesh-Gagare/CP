"""
Traffic Violations Explainable System — Tkinter GUI  (v2 fixed)
Fixes:
  • Violation cards now show RED border/header (not yellow) when VIOL
  • Manual query box auto-populates vehicle(id, type). fact when form fields change
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
import os
import shutil
import datetime
import re

# ── optional deps ─────────────────────────────────────────────────────────────
try:
    from reportlab.lib.pagesizes import A4
    from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer,
                                    Table, TableStyle, HRFlowable)
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib import colors
    from reportlab.lib.units import cm
    REPORTLAB = True
except ImportError:
    REPORTLAB = False

# ── colour palette ────────────────────────────────────────────────────────────
BG_DARK  = "#0d1117"
BG_CARD  = "#161b22"
BG_PANEL = "#1c2330"
BG_INPUT = "#21262d"
ACCENT   = "#e36b1e"
ACCENT2  = "#f5a623"
SUCCESS  = "#2ea043"
DANGER   = "#da3633"       # ← RED used for violations
TEXT_PRI = "#e6edf3"
TEXT_SEC = "#8b949e"
BORDER   = "#30363d"
BLUE     = "#388bfd"
WARN     = "#d29922"       # yellow — ONLY used for insufficient data

VIOLATION_TYPES = [
    "red_light", "speeding", "wrong_lane", "no_helmet",
    "wrong_direction", "illegal_u_turn", "no_seatbelt",
    "phone_usage", "overloading", "no_parking", "speed_breaker",
]

VIOLATION_LABELS = {
    "red_light":       "🚦 Red Light",
    "speeding":        "⚡ Speeding",
    "wrong_lane":      "🛣️  Wrong Lane",
    "no_helmet":       "⛑️  No Helmet",
    "wrong_direction": "↩️  Wrong Direction",
    "illegal_u_turn":  "🔄 Illegal U-Turn",
    "no_seatbelt":     "🪑 No Seatbelt",
    "phone_usage":     "📱 Phone Usage",
    "overloading":     "👥 Overloading",
    "no_parking":      "🚫 No Parking",
    "speed_breaker":   "🐢 Speed Breaker",
}

PROLOG_AVAILABLE = shutil.which("swipl") is not None

# ── status sentinels ──────────────────────────────────────────────────────────
VIOL  = "violation"
CLEAR = "clear"
INSUF = "insufficient"


# ── violation engine ──────────────────────────────────────────────────────────
def _check(vid, vtype, vehicles, tl_red, crossed, speeds, wrong_ln,
           helmets, emerg, dirs, seatbelts, phones, pax, parked, zones, sb):
    vt          = vehicles.get(vid, "")
    valid_types = {"car", "bike", "truck", "bus"}

    if vtype == "red_light":
        if tl_red is None:
            return INSUF, "Traffic-light state not provided."
        if tl_red and vid not in crossed:
            return INSUF, "Crossed-stop-line data missing (required with red light)."
        ok = tl_red and vid in crossed and vid not in emerg
        return (VIOL, "Traffic light was RED and vehicle crossed stop line.") if ok \
               else (CLEAR, "No red-light crossing detected.")

    elif vtype == "speeding":
        if vid not in speeds:
            return INSUF, "Speed not provided."
        s  = speeds[vid]
        ok = s > 60 and vid not in emerg
        return (VIOL, f"Speed {s} km/h exceeds 60 km/h city limit.") if ok \
               else (CLEAR, f"Speed {s} km/h within 60 km/h limit.")

    elif vtype == "wrong_lane":
        ok = vid in wrong_ln
        return (VIOL, "Vehicle crossed a solid lane line.") if ok \
               else (CLEAR, "No solid-line crossing reported.")

    elif vtype == "no_helmet":
        if vt not in valid_types:
            return INSUF, "Vehicle type unknown — cannot assess helmet rule."
        if vt != "bike":
            return CLEAR, "Helmet rule applies to bikes only."
        if vid not in helmets:
            return INSUF, "Helmet status not provided for this bike."
        ok = helmets[vid] == "no"
        return (VIOL, "Two-wheeler rider not wearing helmet.") if ok \
               else (CLEAR, "Helmet worn.")

    elif vtype == "wrong_direction":
        if vid not in dirs:
            return INSUF, "Direction data not provided."
        ok = dirs[vid] == "wrong_way"
        return (VIOL, "Vehicle moving against one-way traffic.") if ok \
               else (CLEAR, "Correct direction observed.")

    elif vtype == "illegal_u_turn":
        if vid not in dirs:
            return INSUF, "Direction data not provided."
        if tl_red is None:
            return INSUF, "Traffic-light state not provided."
        ok = dirs[vid] == "u_turn" and tl_red
        return (VIOL, "Illegal U-turn performed at a red light.") if ok \
               else (CLEAR, "No illegal U-turn detected.")

    elif vtype == "no_seatbelt":
        if vt not in valid_types:
            return INSUF, "Vehicle type unknown — cannot assess seatbelt rule."
        if vt != "car":
            return CLEAR, "Seatbelt rule applies to cars only."
        if vid not in seatbelts:
            return INSUF, "Seatbelt status not provided for this car."
        ok = seatbelts[vid] == "no"
        return (VIOL, "Car driver/passenger not wearing seatbelt.") if ok \
               else (CLEAR, "Seatbelt worn.")

    elif vtype == "phone_usage":
        if vid not in phones:
            return INSUF, "Phone-usage data not provided."
        ok = phones[vid] == "yes"
        return (VIOL, "Driver detected using mobile phone while driving.") if ok \
               else (CLEAR, "No phone usage detected.")

    elif vtype == "overloading":
        if vt not in valid_types:
            return INSUF, "Vehicle type unknown — cannot assess overloading rule."
        if vt != "bike":
            return CLEAR, "Overloading rule applies to bikes only."
        if vid not in pax:
            return INSUF, "Passenger count not provided for this bike."
        n  = pax[vid]
        ok = n > 2
        return (VIOL, f"Bike has {n} passengers (max allowed: 2).") if ok \
               else (CLEAR, f"Passenger count {n} within limit.")

    elif vtype == "no_parking":
        if parked.get(vid) != "yes":
            return CLEAR, "Vehicle not reported as parked."
        if vid not in zones:
            return INSUF, "Zone type not provided (required when parked)."
        ok = zones[vid] == "no_parking"
        return (VIOL, "Vehicle parked in a no-parking zone.") if ok \
               else (CLEAR, "Parked in a permitted zone.")

    elif vtype == "speed_breaker":
        if vid not in speeds:
            return INSUF, "Speed not provided."
        if vid not in sb:
            return CLEAR, "Not reported near a speed breaker."
        s  = speeds[vid]
        ok = s > 20
        return (VIOL, f"Speed {s} km/h exceeds 20 km/h near speed breaker.") if ok \
               else (CLEAR, f"Speed {s} km/h OK near speed breaker.")

    return INSUF, "Unknown violation type."


def simulate_violations(facts: list) -> dict:
    vehicles  = {}
    tl_red    = None
    crossed   = set()
    speeds    = {}
    wrong_ln  = set()
    helmets   = {}
    emerg     = set()
    dirs      = {}
    seatbelts = {}
    phones    = {}
    pax       = {}
    parked    = {}
    zones     = {}
    sb        = set()

    for name, args in facts:
        if   name == "vehicle":                               vehicles[args[0]] = args[1]
        elif name == "traffic_light" and args[0] == "red":   tl_red = True
        elif name == "traffic_light" and args[0] == "green": tl_red = False
        elif name == "crossed_stop_line":                     crossed.add(args[0])
        elif name == "speed":                                 speeds[args[0]] = int(args[1])
        elif name == "in_wrong_lane" and args[1] == "solid": wrong_ln.add(args[0])
        elif name == "helmet":                                helmets[args[0]] = args[1]
        elif name == "emergency_vehicle":                     emerg.add(args[0])
        elif name == "direction":                             dirs[args[0]] = args[1]
        elif name == "seatbelt":                              seatbelts[args[0]] = args[1]
        elif name == "phone_usage":                           phones[args[0]] = args[1]
        elif name == "passenger_count":                       pax[args[0]] = int(args[1])
        elif name == "parked":                                parked[args[0]] = args[1]
        elif name == "zone_type":                             zones[args[0]] = args[1]
        elif name == "near_speed_breaker" and args[1] == "yes": sb.add(args[0])

    result = {}
    for vid in vehicles:
        result[vid] = {
            vt: _check(vid, vt, vehicles, tl_red, crossed, speeds, wrong_ln,
                       helmets, emerg, dirs, seatbelts, phones, pax, parked, zones, sb)
            for vt in VIOLATION_TYPES
        }
    return result


def parse_manual_query(query: str) -> list:
    """Parse Prolog-style fact string into (name, [args]) list."""
    facts = []
    for m in re.finditer(r'(\w+)\(([^)]*)\)', query):
        name = m.group(1).strip()
        args = [a.strip().strip("'\"") for a in m.group(2).split(",")]
        parsed = []
        for a in args:
            try:   parsed.append(int(a))
            except ValueError: parsed.append(a)
        facts.append((name, parsed))
    return facts


def build_facts_from_form(data: dict) -> list:
    facts = [("frame_time", ["t_001"])]
    vid   = data["vehicle_id"].strip()
    facts.append(("vehicle", [vid, data["vehicle_type"]]))

    if data["tl_red"]:
        facts.append(("traffic_light", ["red",   "t_001"]))
    else:
        facts.append(("traffic_light", ["green", "t_001"]))

    spd = data["speed"].strip()
    if spd:
        try:   facts.append(("speed", [vid, int(spd)]))
        except ValueError: pass

    if data["crossed_line"]:  facts.append(("crossed_stop_line", [vid, "t_001"]))
    if data["wrong_lane"]:    facts.append(("in_wrong_lane",      [vid, "solid"]))
    if data["near_sb"]:       facts.append(("near_speed_breaker", [vid, "yes"]))
    if data["helmet"] in ("yes", "no"):   facts.append(("helmet",        [vid, data["helmet"]]))
    if data["emergency"]:                 facts.append(("emergency_vehicle", [vid]))
    if data["direction"] != "none":       facts.append(("direction",     [vid, data["direction"]]))
    if data["seatbelt"] in ("yes", "no"): facts.append(("seatbelt",     [vid, data["seatbelt"]]))
    if data["phone"]    in ("yes", "no"): facts.append(("phone_usage",  [vid, data["phone"]]))

    pax = data["passengers"].strip()
    if pax:
        try:   facts.append(("passenger_count", [vid, int(pax)]))
        except ValueError: pass

    if data["parked"]:
        facts.append(("parked", [vid, "yes"]))
        if data["no_parking_zone"]:
            facts.append(("zone_type", [vid, "no_parking"]))

    return facts


# ── PDF export ────────────────────────────────────────────────────────────────
def export_pdf(report_text: str, vdata: dict, vid: str, path: str):
    doc    = SimpleDocTemplate(path, pagesize=A4,
                               leftMargin=2*cm, rightMargin=2*cm,
                               topMargin=2*cm, bottomMargin=2*cm)
    styles = getSampleStyleSheet()
    title_s = ParagraphStyle("TT", parent=styles["Title"],
                              textColor=colors.HexColor("#e36b1e"), fontSize=18, spaceAfter=6)
    head_s  = ParagraphStyle("HH", parent=styles["Heading2"],
                              textColor=colors.HexColor("#388bfd"),
                              fontSize=12, spaceBefore=12, spaceAfter=4)
    body_s  = ParagraphStyle("BB", parent=styles["Normal"], fontSize=9, leading=14)
    mono_s  = ParagraphStyle("MM", parent=styles["Code"],
                              fontSize=8, leading=11,
                              backColor=colors.HexColor("#1c2330"),
                              textColor=colors.HexColor("#f5a623"))

    story = []
    story.append(Paragraph("Traffic Violations Analysis Report", title_s))
    story.append(Paragraph(
        f"Vehicle: <b>{vid.upper()}</b> &nbsp;&nbsp;|&nbsp;&nbsp; "
        f"Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", body_s))
    story.append(HRFlowable(width="100%", thickness=1,
                             color=colors.HexColor("#e36b1e"), spaceAfter=8))

    story.append(Paragraph("Violation Summary", head_s))
    tbl_data = [["Violation", "Status", "Explanation"]]
    for vtype in VIOLATION_TYPES:
        status, exp = vdata.get(vtype, (INSUF, ""))
        if   status == VIOL:  stat_str = "VIOLATION";         clr = colors.HexColor("#da3633")
        elif status == INSUF: stat_str = "INSUFFICIENT DATA"; clr = colors.HexColor("#d29922")
        else:                 stat_str = "CLEAR";             clr = colors.HexColor("#2ea043")
        label = VIOLATION_LABELS.get(vtype, vtype)
        label_clean = re.sub(r'[^\x00-\x7F]+', '', label).strip()
        tbl_data.append([label_clean, stat_str, exp])

    tbl = Table(tbl_data, colWidths=[4.5*cm, 3.8*cm, 8.7*cm])
    tbl.setStyle(TableStyle([
        ("BACKGROUND",     (0,0), (-1,0), colors.HexColor("#161b22")),
        ("TEXTCOLOR",      (0,0), (-1,0), colors.HexColor("#e6edf3")),
        ("FONTNAME",       (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTSIZE",       (0,0), (-1,-1), 8),
        ("ROWBACKGROUNDS", (0,1), (-1,-1),
         [colors.HexColor("#1c2330"), colors.HexColor("#161b22")]),
        ("TEXTCOLOR",      (0,1), (-1,-1), colors.HexColor("#e6edf3")),
        ("GRID",           (0,0), (-1,-1), 0.3, colors.HexColor("#30363d")),
        ("VALIGN",         (0,0), (-1,-1), "MIDDLE"),
        ("TOPPADDING",     (0,0), (-1,-1), 4),
        ("BOTTOMPADDING",  (0,0), (-1,-1), 4),
    ]))
    story.append(tbl)

    story.append(Paragraph("Full Engine Log", head_s))
    for line in report_text.split("\n"):
        safe = (line.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")
                    .encode("ascii", "ignore").decode())
        story.append(Paragraph(safe or " ", mono_s))

    doc.build(story)


# ── GUI ───────────────────────────────────────────────────────────────────────
class TrafficApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Traffic Violations Explainable System  v2")
        self.geometry("1440x900")
        self.minsize(1000, 700)
        self.configure(bg=BG_DARK)
        self._results: dict    = {}
        self._current_vid: str = ""
        self._report_text: str = ""
        self._build_ui()

    def _build_ui(self):
        self._build_header()
        self._build_body()
        self._build_statusbar()

    # ── header ────────────────────────────────────────────────────────────────
    def _build_header(self):
        hdr = tk.Frame(self, bg=BG_CARD, height=62)
        hdr.pack(fill=tk.X)
        hdr.pack_propagate(False)
        tk.Label(hdr, text="🚔", font=("Segoe UI Emoji", 24),
                 bg=BG_CARD, fg=ACCENT).pack(side=tk.LEFT, padx=(18,6), pady=10)
        tk.Label(hdr, text="TRAFFIC VIOLATIONS",
                 font=("Courier New", 17, "bold"),
                 bg=BG_CARD, fg=TEXT_PRI).pack(side=tk.LEFT)
        tk.Label(hdr, text="  Explainable AI System  v2",
                 font=("Courier New", 10),
                 bg=BG_CARD, fg=TEXT_SEC).pack(side=tk.LEFT, pady=6)
        mode_txt   = "● SWI-Prolog connected" if PROLOG_AVAILABLE else "● Python simulation mode"
        mode_color = SUCCESS if PROLOG_AVAILABLE else ACCENT2
        tk.Label(hdr, text=mode_txt, font=("Courier New", 9),
                 bg=BG_CARD, fg=mode_color).pack(side=tk.RIGHT, padx=18)

    # ── body ──────────────────────────────────────────────────────────────────
    def _build_body(self):
        self._h_pane = tk.PanedWindow(self, orient=tk.HORIZONTAL,
                                      bg=BG_DARK, sashwidth=7,
                                      sashrelief=tk.RAISED, sashpad=2)
        self._h_pane.pack(fill=tk.BOTH, expand=True, padx=6, pady=(0, 4))

        left = tk.Frame(self._h_pane, bg=BG_CARD,
                        highlightthickness=1, highlightbackground=BORDER)
        self._h_pane.add(left, minsize=260, width=370, stretch="never")

        right = tk.Frame(self._h_pane, bg=BG_DARK)
        self._h_pane.add(right, minsize=500, stretch="always")

        self._build_form(left)
        self._build_results(right)

    # ── left: form ────────────────────────────────────────────────────────────
    def _build_form(self, outer):
        canvas = tk.Canvas(outer, bg=BG_CARD, highlightthickness=0)
        sb_w   = ttk.Scrollbar(outer, orient=tk.VERTICAL, command=canvas.yview)
        canvas.configure(yscrollcommand=sb_w.set)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb_w.pack(side=tk.RIGHT, fill=tk.Y)

        form = tk.Frame(canvas, bg=BG_CARD, padx=14)
        canvas.create_window((0, 0), window=form, anchor="nw")
        form.bind("<Configure>",
                  lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

        def _scroll(e):
            canvas.yview_scroll(int(-1*(e.delta/120)), "units")
        canvas.bind("<MouseWheel>", _scroll)
        form.bind("<MouseWheel>",   _scroll)

        # ── VEHICLE DETAILS ──────────────────────────────────────────────────
        self._section_lbl(form, "🚗  VEHICLE DETAILS")
        self._v_id   = self._field(form, "Vehicle ID *", "e.g.  car_001")
        self._v_type = self._dropdown(form, "Vehicle Type *",
                                      ["car", "bike", "truck", "bus"])

        # Trace changes so manual query auto-updates
        self._v_id.trace_add("write",   lambda *_: self._sync_manual_header())
        self._v_type.trace_add("write",  lambda *_: self._sync_manual_header())

        # ── SPEED & LOCATION ─────────────────────────────────────────────────
        self._section_lbl(form, "⚡  SPEED & LOCATION")
        self._v_speed   = self._field(form, "Speed (km/h)", "e.g.  85")
        self._v_crossed = self._checkbox(form, "Crossed Stop Line")
        self._v_wrong   = self._checkbox(form, "In Wrong Lane  (solid line)")
        self._v_near_sb = self._checkbox(form, "Near Speed Breaker")

        # ── TRAFFIC CONDITIONS ───────────────────────────────────────────────
        self._section_lbl(form, "🚦  TRAFFIC CONDITIONS")
        self._v_tl_red = self._checkbox(form, "Traffic Light is RED")
        self._v_dir    = self._dropdown(form, "Direction Violation",
                                        ["none", "wrong_way", "u_turn"])
        self._v_emerg  = self._checkbox(form, "Emergency Vehicle  (exempt)")

        # ── DRIVER / PASSENGER INFO ──────────────────────────────────────────
        self._section_lbl(form, "👤  DRIVER / PASSENGER INFO")
        self._v_helmet = self._dropdown(form, "Helmet  (bikes)", ["", "yes", "no"])
        self._v_belt   = self._dropdown(form, "Seatbelt  (cars)", ["", "yes", "no"])
        self._v_phone  = self._dropdown(form, "Using Phone?", ["", "yes", "no"])
        self._v_pax    = self._field(form, "Passenger Count  (bikes)", "e.g.  3")

        # ── PARKING ──────────────────────────────────────────────────────────
        self._section_lbl(form, "🅿️  PARKING")
        self._v_parked = self._checkbox(form, "Vehicle is Parked")
        self._v_nopk   = self._checkbox(form, "In No-Parking Zone")

        # ── MANUAL FACT QUERY ─────────────────────────────────────────────────
        self._section_lbl(form, "🔍  MANUAL FACT QUERY  (advanced)")
        tk.Label(form,
                 text="vehicle(id, type). is auto-filled from the form above.\n"
                      "Add extra facts below — they are merged at check time.\n"
                      "Example:\n"
                      "  speed(car_001, 110). traffic_light(red, t_001).\n"
                      "  phone_usage(car_001, yes). seatbelt(car_001, no).",
                 font=("Courier New", 7),
                 bg=BG_CARD, fg=TEXT_SEC, justify=tk.LEFT,
                 wraplength=300).pack(fill=tk.X, pady=(2, 4))

        # Read-only header showing the auto-generated vehicle fact
        self._manual_header_var = tk.StringVar(value="vehicle(car_001, car).  ← auto")
        header_entry = tk.Entry(
            form, textvariable=self._manual_header_var,
            bg="#0d1117", fg="#388bfd",
            font=("Courier New", 9, "bold"),
            relief=tk.FLAT,
            highlightthickness=1, highlightbackground=BORDER,
            state="readonly", readonlybackground="#0d1117",
        )
        header_entry.pack(fill=tk.X, ipady=4, pady=(0, 2))

        self._v_manual = tk.Text(form,
                                  bg=BG_INPUT, fg=ACCENT2,
                                  insertbackground=ACCENT,
                                  font=("Courier New", 9),
                                  relief=tk.FLAT,
                                  highlightthickness=1, highlightbackground=BORDER,
                                  highlightcolor=ACCENT,
                                  height=5, wrap=tk.WORD)
        self._v_manual.pack(fill=tk.X, pady=(0, 4))

        self._v_use_manual = tk.BooleanVar(value=False)
        tk.Checkbutton(form,
                       text="Use manual query (vehicle ID/type from form, facts from box above)",
                       variable=self._v_use_manual,
                       bg=BG_CARD, fg=TEXT_PRI, selectcolor=BG_PANEL,
                       activebackground=BG_CARD, activeforeground=ACCENT,
                       font=("Courier New", 8), anchor="w",
                       highlightthickness=0, relief=tk.FLAT).pack(fill=tk.X)

        # ── action buttons ────────────────────────────────────────────────────
        tk.Frame(form, bg=BORDER, height=1).pack(fill=tk.X, pady=(14, 0))
        btn_row = tk.Frame(form, bg=BG_CARD)
        btn_row.pack(fill=tk.X, pady=10)
        self._mk_btn(btn_row, "  ▶  CHECK VIOLATIONS  ", self._on_check,
                     color=ACCENT).pack(fill=tk.X, pady=(0, 5))
        self._mk_btn(btn_row, "  ⟳  LOAD DEMO DATA  ", self._on_demo,
                     color=BG_PANEL).pack(fill=tk.X, pady=(0, 5))
        self._mk_btn(btn_row, "  ✕  CLEAR FORM  ", self._on_clear,
                     color=BG_PANEL).pack(fill=tk.X, pady=(0, 14))

    # ── right: results ────────────────────────────────────────────────────────
    def _build_results(self, parent):
        # summary bar
        sumbar = tk.Frame(parent, bg=BG_CARD,
                          highlightthickness=1, highlightbackground=BORDER)
        sumbar.pack(fill=tk.X, pady=(0, 6))

        self._v_title = tk.Label(
            sumbar,
            text="Enter vehicle details and press CHECK VIOLATIONS →",
            font=("Courier New", 12, "bold"),
            bg=BG_CARD, fg=TEXT_PRI, padx=14, pady=10)
        self._v_title.pack(side=tk.LEFT)

        self._v_badge = tk.Label(sumbar, text="",
                                  font=("Courier New", 10, "bold"),
                                  bg=BG_CARD, fg=DANGER, padx=10)
        self._v_badge.pack(side=tk.LEFT)

        self._pdf_btn = tk.Button(
            sumbar, text="  ⬇  Export PDF  ",
            command=self._on_export_pdf,
            bg=BLUE, fg=TEXT_PRI,
            font=("Courier New", 9, "bold"),
            relief=tk.FLAT, cursor="hand2",
            padx=8, pady=5,
            activebackground=ACCENT2, activeforeground="white",
            borderwidth=0, state=tk.DISABLED)
        self._pdf_btn.pack(side=tk.RIGHT, padx=12, pady=6)

        if not REPORTLAB:
            tk.Label(sumbar, text="(pip install reportlab for PDF export)",
                     font=("Courier New", 7), bg=BG_CARD, fg=TEXT_SEC).pack(
                         side=tk.RIGHT, padx=4)

        # Vertical PanedWindow — cards top, log bottom
        self._v_pane = tk.PanedWindow(parent, orient=tk.VERTICAL,
                                       bg=BG_DARK, sashwidth=7,
                                       sashrelief=tk.RAISED, sashpad=2)
        self._v_pane.pack(fill=tk.BOTH, expand=True)

        # card grid
        card_wrap = tk.Frame(self._v_pane, bg=BG_DARK)
        self._v_pane.add(card_wrap, minsize=140, stretch="always")

        self._cv = tk.Canvas(card_wrap, bg=BG_DARK, highlightthickness=0)
        cv_sb    = ttk.Scrollbar(card_wrap, orient=tk.VERTICAL, command=self._cv.yview)
        self._cv.configure(yscrollcommand=cv_sb.set)
        self._cv.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        cv_sb.pack(side=tk.RIGHT, fill=tk.Y)

        self._grid   = tk.Frame(self._cv, bg=BG_DARK)
        self._cv_win = self._cv.create_window((0, 0), window=self._grid, anchor="nw")
        self._grid.bind("<Configure>",
                        lambda e: self._cv.configure(scrollregion=self._cv.bbox("all")))
        self._cv.bind("<Configure>",
                      lambda e: self._cv.itemconfig(self._cv_win, width=e.width - 2))

        # output log
        out_wrap = tk.Frame(self._v_pane, bg=BG_DARK)
        self._v_pane.add(out_wrap, minsize=100, stretch="always")

        tk.Label(out_wrap, text="ENGINE OUTPUT  /  EXPLANATION LOG",
                 font=("Courier New", 9, "bold"),
                 bg=BG_DARK, fg=TEXT_SEC, anchor="w").pack(
                     fill=tk.X, padx=2, pady=(2, 2))

        self._out = scrolledtext.ScrolledText(
            out_wrap,
            bg=BG_CARD, fg=ACCENT2,
            insertbackground=ACCENT,
            font=("Courier New", 10),
            borderwidth=0,
            highlightthickness=1, highlightbackground=BORDER,
            relief=tk.FLAT, wrap=tk.WORD,
            state=tk.DISABLED)
        self._out.pack(fill=tk.BOTH, expand=True)

        self.after(250, self._equalise_panes)

    def _equalise_panes(self):
        self._v_pane.update_idletasks()
        h = self._v_pane.winfo_height()
        if h > 20:
            self._v_pane.sash_place(0, 0, h // 2)

    # ── status bar ────────────────────────────────────────────────────────────
    def _build_statusbar(self):
        self._status = tk.Label(
            self,
            text="Ready.  Fill in the form and press CHECK VIOLATIONS.",
            font=("Courier New", 9),
            bg=BG_CARD, fg=TEXT_SEC, anchor="w", padx=12, pady=4)
        self._status.pack(fill=tk.X, side=tk.BOTTOM)

    # ── widget helpers ────────────────────────────────────────────────────────
    def _section_lbl(self, parent, text):
        tk.Frame(parent, bg=BORDER, height=1).pack(fill=tk.X, pady=(12, 0))
        tk.Label(parent, text=text, font=("Courier New", 9, "bold"),
                 bg=BG_CARD, fg=ACCENT, anchor="w", pady=4).pack(fill=tk.X)

    def _field(self, parent, label, placeholder=""):
        tk.Label(parent, text=label, font=("Courier New", 9),
                 bg=BG_CARD, fg=TEXT_SEC, anchor="w").pack(fill=tk.X, pady=(4, 0))
        var   = tk.StringVar()
        entry = tk.Entry(parent, textvariable=var,
                         bg=BG_INPUT, fg=TEXT_PRI,
                         insertbackground=TEXT_PRI,
                         font=("Courier New", 10),
                         relief=tk.FLAT,
                         highlightthickness=1, highlightbackground=BORDER,
                         highlightcolor=ACCENT)
        entry.pack(fill=tk.X, ipady=5, pady=(2, 0))
        if placeholder:
            var.set(placeholder)
            entry.config(fg=TEXT_SEC)
            entry.bind("<FocusIn>",
                       lambda e, v=var, p=placeholder, w=entry: self._ph_in(v, p, w))
            entry.bind("<FocusOut>",
                       lambda e, v=var, p=placeholder, w=entry: self._ph_out(v, p, w))
        return var

    def _ph_in(self, var, placeholder, widget):
        if var.get() == placeholder:
            var.set("")
            widget.config(fg=TEXT_PRI)

    def _ph_out(self, var, placeholder, widget):
        if var.get() == "":
            var.set(placeholder)
            widget.config(fg=TEXT_SEC)

    def _dropdown(self, parent, label, options):
        tk.Label(parent, text=label, font=("Courier New", 9),
                 bg=BG_CARD, fg=TEXT_SEC, anchor="w").pack(fill=tk.X, pady=(4, 0))
        var = tk.StringVar(value=options[0])
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Dark.TCombobox",
                        fieldbackground=BG_INPUT, background=BG_INPUT,
                        foreground=TEXT_PRI, selectforeground=TEXT_PRI,
                        selectbackground=BG_INPUT, arrowcolor=ACCENT)
        cb = ttk.Combobox(parent, textvariable=var, values=options,
                          state="readonly", style="Dark.TCombobox",
                          font=("Courier New", 10))
        cb.pack(fill=tk.X, pady=(2, 0))
        return var

    def _checkbox(self, parent, label):
        var = tk.BooleanVar(value=False)
        tk.Checkbutton(parent, text=label, variable=var,
                       bg=BG_CARD, fg=TEXT_PRI, selectcolor=BG_PANEL,
                       activebackground=BG_CARD, activeforeground=ACCENT,
                       font=("Courier New", 9), anchor="w", pady=3,
                       highlightthickness=0, relief=tk.FLAT).pack(fill=tk.X)
        return var

    def _mk_btn(self, parent, text, cmd, color=ACCENT):
        return tk.Button(parent, text=text, command=cmd,
                         bg=color, fg=TEXT_PRI,
                         font=("Courier New", 10, "bold"),
                         relief=tk.FLAT, cursor="hand2",
                         padx=10, pady=8,
                         activebackground=ACCENT2, activeforeground="white",
                         borderwidth=0)

    # ── auto-sync manual header ───────────────────────────────────────────────
    def _sync_manual_header(self):
        """Keep the read-only vehicle fact line in sync with the form fields."""
        PLACEHOLDERS = {"e.g.  car_001"}
        vid = self._v_id.get().strip()
        if not vid or vid in PLACEHOLDERS:
            vid = "???"
        vtype = self._v_type.get().strip() or "car"
        self._manual_header_var.set(f"vehicle({vid}, {vtype}).  ← auto")

    # ── form reader ───────────────────────────────────────────────────────────
    def _read_form(self):
        PLACEHOLDERS = {"e.g.  car_001", "e.g.  85", "e.g.  3"}
        vid = self._v_id.get().strip()
        if not vid or vid in PLACEHOLDERS:
            messagebox.showerror("Missing Field", "Please enter a Vehicle ID.")
            return None
        spd = self._v_speed.get().strip()
        if spd.startswith("e.g."): spd = ""
        pax = self._v_pax.get().strip()
        if pax.startswith("e.g."): pax = ""
        return {
            "vehicle_id":      vid,
            "vehicle_type":    self._v_type.get(),
            "speed":           spd,
            "tl_red":          self._v_tl_red.get(),
            "crossed_line":    self._v_crossed.get(),
            "wrong_lane":      self._v_wrong.get(),
            "near_sb":         self._v_near_sb.get(),
            "direction":       self._v_dir.get(),
            "emergency":       self._v_emerg.get(),
            "helmet":          self._v_helmet.get(),
            "seatbelt":        self._v_belt.get(),
            "phone":           self._v_phone.get(),
            "passengers":      pax,
            "parked":          self._v_parked.get(),
            "no_parking_zone": self._v_nopk.get(),
        }

    # ── actions ───────────────────────────────────────────────────────────────
    def _on_check(self):
        use_manual = self._v_use_manual.get()
        manual_txt = self._v_manual.get("1.0", tk.END).strip()

        if use_manual:
            # Always take vehicle id/type from the form, merge with manual facts
            PLACEHOLDERS = {"e.g.  car_001"}
            vid = self._v_id.get().strip()
            if not vid or vid in PLACEHOLDERS:
                messagebox.showerror("Missing Field",
                                     "Enter a Vehicle ID in the form above — it is used even in manual mode.")
                return
            vtype = self._v_type.get().strip() or "car"

            # Start with the auto vehicle fact
            facts = [("frame_time", ["t_001"]), ("vehicle", [vid, vtype])]

            # Parse and append any extra facts from the text box
            if manual_txt:
                extra = parse_manual_query(manual_txt)
                # Remove duplicate vehicle fact if user typed one
                extra = [(n, a) for n, a in extra if n != "vehicle"]
                facts.extend(extra)
        else:
            data = self._read_form()
            if data is None:
                return
            facts = build_facts_from_form(data)
            vid   = data["vehicle_id"]

        self._status.config(text="Analysing…", fg=ACCENT)
        threading.Thread(
            target=lambda: self.after(
                0, lambda: self._display(simulate_violations(facts), vid, facts)),
            daemon=True).start()

    def _display(self, results: dict, vid: str, facts: list):
        vdata   = results.get(vid, {})
        n_viol  = sum(1 for s, _ in vdata.values() if s == VIOL)
        n_insuf = sum(1 for s, _ in vdata.values() if s == INSUF)

        self._current_vid = vid
        self._results     = vdata

        self._v_title.config(text=f"🚗  {vid.upper()}")
        if not vdata:
            self._v_badge.config(text="⚠️ Vehicle not found in facts.", fg=DANGER)
        else:
            parts = []
            if n_viol:  parts.append(f"⚠️ {n_viol} VIOLATION(S)")
            if n_insuf: parts.append(f"❓ {n_insuf} INSUFFICIENT")
            if not parts: parts.append("✅ NO VIOLATIONS")
            self._v_badge.config(
                text="  ".join(parts),
                fg=DANGER if n_viol else (WARN if n_insuf else SUCCESS))

        # ── violation cards ───────────────────────────────────────────────────
        for w in self._grid.winfo_children():
            w.destroy()
        cols = 3
        for i, vtype in enumerate(VIOLATION_TYPES):
            status, exp = vdata.get(vtype, (INSUF, "No data."))
            r, c = divmod(i, cols)
            self._make_card(self._grid, vtype, status, exp).grid(
                row=r, column=c, padx=6, pady=6, sticky="nsew")
            self._grid.columnconfigure(c, weight=1)
        self._cv.update_idletasks()
        self._cv.configure(scrollregion=self._cv.bbox("all"))

        # ── engine log ────────────────────────────────────────────────────────
        sep = "=" * 64
        lines = [sep,
                 f"  ANALYSIS REPORT  —  Vehicle: {vid.upper()}",
                 f"  {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                 sep, "",
                 "FACTS ASSERTED:"]
        for name, args in facts:
            lines.append(f"  {name}({', '.join(str(a) for a in args)})")
        lines += ["", "VIOLATION CHECK RESULTS:"]
        for vtype in VIOLATION_TYPES:
            status, exp = vdata.get(vtype, (INSUF, "No data."))
            flag  = ("[ VIOLATION  ]" if status == VIOL
                     else "[ INSUF DATA ]" if status == INSUF
                     else "[    CLEAR   ]")
            label = VIOLATION_LABELS.get(vtype, vtype)
            lines.append(f"  {flag}  {label}")
            lines.append(f"               → {exp}")
        lines += ["", sep]
        if n_viol:
            lines.append(f"  SUMMARY: {n_viol} violation(s):")
            for vt in VIOLATION_TYPES:
                if vdata.get(vt, (None,))[0] == VIOL:
                    lines.append(f"    •  {VIOLATION_LABELS[vt]}")
        else:
            lines.append("  SUMMARY: No confirmed violations.")
        if n_insuf:
            lines.append(f"  NOTE: {n_insuf} check(s) had insufficient data.")
            lines.append("        Provide more facts for a complete assessment.")
        lines.append(sep)

        self._report_text = "\n".join(lines)
        self._out.config(state=tk.NORMAL)
        self._out.delete("1.0", tk.END)
        self._out.insert(tk.END, self._report_text)
        self._out.config(state=tk.DISABLED)

        self._status.config(
            text=f"Done.  {vid}  —  {n_viol} violation(s)  |  {n_insuf} insufficient data.",
            fg=DANGER if n_viol else (WARN if n_insuf else SUCCESS))

        if REPORTLAB:
            self._pdf_btn.config(state=tk.NORMAL)

    # ── FIX 1: card colours ────────────────────────────────────────────────────
    def _make_card(self, parent, vtype: str, status: str, explanation: str):
        # DANGER (red) for violations, WARN (yellow) only for insufficient data
        if status == VIOL:
            color = DANGER          # "#da3633"  ← RED
            icon  = "🔴"
            badge = "✔ HIT"
        elif status == INSUF:
            color = WARN            # "#d29922"  ← yellow — only for missing data
            icon  = "❓"
            badge = "? DATA"
        else:
            color = SUCCESS         # "#2ea043"  ← green
            icon  = "🟢"
            badge = "✘ OK"

        card = tk.Frame(parent, bg=BG_CARD,
                        highlightthickness=2, highlightbackground=color)
        hdr  = tk.Frame(card, bg=color)
        hdr.pack(fill=tk.X)
        tk.Label(hdr, text=VIOLATION_LABELS.get(vtype, vtype),
                 font=("Courier New", 9, "bold"),
                 bg=color, fg="white", padx=8, pady=5,
                 anchor="w").pack(side=tk.LEFT, fill=tk.X, expand=True)
        tk.Label(hdr, text=badge, font=("Courier New", 8, "bold"),
                 bg=color, fg="white", padx=6).pack(side=tk.RIGHT)

        body = tk.Frame(card, bg=BG_CARD, pady=6, padx=8)
        body.pack(fill=tk.BOTH, expand=True)
        tk.Label(body, text=icon,
                 font=("Segoe UI Emoji", 20), bg=BG_CARD).pack()
        tk.Label(body, text=explanation,
                 font=("Courier New", 8),
                 bg=BG_CARD, fg=TEXT_SEC,
                 wraplength=200, justify=tk.CENTER).pack(pady=(3, 0))
        return card

    # ── PDF export ────────────────────────────────────────────────────────────
    def _on_export_pdf(self):
        if not REPORTLAB:
            messagebox.showerror("Not installed",
                                  "Install reportlab:\n  pip install reportlab")
            return
        if not self._current_vid:
            messagebox.showinfo("No data", "Run a violation check first.")
            return
        from tkinter.filedialog import asksaveasfilename
        fname = (f"traffic_report_{self._current_vid}_"
                 f"{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf")
        path = asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")],
            initialfile=fname,
            title="Save Report as PDF")
        if not path:
            return
        try:
            export_pdf(self._report_text, self._results, self._current_vid, path)
            messagebox.showinfo("Exported", f"PDF saved:\n{path}")
        except Exception as ex:
            messagebox.showerror("Export failed", str(ex))

    # ── demo ──────────────────────────────────────────────────────────────────
    def _on_demo(self):
        self._v_id.set("car_001");    self._v_type.set("car")
        self._v_speed.set("85");      self._v_tl_red.set(True)
        self._v_crossed.set(True);    self._v_wrong.set(False)
        self._v_near_sb.set(False);   self._v_dir.set("none")
        self._v_emerg.set(False);     self._v_helmet.set("")
        self._v_belt.set("no");       self._v_phone.set("")
        self._v_pax.set("");          self._v_parked.set(False)
        self._v_nopk.set(False);      self._v_use_manual.set(False)
        self._sync_manual_header()
        self._status.config(
            text="Demo loaded (car_001 — red light + speeding + no seatbelt). "
                 "Press CHECK VIOLATIONS.", fg=ACCENT2)

    # ── clear ─────────────────────────────────────────────────────────────────
    def _on_clear(self):
        self._v_id.set("");           self._v_type.set("car")
        self._v_speed.set("e.g.  85"); self._v_tl_red.set(False)
        self._v_crossed.set(False);   self._v_wrong.set(False)
        self._v_near_sb.set(False);   self._v_dir.set("none")
        self._v_emerg.set(False);     self._v_helmet.set("")
        self._v_belt.set("");         self._v_phone.set("")
        self._v_pax.set("e.g.  3");   self._v_parked.set(False)
        self._v_nopk.set(False);      self._v_use_manual.set(False)
        self._v_manual.delete("1.0", tk.END)
        self._sync_manual_header()
        for w in self._grid.winfo_children():
            w.destroy()
        self._out.config(state=tk.NORMAL)
        self._out.delete("1.0", tk.END)
        self._out.config(state=tk.DISABLED)
        self._v_title.config(text="Enter vehicle details and press CHECK VIOLATIONS →")
        self._v_badge.config(text="")
        self._pdf_btn.config(state=tk.DISABLED)
        self._current_vid  = ""
        self._report_text  = ""
        self._status.config(text="Form cleared.", fg=TEXT_SEC)


if __name__ == "__main__":
    app = TrafficApp()
    app.mainloop()