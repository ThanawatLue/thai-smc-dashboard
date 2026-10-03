# Thai SMC Dashboard - Project Update & Deployment Guide

เอกสารสรุปสถานะโปรเจกต์ โครงสร้างระบบ รายละเอียดการ Deploy และแนวทางการพัฒนาต่อในอนาคต

---

## 📌 1. รายละเอียดการ Deploy (Deployment Overview)

- **Live Production URL:** [https://thai-smc-dashboard.onrender.com/](https://thai-smc-dashboard.onrender.com/)
- **Hosting Provider:** Render.com (Free Web Service Tier)
- **GitHub Repository:** [https://github.com/ThanawatLue/thai-smc-dashboard](https://github.com/ThanawatLue/thai-smc-dashboard)
- **Primary Branch:** `master`
- **Build & Server Configuration:**
  - **Environment:** Python 3.10+
  - **Build Command:** `pip install -r requirements.txt`
  - **Start Command:** `gunicorn --bind 0.0.0.0:$PORT --timeout 180 --workers 2 dashboard.app:app`
  - **Deployment Blueprint Files:** `Procfile`, `render.yaml`

---

## 🚀 2. สถานะโปรเจกต์ในปัจจุบัน (Current Features & Capabilities)

1. **Standalone Universe & Candidate Screening:**
   - สร้างและคัดกรอง universe จาก 4 แหล่งที่มา (Source Buckets):
     - `VCP` (Volatility Contraction Pattern Proxy)
     - `CANSLIM` (Quarterly Growth & SET100 Proxy)
     - `DIP_BUY` (Pullback to Support Proxy)
     - `MOMENTUM` (Breakout Momentum Proxy)
2. **SMC (Smart Money Concept) Scoring Engine:**
   - วิเคราะห์ Order Block, Fair Value Gap (FVG), Market Structure (BOS / CHoCH), Liquidity Sweep
   - คำนวณค่า Risk-to-Reward Ratio (กรองเฉพาะรายการที่ `RR >= 1:2.0`)
3. **Multi-Market Support:**
   - รองรับตลาดไทย (`TH`), ตลาดอเมริกา (`US`), ทองคำ (`GOLD`), และ `US_MEDIUM_TERM`
4. **Caching System:**
   - ระบบเก็บ Cache ผลการสแกนด้วย SQLite Database (`dashboard/state/dashboard.db`) ป้องกันการดึงข้อมูลซ้ำเกินจำเป็น (Cache 1 ชั่วโมง)
5. **Real-time Data Fetching:**
   - ดึงข้อมูลจาก TradingView Screener API และ Yahoo Finance (`yfinance`) พร้อมระบบ Fallback เมื่อข้อมูลไม่ตอบสนอง
6. **Automated Market Schedule (GitHub Actions):**
   - **ตลาดไทย (TH):** จันทร์–ศุกร์ เวลา 10:00 – 17:00 น. (เวลาไทย) ทุกๆ 1 ชั่วโมง
   - **ตลาดอเมริกา (US):** จันทร์–ศุกร์ เวลา 20:00 – 04:00 น. (เวลาไทย) ทุกๆ 1 ชั่วโมง
   - จัดการสแกนและอัปเดตข้อมูลอัตโนมัติผ่าน `.github/workflows/market_schedule.yml`
7. **Instant DB Serving & Pre-calculated Caching (Sub-500ms):**
   - ผู้ใช้ทั่วไปที่เข้ามาดูหน้าเว็บ จะได้รับการส่งคืนข้อมูลสแกนล่าสุดจาก Database ทันทีในระดับ < 0.5 วินาที โดยไม่ต้องรอดึงราคาใหม่
   - GitHub Actions ทำหน้าที่สแกนเบื้องหลังและอัปเดตข้อมูลสดลง Database ตามสเกดดูล
8. **ReOrc-Inspired Editorial FinTech Frontend & Dual Themes (Oct 2026):**
   - ปรับโฉมหน้าตาใหม่ทั้งหมด โดยถอดดีไซน์สไตล์ AI Dark Neon ออก และนำ Design System สไตล์ [ReOrc.com](https://reorc.com/) มาใช้
   - โทนสี Warm Cream (`#fbfbf9`) + การ์ดสีขาวบริสุทธิ์ (`#ffffff`) เส้นขอบ Hairline คมกริบ (`#e2e8f0`)
   - ใช้ Typography คู่ฟอนต์ `Bricolage Grotesque` + `Plus Jakarta Sans` + `Noto Sans Thai` และ `JetBrains Mono` สำหรับตัวเลขการเงิน
   - สถานะระบบแบบ Live Pill Badge พร้อมจุดกระพริบเขียวสด (Pulsing Emerald Dot) ระดับ Sub-200ms
   - รองรับทั้งโหมด ReOrc Clean Light (ค่าเริ่มต้น) และ Sleek Slate Dark Mode
   - ผ่านการทดสอบ Full E2E Browser Testing ครบทุกฟังก์ชัน (Search, Filter, Chart Rendering, Drawer, Market Switch, Theme Toggle)
9. **AI PORTFOLIO X-RAY PRO & DEEP THESIS ENGINE (NEW - Oct 2026):**
   - **Portfolio X-Ray Mode (เมื่อมีสินทรัพย์ 2 ตัวขึ้นไป):**
     - **Look-Through Effective Exposure:** ทะลุไส้ในของ ETF ทุกตัวเพื่อคำนวณหาน้ำหนักหุ้นจริง เช่น ถือ VOO + QQQM + SCHD ระบบจะรวมน้ำหนัก NVDA, AAPL, MSFT ที่ซ่อนอยู่ในแต่ละกองเข้าด้วยกัน
     - **Holding Overlap Matrix:** คำนวณค่าสัมประสิทธิ์การทับซ้อน $\sum \min(w_A, w_B)$ ระหว่างสินทรัพย์ทุกคู่ พร้อมแจ้งเตือนคู่ที่มีความซ้ำซ้อนสูง (>25%) ในภาษาไทยที่เข้าใจง่าย
     - **Max Drawdown ในรูปเงินจริง (Real Currency Loss):** แปลงการลดลงสูงสุดจากจุดพีคออกมาเป็นจำนวนเงินบาทหรือดอลลาร์จริงตามขนาดพอร์ต เช่น พอร์ต 1,000,000 บาท ลดลงสูงสุด -11.96% คิดเป็นเงินลดลง -119,559.95 บาท พร้อมคำนวณระยะเวลาฟื้นตัว (Recovery Time)
     - **Cross-Asset Weekly Correlation Matrix:** ประมวลผลสหสัมพันธ์ผลตอบแทนรวม (Total Return) โดย Resample เป็นรายสัปดาห์ (Friday Close) เพื่อให้สินทรัพย์ที่เทรด 24/7 เช่น Crypto (BTC) ทำงานร่วมกับตลาดหุ้นอเมริกาและพันธบัตรได้อย่างแม่นยำ
     - **Variance Attribution / Risk Contribution (%RC):** แยกองค์ประกอบความเสี่ยงจริงของแต่ละสินทรัพย์ผ่าน Covariance Matrix ($\%RC_i = \frac{w_i (\Sigma w)_i}{\sigma_p^2} \times 100\%$) เพื่อดูว่าสินทรัพย์ไหนเป็นตัวสร้างความผันผวนหลัก (Risk Dominator)
     - **Position Sizing & Rebalancing Action Plan:** ให้คำแนะนำปรับสัดส่วนเพื่อควบคุม Drawdown โดยคำนวณเป็นเปอร์เซ็นต์และเม็ดเงินจริงที่ควร TRIM หรือ Rebalance
     - **Concentration Analysis (HHI):** คำนวณ Herfindahl-Hirschman Index และจำนวนการเดิมพันอิสระ ($N_{\text{eff}} = 1/HHI$)
      - **Educational Callout "Overlap vs Correlation":** กล่องคำอธิบายเชิงการศึกษาตาม Master Prompt Section 7 ให้ผู้ใช้เข้าใจลึกซึ้งว่าการถือหุ้นซ้ำ (Overlap) ต่างจากการที่ราคาวิ่งตามกัน (Correlation) อย่างไร
      - **Blended Portfolio Expense Ratio (Fee Drag):** คำนวณค่าธรรมเนียมรวมถ่วงน้ำหนัก (Blended TER %) และคำนวณเงินค่าธรรมเนียมที่ถูก Drag จริงต่อปี (Annual Cash Drag) และสะสม 5 ปี เพื่อเตือนสตินักลงทุนเรื่องต้นทุนกองทุน
      - **Macro Stress Test & Sensitivity Matrix:** ตารางจำลอง 4 วิกฤตการณ์เศรษฐกิจมหภาค: (1) Tech De-Rating, (2) Rate Shock, (3) Global Recession, (4) Stagflation Crisis พร้อมคำนวณผลกระทบเป็น % และเม็ดเงินจริง และระบุ Cushion Asset
     - **CAGR, Annualized Volatility, Sharpe, Sortino, Calmar:** เปรียบเทียบเคียงข้างกับ S&P 500 (VOO Total Return)
   - **Deep Thesis & Reverse DCF Mode (เมื่อใส่หุ้นเดี่ยว 1 ตัว เช่น NVDA, RKLB):**
     - **Reverse DCF Implied Growth Solver:** ใช้ Bisection Algorithm คำนวณหาอัตราการเติบโตของ Free Cash Flow (FCF CAGR) เฉลี่ย 10 ปี ที่ตลาดกำลังสะท้อนอยู่ในราคาปัจจุบัน
     - **Reality Check & Scenarios:** ประเมินความสมเหตุสมผลของความคาดหวังตลาด และคำนวณราคาเหมาะสม 3 รูปแบบ (Bear / Base / Bull) พร้อม Margin of Safety
     - **Total Addressable Market (TAM) & S-Curve Analysis:** ประเมินขนาดโอกาสทางการตลาด ($B), Current Penetration %, S-Curve Lifecycle Stage, และ Key Structural Growth Catalysts
     - **3-Year Historical Financials Trend:** แสดงตารางย้อนหลังของรายได้ (Revenue), Gross Margin %, Operating Income, Operating Margin % และ Net Income
      - **Wall Street Analyst Consensus & Price Targets:** แสดง Consensus Rating (Strong Buy/Buy/Hold/Sell แปลไทย), จำนวนนักวิเคราะห์, กรอบราคาเป้าหมาย Target Price (Mean / High / Low) และคำนวณ Upside to Mean %
      - **Investment Verdict & Strategic Action:** สรุปบทวิเคราะห์เชิงกลยุทธ์ชี้ชัดการกระทำ (ACCUMULATE / HOLD / WAIT / CAUTION) พร้อม Base Case Fair Value และสรุปตรรกะความคุ้มค่า/ความเสี่ยงในการลงทุน
     - **Competitive Moat Analysis & Pre-Mortem:** วิเคราะห์คูเมืองธุรกิจ (Pricing power, High ROIC, Switching costs) และระบุข้อผิดพลาดที่จะทำให้ Thesis ล้มเหลว
   - **Standalone HTML Dashboard Export & One-Click Markdown Copy:**
     - ปุ่ม **HTML Export:** สร้างรายงาน HTML แบบ Single File ที่สมบูรณ์ในตัวเอง มีกราฟ ECharts/Chart.js ฝังพร้อมเปิดดูหรือแชร์ได้โดยไม่ต้องพึ่ง Server
     - ปุ่ม **Copy Text:** คัดลอกบทวิเคราะห์ทั้งหมดในรูปแบบ Structured Markdown ลง Clipboard ได้ทันทีเพียงคลิกเดียว นำไปแชร์หรือส่งต่อให้ AI วิเคราะห์ต่อได้อย่างสะดวก
   - **API Routes:**
     - `POST /api/xray/analyze` (JSON analysis)
     - `POST /api/xray/export-html` (Downloadable HTML report)
    - **Quality Assurance & End-to-End Testing (E2E):**
      - Unit Tests: 23/23 Automated Tests ผ่าน 100% ใน tests/test_portfolio_xray.py และ tests/test_engine.py
      - Browser E2E Testing: ผ่านการทดสอบด้วย Chrome DevTools MCP ทั้งโหมด Portfolio (Blended TER, Overlap vs Correlation, Macro Stress Test 4 Scenarios) และโหมด Deep Thesis (Consensus Rating, Price Target Range, Investment Verdict, Reverse DCF) ตรวจสอบแล้วไม่มี JavaScript Console Errors ใดๆ ทั้งสิ้น
10. **SMC Scanner Robust Fallback & Liquid Candidate Guarantee (Oct 2026 Fix):**
    - **ต้นตอของปัญหา:** บน Cloud Server (Render) ผู้ให้บริการ TradingView Screener จะส่ง HTTP 429 Too Many Requests เมื่อเรียกจาก Datacenter IPs ทำให้ระบบต้องใช้ Fallback Universe แต่เกิดปัญหา:
      1. ใน Fallback mode ตลาด TH คืนค่า `sector: "TH"` และไม่มี `market_cap` ทำให้หลุดเงื่อนไขการเป็น SET100 และ Swing Universe ส่งผลให้ไม่มีหุ้นตัวใดผ่านเกณฑ์คัดกรอง VCP, CANSLIM, DIP_BUY, MOMENTUM
      2. ตลาด US และ US_MEDIUM_TERM เดิม Fallback มีเพียงหุ้นตัวเดียว (`AAPL`)
      3. ตลาด GOLD คืนค่าเพียงสัญลักษณ์เดียว (`GC=F`)
      4. Database Cache บันทึกผลสแกนที่ว่างเปล่า (`count: 0, results: []`) ลง SQLite ทำให้ผู้ใช้เห็น "0 candidates evaluated" และตารางว่างตลอดเวลา
    - **แนวทางแก้ไขและปรับปรุง:**
      1. **Multi-Market Liquid Fallback Universe:** กำหนด `DEFAULT_TH_SYMBOLS` (44 หุ้น SET50/SET100), `DEFAULT_US_SYMBOLS` (30 หุ้น S&P 500 เมกะแคป), และ `DEFAULT_GOLD_SYMBOLS` (6 สินทรัพย์โภคภัณฑ์และโลหะมีค่า: `GC=F`, `SI=F`, `PL=F`, `GLD`, `IAU`, `GDX`)
      2. **Screen Metrics & Fundamental Baseline:** ปรับปรุง `_screen_metrics` ให้ส่งคืน sector และ market cap ที่ถูกต้องสำหรับแต่ละตลาด พร้อมค่าพื้นฐาน (ROE, Debt/Equity, FCF margin) เพื่อรองรับแท็บ US M.Term
      3. **Liquid Candidate Guarantee:** เพิ่มกลไกความปลอดภัย หากเกณฑ์ Breakout ไม่พบหุ้นตามเงื่อนไข (เช่น ตลาดพักฐาน) ระบบจะดึงหุ้นสภาพคล่องสูงของตลาดนั้นๆ (`CORE_MONITOR`) มาประเมิน SMC Structure, Order Block, FVG, RR, และ Decision ให้ครบถ้วน 15 รายการเสมอ ผู้ใช้จึงมีข้อมูลและกราฟให้ดูครบทุกแท็บ
      4. **Cache Integrity:** ปรับปรุง `_load_scan_cache` และ `_save_scan_cache` ใน `dashboard/app.py` ไม่ให้บันทึกหรือเสิร์ฟ Cache ที่มีจำนวนหุ้นเป็น 0
      5. **Automated Test Coverage:** เพิ่มชุดทดสอบจำลองเหตุการณ์ HTTP 429 ใน `tests/test_engine.py` ยืนยันว่าทุกตลาดต้องมี Candidates เสมอแม้เกิด 429

---

## 🏗️ 3. โครงสร้างซอร์สโค้ด (Project Directory Structure)

```text
stamp_trading/
├── dashboard/                  # ส่วนงาน Web Application & Database Layer
│   ├── app.py                  # Flask Web Server & API Routes (/api/scan, /api/xray/analyze, /api/xray/export-html)
│   ├── db.py                   # SQLAlchemy Database Models (Scan, ScanResult)
│   ├── templates/
│   │   └── dashboard.html      # หน้าจอ Frontend ReOrc FinTech (SMC Scanner + AI Portfolio X-Ray Tab)
│   └── state/                  # โฟลเดอร์เก็บไฟล์ SQLite Database (dashboard.db)
├── src/
│   ├── portfolio_xray/         # เครื่องมือวิเคราะห์ AI Portfolio X-Ray Pro & Deep Thesis
│   │   ├── __init__.py
│   │   ├── parser.py           # ตัวแกะข้อมูลพอร์ตอัจฉริยะ (รองรับสัดส่วน %, Equal weight, Crypto ticker)
│   │   ├── holdings_data.py    # ฐานข้อมูลและ Cache ไส้ใน ETF ชั้นนำ (VOO, QQQ, SCHD, SMH, TLT, GLD ฯลฯ)
│   │   ├── metrics.py          # Look-Through, Overlap Matrix, HHI, CAGR, Volatility, Drawdown เงินจริง, Sharpe
│   │   ├── reverse_dcf.py      # Bisection Solver คำนวณ Market Implied FCF Growth และ Bull/Base/Bear
│   │   ├── deep_thesis.py      # ดึงงบการเงินสดจาก yfinance, วิเคราะห์ Moat, Multiples, และ Pre-Mortem
│   │   ├── html_generator.py   # สร้างรายงาน Standalone HTML Report สไตล์ ReOrc
│   │   └── engine.py           # ตัวเชื่อมประสานหลัก (Coordinator Engine)
│   └── th_smc/                 # ส่วนงาน Core Business & SMC Analytics Engine
│       ├── __init__.py
│       ├── engine.py           # ตัวประมวลผล SMC Analysis, Scoring และ Source Aggregation
│       └── scraper.py          # ตัวดึงข้อมูลราคา Real-time (TradingView & yfinance)
├── tests/                      # Automated Test Suites (test_engine.py, test_portfolio_xray.py)
├── Procfile                    # สคริปต์ควบคุมการเริ่มรัน Production Gunicorn Server
├── render.yaml                 # ไฟล์ Infrastructure-as-Code Blueprint สำหรับ Render.com
├── requirements.txt            # รายการ Python Packages ทั้งหมดที่ใช้ใน Production
├── pyproject.toml              # การตั้งค่าโครงสร้างแพ็กเกจ Python (Setuptools)
├── UPDATE.md                   # เอกสารสรุปสถานะและการ Deploy (ไฟล์นี้)
└── README.md                   # เอกสารแนะนำโปรเจกต์เบื้องต้น
```

---

## 🛣️ 4. แผนงานและแนวทางการพัฒนาต่อในอนาคต (Future Roadmap)

1. **การป้องกัน Free Tier Sleep Mode (Keep-Alive):**
   - สมัครบริการฟรี เช่น [Cron-job.org](https://cron-job.org) หรือ [UptimeRobot](https://uptimerobot.com) เพื่อส่ง HTTP Ping ไปยัง `https://thai-smc-dashboard.onrender.com/` ทุกๆ 10 นาที เพื่อให้ Server พร้อมทำงานตลอด 24/7 โดยไม่เข้าโหมด Sleep
2. **การย้ายระบบ Database ไปใช้ Cloud Postgres:**
   - ปัจจุบัน SQLite จะรีเซ็ตไฟล์ Cache เมื่อ Render ทำการ Restart เครื่อง
   - ในอนาคตสามารถเปลี่ยน `dashboard/db.py` ไปใช้ **Neon.tech** หรือ **Supabase (Free PostgreSQL)** เพื่อให้ไฟล์ Cache คงอยู่ถาวร
3. **ระบบแจ้งเตือนผ่าน Line / Telegram (Alert Notification):**
   - เพิ่ม Background Worker สำหรับส่งการแจ้งเตือนเข้า Line Notify หรือ Telegram Bot เมื่อสแกนพบหุ้น SMC Score สูง และ `RR >= 1:3` ในช่วงเวลาตลาดเปิด
4. **การบันทึก Backtest History:**
   - บันทึกผลการสแกนย้อนหลังลง Database เพื่อนำมาประเมิน Win Rate และประสิทธิภาพของ SMC Setups ในอนาคต

---

## 🎨 5. การพัฒนาเพื่อเพิ่มความ Dynamic และ User-Friendly (เวอร์ชัน 3 ตุลาคม 2026)

ได้มีการปรับปรุงส่วนติดต่อผู้ใช้ (UI/UX) และระบบช่วยตัดสินใจเชิงปริมาณ 5 รายการใหญ่ เพื่อให้ผู้ใช้งานทั่วไปและนักเทรดเข้าใจง่ายและนำไปใช้เทรดจริงได้ทันที:

1. **📋 Plain-Thai Action Plan (สรุปแผนเทรดภาษาคน):**
   - มีการ์ดไฮไลต์สรุปคำแนะนำกลยุทธ์ภาษาไทยในการ์ดรายละเอียดของหุ้นทุกตัว ระบุสถานะชัดเจน (`🔥 พร้อมเข้าเทรด`, `👀 เฝ้าติดตาม`, `⏸️ ยังไม่เข้าเงื่อนไข`)
   - สรุปจุดเข้าซื้อ (Entry), จุดตัดขาดทุน (SL), และเป้าหมายกำไร (TP) พร้อมสัดส่วน Risk:Reward
   - มีปุ่ม **`คัดลอกแผนเทรด (Copy Plan)`** สำหรับกดคลิกเดียวเพื่อคัดลอกข้อความสรุปพร้อมส่งเข้า LINE, Telegram หรือบันทึกในสมุดจดเทรด

2. **🧮 Interactive Position Sizing & Risk Calculator (เครื่องคำนวณขนาดไม้และคุมความเสี่ยง):**
   - กล่องคำนวณจำนวนหุ้นอัตโนมัติตามจุด Stop Loss จริงของหุ้นตัวนั้นๆ
   - ผู้ใช้สามารถใส่ขนาดพอร์ต (เช่น 100,000 บาท) และเลือกระดับความเสี่ยง (% Risk เช่น 1%, 2%, 3%, 5%)
   - ระบบคำนวณให้ทันที: จำนวนหุ้นที่ควรซื้อ, มูลค่าเงินทุนที่ต้องใช้, จำนวนเงินขาดทุนสูงสุดหากโดน SL, และกำไรคาดหวังหากถึง TP

3. **📊 Visual Price Targets บนชาร์ต ECharts (เป้าหมายราคาและแถบ R:R บนกราฟจริง):**
   - วาดเส้นแนวนอนที่มีป้ายราคาเด่นชัดบนแท่งเทียน:
     - 🎯 **เส้นประสีเขียว:** `TP (Take Profit)` พร้อมเปอร์เซ็นต์กำไรคาดหวัง
     - 🔵 **เส้นทึบสีฟ้า:** `Entry` จุดเปิดออเดอร์
     - 🛑 **เส้นประสีแดง:** `SL (Stop Loss)` พร้อมเปอร์เซ็นต์ขาดทุน
   - เพิ่มแถบไฮไลต์โปร่งแสงจำลองเครื่องมือ Risk/Reward Box (โซนเขียว = กำไร, โซนแดง = ความเสี่ยง)

4. **ℹ️ Interactive Tooltips (ระบบคำอธิบายศัพท์เทคนิค Popover):**
   - เพิ่มไอคอน `ℹ️` บนหัวตาราง (`Decision`, `Score`, `RR`, `Structure`, `Liquidity`) และกล่อง Setup (`Demand Zone`, `Supply Zone`, `Fair Value Gap`)
   - นำเมาส์ชี้หรือแตะเพื่อดูคำอธิบายความหมายภาษาไทยแบบเข้าใจง่าย ไม่ต้องเปิดตำราหาศัพท์

5. **⚡ Quick Filter Chips (ชิปคัดกรองด่วนคลิกเดียว):**
   - แถบปุ่มคัดกรองด่วนบนหัวตาราง: `ทั้งหมด (All)`, `🔥 Armed Setups`, `🎯 R:R ≥ 2.5`, `🟢 Bullish Bias`, `⚡ ใกล้จุดเข้า (≤ 2%)`
   - ช่วยให้นักเทรดโฟกัสเฉพาะหุ้นที่มีโอกาสทำกำไรสูงได้ในคลิกเดียว

---
*อัปเดตล่าสุดเมื่อ: 3 ตุลาคม 2026*

