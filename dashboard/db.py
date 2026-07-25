from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey, JSON
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).parent.resolve()
db_path = BASE_DIR / "state" / "dashboard.db"
db_path.parent.mkdir(parents=True, exist_ok=True)

engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Scan(Base):
    __tablename__ = 'scans'
    id = Column(Integer, primary_key=True, index=True)
    market = Column(String(50), index=True)
    min_rr = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Metadata fields from the overall scan dictionary
    universe_meta = Column(JSON)
    source_summary = Column(JSON)
    passed_counts = Column(JSON)
    selected_counts = Column(JSON)
    count = Column(Integer)
    armed_count = Column(Integer)
    fallback_used = Column(JSON) # Boolean stored as JSON for simplicity, or we can use Integer
    data_policy = Column(String(100))
    source_reports = Column(JSON)
    
    results = relationship("ScanResult", back_populates="scan", cascade="all, delete-orphan")

class ScanResult(Base):
    __tablename__ = 'scan_results'
    id = Column(Integer, primary_key=True, index=True)
    scan_id = Column(Integer, ForeignKey('scans.id'))
    symbol = Column(String(50), index=True)
    name = Column(String(200))
    sector = Column(String(50))
    decision = Column(String(50))
    side = Column(String(50))
    score = Column(Integer)
    rr = Column(Float)
    
    # Nested detail objects are stored as JSON to avoid excessive normalization
    details = Column(JSON) 

    scan = relationship("Scan", back_populates="results")
