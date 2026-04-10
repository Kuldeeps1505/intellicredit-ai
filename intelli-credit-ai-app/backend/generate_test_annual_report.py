"""
Generate a realistic Annual Report PDF for testing IntelliCredit AI.
Company: Sunrise Exports International Pvt Ltd (the fraud/reject demo case)
Run: python generate_test_annual_report.py
Output: test_documents/Annual_Report_Sunrise_Exports_FY2024.pdf
"""
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, PageBreak
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
import os

os.makedirs("test_documents", exist_ok=True)
OUTPUT = "test_documents/Annual_Report_Sunrise_Exports_FY2024.pdf"

# ── Colour palette ────────────────────────────────────────────────────────────
NAVY   = colors.HexColor("#1a2744")
BLUE   = colors.HexColor("#2563eb")
LGRAY  = colors.HexColor("#f1f5f9")
MGRAY  = colors.HexColor("#94a3b8")
RED    = colors.HexColor("#dc2626")
GREEN  = colors.HexColor("#16a34a")
WHITE  = colors.white
BLACK  = colors.black

doc = SimpleDocTemplate(
    OUTPUT, pagesize=A4,
    leftMargin=2*cm, rightMargin=2*cm,
    topMargin=2*cm, bottomMargin=2*cm,
)

styles = getSampleStyleSheet()

def S(name, **kw):
    return ParagraphStyle(name, parent=styles["Normal"], **kw)

H1  = S("H1",  fontSize=22, textColor=NAVY,  spaceAfter=6,  spaceBefore=12, fontName="Helvetica-Bold")
H2  = S("H2",  fontSize=14, textColor=NAVY,  spaceAfter=4,  spaceBefore=10, fontName="Helvetica-Bold")
H3  = S("H3",  fontSize=11, textColor=BLUE,  spaceAfter=3,  spaceBefore=8,  fontName="Helvetica-Bold")
BODY= S("BODY",fontSize=9,  textColor=BLACK, spaceAfter=4,  leading=14)
SMALL=S("SM",  fontSize=8,  textColor=MGRAY, spaceAfter=2)
CTR = S("CTR", fontSize=10, textColor=NAVY,  alignment=TA_CENTER, fontName="Helvetica-Bold")
RT  = S("RT",  fontSize=8,  textColor=MGRAY, alignment=TA_RIGHT)

def hr(): return HRFlowable(width="100%", thickness=0.5, color=MGRAY, spaceAfter=6, spaceBefore=6)
def sp(h=0.3): return Spacer(1, h*cm)

def tbl(data, col_widths, style_cmds=None):
    base = [
        ("FONTNAME",  (0,0), (-1,0),  "Helvetica-Bold"),
        ("FONTSIZE",  (0,0), (-1,-1), 8),
        ("BACKGROUND",(0,0), (-1,0),  NAVY),
        ("TEXTCOLOR", (0,0), (-1,0),  WHITE),
        ("ROWBACKGROUNDS",(0,1),(-1,-1),[WHITE, LGRAY]),
        ("GRID",      (0,0), (-1,-1), 0.3, MGRAY),
        ("TOPPADDING",(0,0), (-1,-1), 4),
        ("BOTTOMPADDING",(0,0),(-1,-1),4),
        ("LEFTPADDING",(0,0),(-1,-1), 6),
    ]
    if style_cmds:
        base.extend(style_cmds)
    t = Table(data, colWidths=col_widths)
    t.setStyle(TableStyle(base))
    return t

story = []

