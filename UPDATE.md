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
8. **ReOrc-Inspired Editorial FinTech Frontend & Dual Themes (NEW - Oct 2026):**
   - ปรับโฉมหน้าตาใหม่ทั้งหมด โดยถอดดีไซน์สไตล์ AI Dark Neon ออก และนำ Design System สไตล์ [ReOrc.com](https://reorc.com/) มาใช้
   - โทนสี Warm Cream (`#fbfbf9`) + การ์ดสีขาวบริสุทธิ์ (`#ffffff`) เส้นขอบ Hairline คมกริบ (`#e2e8f0`)
   - ใช้ Typography คู่ฟอนต์ `Bricolage Grotesque` + `Plus Jakarta Sans` + `Noto Sans Thai` และ `JetBrains Mono` สำหรับตัวเลขการเงิน
   - สถานะระบบแบบ Live Pill Badge พร้อมจุดกระพริบเขียวสด (Pulsing Emerald Dot) ระดับ Sub-200ms
   - รองรับทั้งโหมด ReOrc Clean Light (ค่าเริ่มต้น) และ Sleek Slate Dark Mode
   - ผ่านการทดสอบ Full E2E Browser Testing ครบทุกฟังก์ชัน (Search, Filter, Chart Rendering, Drawer, Market Switch, Theme Toggle)

---

## 🏗️ 3. โครงสร้างซอร์สโค้ด (Project Directory Structure)

```text
stamp_trading/
├── dashboard/                  # ส่วนงาน Web Application & Database Layer
│   ├── app.py                  # Flask Web Server & API Routes (/api/scan, /api/sources)
│   ├── db.py                   # SQLAlchemy Database Models (Scan, ScanResult)
│   ├── templates/
│   │   └── dashboard.html      # หน้าจอ Frontend Dashboard (ECharts + Tailwind CSS)
│   └── state/                  # โฟลเดอร์เก็บไฟล์ SQLite Database (dashboard.db)
├── src/
│   └── th_smc/                 # ส่วนงาน Core Business & SMC Analytics Engine
│       ├── __init__.py
│       ├── engine.py           # ตัวประมวลผล SMC Analysis, Scoring และ Source Aggregation
│       └── scraper.py          # ตัวดึงข้อมูลราคา Real-time (TradingView & yfinance)
├── tests/                      # Automated Test Suites
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
*อัปเดตล่าสุดเมื่อ: 3 ตุลาคม 2026*
