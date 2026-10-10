import datetime
from sqlalchemy import Column, Integer, BigInteger, String, Text, Date, DateTime, Boolean
from sqlalchemy.orm import declarative_base
Base = declarative_base()

class DocumentMetadataRecord(Base):
    __tablename__ = 'doc_metadata'
    document_id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    file_name = Column(String(255), nullable=False)
    storage_path = Column(String(512), nullable=True)
    regulator = Column(String(100), nullable=False, index=True)
    jurisdiction = Column(String(100), nullable=True, index=True)
    effective_date = Column(Date, nullable=True)
    category = Column(String(100), nullable=True)
    version = Column(String(50), nullable=True)
    upload_timestamp = Column(DateTime(timezone=True), default=datetime.datetime.utcnow)
    parent_doc_id = Column(BigInteger, nullable=True)

class RegulatoryAlertRecord(Base):
    __tablename__ = 'regulatory_alerts'
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    document_id = Column(BigInteger, nullable=True)
    regulator = Column(String(100), nullable=False)
    document_title = Column(String(255), nullable=False)
    version = Column(String(50), nullable=False)
    effective_date = Column(Date, nullable=True)
    diff_summary = Column(Text, nullable=False)
    impact_level = Column(String(50), default='MEDIUM')
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)