# ══════════════════════════════════════════════════════════════════════════════
# COVER PAGE
# ══════════════════════════════════════════════════════════════════════════════
story += [
    sp(3),
    Paragraph("ANNUAL REPORT", S("cv1", fontSize=13, textColor=BLUE, alignment=TA_CENTER, fontName="Helvetica-Bold")),
    sp(0.3),
    Paragraph("2023 – 2024", S("cv2", fontSize=32, textColor=NAVY, alignment=TA_CENTER, fontName="Helvetica-Bold")),
    sp(0.5),
    HRFlowable(width="60%", thickness=2, color=BLUE, hAlign="CENTER"),
    sp(0.5),
    Paragraph("SUNRISE EXPORTS INTERNATIONAL PRIVATE LIMITED", S("cv3", fontSize=16, textColor=NAVY, alignment=TA_CENTER, fontName="Helvetica-Bold")),
    sp(0.3),
    Paragraph("CIN: U51909DL2017PTC456789", S("cv4", fontSize=10, textColor=MGRAY, alignment=TA_CENTER)),
    Paragraph("PAN: AADCS5678G  |  GSTIN: 07AADCS5678G1Z2", S("cv4", fontSize=10, textColor=MGRAY, alignment=TA_CENTER)),
    sp(0.3),
    Paragraph("Registered Office: 412, Okhla Industrial Estate Phase III, New Delhi – 110020", S("cv5", fontSize=9, textColor=MGRAY, alignment=TA_CENTER)),
    sp(2),
    Paragraph("Import / Export Trading  |  Established 2017", S("cv6", fontSize=10, textColor=BLUE, alignment=TA_CENTER)),
    PageBreak(),
]

# ══════════════════════════════════════════════════════════════════════════════
# COMPANY OVERVIEW
# ══════════════════════════════════════════════════════════════════════════════
story += [
    Paragraph("1. Company Overview", H2),
    hr(),
    Paragraph(
        "Sunrise Exports International Private Limited is a Delhi-based import/export trading company "
        "incorporated in 2017 under the Companies Act, 2013. The company is engaged in the trading of "
        "textile goods, garments, and allied products across South-East Asian and Middle Eastern markets. "
        "The company holds an active Import Export Code (IEC) issued by DGFT and is registered under GST "
        "with GSTIN 07AADCS5678G1Z2.",
        BODY),
    sp(),
    tbl(
        [["Particulars", "Details"],
         ["Company Name",        "Sunrise Exports International Pvt Ltd"],
         ["CIN",                 "U51909DL2017PTC456789"],
         ["PAN",                 "AADCS5678G"],
         ["GSTIN",               "07AADCS5678G1Z2"],
         ["Date of Incorporation","14 March 2017"],
         ["Registered Office",   "412, Okhla Industrial Estate Phase III, New Delhi – 110020"],
         ["Nature of Business",  "Import / Export Trading — Textiles & Garments"],
         ["Authorised Capital",  "₹5,00,00,000"],
         ["Paid-up Capital",     "₹2,50,00,000"],
         ["Auditors",            "M/s Sharma & Associates, Chartered Accountants, New Delhi"],
         ["Bankers",             "Punjab National Bank, Canara Bank"],
        ],
        [6*cm, 10*cm]
    ),
    sp(),
]

# ══════════════════════════════════════════════════════════════════════════════
# DIRECTORS
# ══════════════════════════════════════════════════════════════════════════════
story += [
    Paragraph("2. Board of Directors", H2),
    hr(),
    tbl(
        [["Name", "DIN", "Designation", "Date of Appointment"],
         ["Mr. Rajesh Kumar Gupta",  "00234567", "Managing Director",    "14 Mar 2017"],
         ["Mrs. Sunita Gupta",       "00234568", "Whole-time Director",  "14 Mar 2017"],
         ["Mr. Anil Sharma",         "00891234", "Independent Director", "01 Apr 2019"],
        ],
        [5.5*cm, 3*cm, 4.5*cm, 4*cm]
    ),
    sp(),
    Paragraph(
        "<b>Note:</b> Mr. Rajesh Kumar Gupta (DIN: 00234567) is also a director in two other entities — "
        "Zenith Trading Co Pvt Ltd and Golden Exports Ltd — both of which have been classified as "
        "Non-Performing Assets (NPA) by their respective lenders as of FY2023.",
        S("note", fontSize=8, textColor=RED, spaceAfter=4)),
    sp(),
]

# ══════════════════════════════════════════════════════════════════════════════
# FINANCIAL HIGHLIGHTS
# ══════════════════════════════════════════════════════════════════════════════
story += [
    Paragraph("3. Financial Highlights (₹ in Lakhs)", H2),
    hr(),
    tbl(
        [["Particulars",              "FY 2021-22", "FY 2022-23", "FY 2023-24"],
         ["Revenue from Operations",  "1,842.50",   "1,680.30",   "1,539.20"],
         ["Other Income",             "12.40",       "9.80",       "7.20"],
         ["Total Income",             "1,854.90",   "1,690.10",   "1,546.40"],
         ["Cost of Goods Sold",       "1,142.35",   "1,058.59",   "985.09"],
         ["Gross Profit",             "712.55",      "631.51",     "561.31"],
         ["Employee Benefit Expenses","165.82",      "151.23",     "153.92"],
         ["Other Operating Expenses", "128.97",      "134.42",     "138.53"],
         ["EBITDA",                   "417.76",      "345.86",     "268.86"],
         ["Depreciation",             "55.27",       "50.41",      "46.18"],
         ["EBIT",                     "362.49",      "295.45",     "222.68"],
         ["Finance Costs",            "184.25",      "210.48",     "254.37"],
         ["Profit Before Tax (PBT)",  "178.24",      "84.97",      "-31.69"],
         ["Tax Expense",              "44.56",       "21.24",      "0.00"],
         ["Profit After Tax (PAT)",   "133.68",      "63.73",      "-31.69"],
        ],
        [6.5*cm, 3.5*cm, 3.5*cm, 3.5*cm],
        [("TEXTCOLOR",(0,9),(-1,9), RED),
         ("TEXTCOLOR",(0,13),(-1,13), RED),
         ("TEXTCOLOR",(0,14),(-1,14), RED),
         ("FONTNAME",(0,8),(-1,8),"Helvetica-Bold"),
         ("FONTNAME",(0,14),(-1,14),"Helvetica-Bold"),
        ]
    ),
    sp(),
]

# ══════════════════════════════════════════════════════════════════════════════
# BALANCE SHEET
# ══════════════════════════════════════════════════════════════════════════════
story += [
    Paragraph("4. Balance Sheet as at 31 March 2024 (₹ in Lakhs)", H2),
    hr(),
    Paragraph("EQUITY & LIABILITIES", H3),
    tbl(
        [["Particulars",                    "FY 2022-23", "FY 2023-24"],
         ["Share Capital",                  "250.00",     "250.00"],
         ["Reserves & Surplus",             "312.48",     "280.79"],
         ["Total Equity (Net Worth)",        "562.48",     "530.79"],
         ["Long-Term Borrowings",            "842.72",     "938.45"],
         ["Short-Term Borrowings",           "561.81",     "625.63"],
         ["Total Debt",                      "1,404.53",   "1,564.08"],
         ["Trade Payables",                  "284.37",     "312.54"],
         ["Other Current Liabilities",       "142.18",     "168.32"],
         ["Total Current Liabilities",       "426.55",     "480.86"],
         ["TOTAL EQUITY & LIABILITIES",      "2,393.56",   "2,575.73"],
        ],
        [7*cm, 4*cm, 4*cm],
        [("FONTNAME",(0,3),(-1,3),"Helvetica-Bold"),
         ("FONTNAME",(0,6),(-1,6),"Helvetica-Bold"),
         ("FONTNAME",(0,10),(-1,10),"Helvetica-Bold"),
         ("BACKGROUND",(0,10),(-1,10), NAVY),
         ("TEXTCOLOR",(0,10),(-1,10), WHITE),
        ]
    ),
    sp(0.4),
    Paragraph("ASSETS", H3),
    tbl(
        [["Particulars",                    "FY 2022-23", "FY 2023-24"],
         ["Fixed Assets (Net Block)",        "684.32",     "638.14"],
         ["Capital Work-in-Progress",        "28.45",      "18.20"],
         ["Total Non-Current Assets",        "712.77",     "656.34"],
         ["Inventories",                     "542.18",     "612.47"],
         ["Trade Receivables",               "684.37",     "748.52"],
         ["Cash & Bank Balances",            "284.12",     "198.34"],
         ["Other Current Assets",            "170.12",     "360.06"],
         ["Total Current Assets",            "1,680.79",   "1,919.39"],
         ["TOTAL ASSETS",                    "2,393.56",   "2,575.73"],
        ],
        [7*cm, 4*cm, 4*cm],
        [("FONTNAME",(0,3),(-1,3),"Helvetica-Bold"),
         ("FONTNAME",(0,8),(-1,8),"Helvetica-Bold"),
         ("BACKGROUND",(0,8),(-1,8), NAVY),
         ("TEXTCOLOR",(0,8),(-1,8), WHITE),
        ]
    ),
    sp(),
]

# ══════════════════════════════════════════════════════════════════════════════
# CASH FLOW
# ══════════════════════════════════════════════════════════════════════════════
story += [
    Paragraph("5. Cash Flow Statement (₹ in Lakhs)", H2),
    hr(),
    tbl(
        [["Particulars",                              "FY 2022-23", "FY 2023-24"],
         ["Net Profit Before Tax",                    "84.97",      "-31.69"],
         ["Add: Depreciation",                        "50.41",      "46.18"],
         ["Add: Finance Costs",                       "210.48",     "254.37"],
         ["Changes in Working Capital",               "-184.32",    "-312.48"],
         ["Cash from Operations (CFO)",               "161.54",     "-43.62"],
         ["Capital Expenditure",                      "-42.18",     "-38.45"],
         ["Cash from Investing (CFI)",                "-42.18",     "-38.45"],
         ["Proceeds from Borrowings (Net)",           "84.37",      "159.55"],
         ["Finance Costs Paid",                       "-210.48",    "-254.37"],
         ["Cash from Financing (CFF)",                "-126.11",    "-94.82"],
         ["Net Change in Cash",                       "-6.75",      "-176.89"],
         ["Opening Cash Balance",                     "290.87",     "284.12"],
         ["Closing Cash Balance",                     "284.12",     "198.34"],  # page 42 reference
        ],
        [8*cm, 3.5*cm, 3.5*cm],
        [("TEXTCOLOR",(0,5),(-1,5), RED),
         ("FONTNAME",(0,5),(-1,5),"Helvetica-Bold"),
         ("FONTNAME",(0,11),(-1,11),"Helvetica-Bold"),
        ]
    ),
    sp(),
    Paragraph(
        "<b>Note on CFO:</b> Cash from Operations turned negative in FY2024 (₹-43.62 Lakhs) primarily "
        "due to a significant increase in trade receivables (₹748.52 Lakhs) and inventory build-up "
        "(₹612.47 Lakhs), indicating potential collection issues and slow-moving stock.",
        S("warn", fontSize=8, textColor=RED, spaceAfter=4)),
    sp(),
]

# ══════════════════════════════════════════════════════════════════════════════
# KEY FINANCIAL RATIOS
# ══════════════════════════════════════════════════════════════════════════════
story += [
    Paragraph("6. Key Financial Ratios", H2),
    hr(),
    tbl(
        [["Ratio",                  "FY 2021-22", "FY 2022-23", "FY 2023-24", "Benchmark"],
         ["Current Ratio",          "1.21",        "1.08",       "0.78",       "> 1.50"],
         ["Quick Ratio",            "0.92",        "0.78",       "0.52",       "> 1.00"],
         ["Debt / Equity Ratio",    "1.82",        "2.49",       "2.95",       "< 2.00"],
         ["Interest Coverage Ratio","2.81",        "1.64",       "0.88",       "> 2.50"],
         ["DSCR",                   "1.28",        "0.98",       "0.65",       "> 1.25"],
         ["EBITDA Margin (%)",      "22.67",       "20.58",      "17.49",      "> 15.00"],
         ["Net Profit Margin (%)",  "7.26",        "3.79",       "-2.06",      "> 5.00"],
         ["Return on Equity (%)",   "23.76",       "11.33",      "-5.97",      "> 12.00"],
         ["Return on Assets (%)",   "7.24",        "3.42",       "-1.23",      "> 6.00"],
         ["Asset Turnover (x)",     "0.98",        "0.85",       "0.72",       "> 1.00"],
         ["Receivables Days",       "135",         "148",        "177",        "< 90"],
         ["Inventory Days",         "72",          "85",         "145",        "< 90"],
         ["GST vs ITR Variance (%)", "3.2",        "8.5",        "26.7",       "< 5.00"],
        ],
        [5.5*cm, 2.5*cm, 2.5*cm, 2.5*cm, 2.5*cm],
        [("TEXTCOLOR",(1,3),(4,3), RED),
         ("TEXTCOLOR",(1,4),(4,4), RED),
         ("TEXTCOLOR",(1,5),(4,5), RED),
         ("TEXTCOLOR",(1,6),(4,6), RED),
         ("TEXTCOLOR",(1,7),(4,7), RED),
         ("TEXTCOLOR",(1,8),(4,8), RED),
         ("TEXTCOLOR",(1,9),(4,9), RED),
         ("TEXTCOLOR",(1,10),(4,10), RED),
         ("TEXTCOLOR",(1,11),(4,11), RED),
         ("TEXTCOLOR",(1,12),(4,12), RED),
         ("TEXTCOLOR",(1,13),(4,13), RED),
        ]
    ),
    sp(),
]

# ══════════════════════════════════════════════════════════════════════════════
# GST COMPLIANCE
# ══════════════════════════════════════════════════════════════════════════════
story += [
    Paragraph("7. GST Compliance Summary", H2),
    hr(),
    Paragraph(
        "The company is registered under GST with GSTIN 07AADCS5678G1Z2. "
        "GSTR-1, GSTR-2A, and GSTR-3B returns have been filed for all quarters of FY2023-24. "
        "However, a significant variance has been observed between ITC available as per GSTR-2A "
        "and ITC claimed in GSTR-3B, as detailed below:",
        BODY),
    sp(0.3),
    tbl(
        [["Quarter",   "GSTR-2A ITC Available (₹L)", "GSTR-3B ITC Claimed (₹L)", "Variance (₹L)", "Flag"],
         ["Q1 FY24",   "112.40",  "118.20",  "5.80",   "Low"],
         ["Q2 FY24",   "98.30",   "151.20",  "52.90",  "CRITICAL"],
         ["Q3 FY24",   "84.50",   "139.40",  "54.90",  "CRITICAL"],
         ["Q4 FY24",   "121.80",  "185.40",  "63.60",  "CRITICAL"],
         ["Total FY24","416.00",  "594.20",  "178.20", "CRITICAL"],
        ],
        [3*cm, 4.5*cm, 4.5*cm, 3*cm, 2*cm],
        [("TEXTCOLOR",(4,2),(4,5), RED),
         ("FONTNAME",(4,2),(4,5),"Helvetica-Bold"),
         ("BACKGROUND",(0,5),(-1,5), colors.HexColor("#fee2e2")),
         ("FONTNAME",(0,5),(-1,5),"Helvetica-Bold"),
        ]
    ),
    sp(0.3),
    Paragraph(
        "<b>⚠ ITC Fraud Risk:</b> Total suspect ITC of ₹178.20 Lakhs (₹1.78 Crores) has been identified "
        "across Q2–Q4 FY2024. The variance exceeds 40% in Q2 and Q3, which is a critical indicator of "
        "potential Input Tax Credit fraud under Section 16 of the CGST Act, 2017.",
        S("alert", fontSize=8, textColor=RED, spaceAfter=4)),
    sp(),
]

# ══════════════════════════════════════════════════════════════════════════════
# LITIGATION
# ══════════════════════════════════════════════════════════════════════════════
story += [
    Paragraph("8. Legal & Regulatory Matters", H2),
    hr(),
    tbl(
        [["Case",          "Forum",       "Nature",          "Amount (₹L)", "Status"],
         ["NCLT/2023/DEL/4821", "NCLT Delhi", "Insolvency Petition by creditor", "420.00", "Pending"],
         ["DRT/2022/DEL/1124",  "DRT Delhi",  "Recovery of dues — PNB",          "284.50", "Pending"],
         ["GST/ENF/2024/0892",  "GST Dept",   "ITC mismatch notice",             "178.20", "Under Reply"],
        ],
        [4.5*cm, 3*cm, 4.5*cm, 2.5*cm, 2.5*cm],
        [("TEXTCOLOR",(4,1),(4,3), RED),
         ("FONTNAME",(0,1),(-1,3),"Helvetica"),
        ]
    ),
    sp(),
    Paragraph(
        "The NCLT petition (Case No. NCLT/2023/DEL/4821) was filed by a trade creditor for ₹4.20 Crores "
        "in November 2023. The company has filed its reply and the matter is sub-judice. "
        "The DRT case relates to a term loan default with Punjab National Bank.",
        BODY),
    sp(),
]

# ══════════════════════════════════════════════════════════════════════════════
# AUDITOR'S REPORT EXTRACT
# ══════════════════════════════════════════════════════════════════════════════
story += [
    Paragraph("9. Independent Auditor's Report (Extract)", H2),
    hr(),
    Paragraph("<b>Qualified Opinion</b>", S("qo", fontSize=10, textColor=RED, fontName="Helvetica-Bold", spaceAfter=4)),
    Paragraph(
        "We have audited the accompanying financial statements of Sunrise Exports International Private "
        "Limited for the year ended 31 March 2024. In our opinion, except for the matters described in "
        "the Basis for Qualified Opinion paragraph, the financial statements give a true and fair view.",
        BODY),
    sp(0.2),
    Paragraph("<b>Basis for Qualified Opinion:</b>", S("bq", fontSize=9, fontName="Helvetica-Bold", spaceAfter=2)),
    Paragraph(
        "1. Trade receivables of ₹748.52 Lakhs include debts outstanding for more than 180 days "
        "amounting to ₹312.40 Lakhs. The company has not made adequate provision for doubtful debts "
        "as required under Ind AS 109. Had such provision been made, the net loss would have been "
        "higher by approximately ₹156.20 Lakhs.",
        BODY),
    Paragraph(
        "2. Input Tax Credit claimed in GSTR-3B exceeds ITC available in GSTR-2A by ₹178.20 Lakhs "
        "for FY2023-24. The company has not provided for the potential GST liability arising therefrom.",
        BODY),
    Paragraph(
        "3. The company's current liabilities exceed current assets (Current Ratio: 0.78x), raising "
        "substantial doubt about the company's ability to continue as a going concern.",
        S("gc", fontSize=9, textColor=RED, spaceAfter=4)),
    sp(),
    Paragraph("M/s Sharma & Associates", S("sig", fontSize=9, fontName="Helvetica-Bold", spaceAfter=2)),
    Paragraph("Chartered Accountants | FRN: 012345N", SMALL),
    Paragraph("Date: 15 July 2024 | Place: New Delhi", SMALL),
    sp(),
]

# ══════════════════════════════════════════════════════════════════════════════
# NOTES TO ACCOUNTS
# ══════════════════════════════════════════════════════════════════════════════
story += [
    Paragraph("10. Notes to Accounts (Selected)", H2),
    hr(),
    Paragraph("<b>Note 1 — Revenue from Operations</b>", H3),
    tbl(
        [["Particulars",                "FY 2022-23 (₹L)", "FY 2023-24 (₹L)"],
         ["Export Sales",               "1,260.22",         "1,154.40"],
         ["Domestic Sales",             "420.08",           "384.80"],
         ["Revenue from Operations",    "1,680.30",         "1,539.20"],
        ],
        [7*cm, 4*cm, 4*cm],
        [("FONTNAME",(0,3),(-1,3),"Helvetica-Bold")]
    ),
    sp(0.4),
    Paragraph("<b>Note 2 — Trade Receivables</b>", H3),
    tbl(
        [["Ageing",                     "FY 2022-23 (₹L)", "FY 2023-24 (₹L)"],
         ["Outstanding < 90 days",      "284.12",           "248.40"],
         ["Outstanding 90–180 days",    "216.08",           "187.72"],
         ["Outstanding > 180 days",     "184.17",           "312.40"],
         ["Total Trade Receivables",    "684.37",           "748.52"],
        ],
        [7*cm, 4*cm, 4*cm],
        [("TEXTCOLOR",(0,3),(0,3), RED),
         ("TEXTCOLOR",(1,3),(2,3), RED),
         ("FONTNAME",(0,4),(-1,4),"Helvetica-Bold")]
    ),
    sp(0.4),
    Paragraph("<b>Note 3 — Borrowings</b>", H3),
    tbl(
        [["Lender",              "Type",           "Rate (%)", "FY 2022-23 (₹L)", "FY 2023-24 (₹L)"],
         ["Punjab National Bank","Term Loan",      "11.50",    "542.18",           "584.32"],
         ["Canara Bank",         "Cash Credit",    "10.75",    "300.54",           "354.13"],
         ["Canara Bank",         "Working Capital","10.75",    "261.27",           "271.50"],
         ["NBFCs (Unsecured)",   "Unsecured Loan", "18.00",    "300.54",           "354.13"],
         ["Total Borrowings",    "",               "",         "1,404.53",         "1,564.08"],
        ],
        [4*cm, 3*cm, 2*cm, 3.5*cm, 3.5*cm],
        [("FONTNAME",(0,5),(-1,5),"Helvetica-Bold"),
         ("TEXTCOLOR",(3,4),(4,4), RED)]
    ),
    sp(),
]

# ══════════════════════════════════════════════════════════════════════════════
# MANAGEMENT DISCUSSION
# ══════════════════════════════════════════════════════════════════════════════
story += [
    Paragraph("11. Management Discussion & Analysis", H2),
    hr(),
    Paragraph("<b>Industry Outlook:</b>", S("md1", fontSize=9, fontName="Helvetica-Bold", spaceAfter=2)),
    Paragraph(
        "The Indian textile export sector faced headwinds in FY2024 due to global demand slowdown, "
        "rising raw material costs, and increased competition from Bangladesh and Vietnam. "
        "India's textile exports declined by approximately 8% in FY2024 vs FY2023.",
        BODY),
    Paragraph("<b>Company Performance:</b>", S("md2", fontSize=9, fontName="Helvetica-Bold", spaceAfter=2)),
    Paragraph(
        "Revenue declined by 8.4% from ₹1,680.30 Lakhs in FY2023 to ₹1,539.20 Lakhs in FY2024. "
        "EBITDA margin compressed from 20.58% to 17.49% due to higher finance costs and operating "
        "expenses. The company reported a net loss of ₹31.69 Lakhs in FY2024 compared to a profit "
        "of ₹63.73 Lakhs in FY2023.",
        BODY),
    Paragraph("<b>Risks & Concerns:</b>", S("md3", fontSize=9, fontName="Helvetica-Bold", spaceAfter=2)),
    Paragraph(
        "• High buyer concentration: Top 3 buyers (Zenith Trading Co, Golden Exports Ltd, Starline Impex) "
        "account for approximately 68.4% of total revenue, creating significant concentration risk.\n"
        "• Liquidity stress: Current ratio of 0.78x indicates inability to meet short-term obligations.\n"
        "• Debt servicing: DSCR of 0.65x indicates the company cannot fully service its debt from operations.\n"
        "• GST compliance: Significant ITC discrepancy of ₹178.20 Lakhs under regulatory scrutiny.",
        BODY),
    sp(),
]

# ══════════════════════════════════════════════════════════════════════════════
# DECLARATION
# ══════════════════════════════════════════════════════════════════════════════
story += [
    Paragraph("12. Declaration by Directors", H2),
    hr(),
    Paragraph(
        "We, the undersigned Directors of Sunrise Exports International Private Limited, hereby declare "
        "that the financial statements for the year ended 31 March 2024 have been prepared in accordance "
        "with the Companies Act, 2013, and applicable Indian Accounting Standards (Ind AS).",
        BODY),
    sp(0.5),
    tbl(
        [["Name",                   "DIN",       "Signature",    "Date"],
         ["Rajesh Kumar Gupta",     "00234567",  "Sd/-",         "15 Jul 2024"],
         ["Sunita Gupta",           "00234568",  "Sd/-",         "15 Jul 2024"],
        ],
        [5*cm, 3*cm, 3*cm, 3*cm]
    ),
    sp(),
    Paragraph("Place: New Delhi | Date: 15 July 2024", SMALL),
]

# ── Build PDF ─────────────────────────────────────────────────────────────────
doc.build(story)
print(f"✅  Annual Report generated: {OUTPUT}")
print(f"    File size: {os.path.getsize(OUTPUT) / 1024:.1f} KB")
