"""SQLAlchemy ORM Data Models for Emitens, Documents, and Chunks."""

from __future__ import annotations

from datetime import datetime
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship
from backend.database import Base


class EmitenModel(Base):
    __tablename__ = "emitens"

    code = Column(String(10), primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    sector = Column(String(100), default="Umum")
    subsector = Column(String(100), default="Umum")
    market_cap = Column(String(100), default="-")
    technology_stack = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow)

    documents = relationship("DocumentModel", back_populates="emiten", cascade="all, delete-orphan")
    chunks = relationship("ChunkModel", back_populates="emiten", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "code": self.code,
            "name": self.name,
            "sector": self.sector,
            "subsector": self.subsector,
            "market_cap": self.market_cap,
            "technology_stack": self.technology_stack,
        }


class DocumentModel(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, autoincrement=True)
    emiten_code = Column(String(10), ForeignKey("emitens.code", ondelete="CASCADE"), index=True, nullable=False)
    doc_name = Column(String(255), nullable=False, index=True)
    year = Column(Integer, index=True, nullable=False)
    file_path = Column(String(500), nullable=True)
    total_pages = Column(Integer, default=0)
    file_size = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    emiten = relationship("EmitenModel", back_populates="documents")

    __table_args__ = (
        Index("ix_doc_emiten_year", "emiten_code", "year"),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "emiten_code": self.emiten_code,
            "doc_name": self.doc_name,
            "year": self.year,
            "file_path": self.file_path,
            "total_pages": self.total_pages,
            "file_size": self.file_size,
        }


class ChunkModel(Base):
    __tablename__ = "document_chunks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    chunk_id = Column(String(100), index=True, nullable=False)
    emiten_code = Column(String(10), ForeignKey("emitens.code", ondelete="CASCADE"), index=True, nullable=False)
    doc_name = Column(String(255), nullable=False)
    year = Column(Integer, index=True, nullable=False)
    physical_page = Column(Integer, default=1)
    printed_page = Column(Integer, default=1)
    page_display = Column(String(100), default="")
    page_number = Column(Integer, default=1)
    chapter_title = Column(String(255), default="Laporan Tahunan")
    raw_paragraph = Column(Text, nullable=False)
    is_noise = Column(Boolean, default=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    emiten = relationship("EmitenModel", back_populates="chunks")

    __table_args__ = (
        Index("ix_chunk_emiten_year", "emiten_code", "year"),
        Index("ix_chunk_emiten_noise", "emiten_code", "is_noise"),
        Index("ix_chunk_emiten_page", "emiten_code", "printed_page"),
    )

    def to_dict(self):
        return {
            "chunk_id": self.chunk_id,
            "emiten_code": self.emiten_code,
            "doc_name": self.doc_name,
            "year": self.year,
            "physical_page": self.physical_page,
            "printed_page": self.printed_page,
            "page_display": self.page_display,
            "page_number": self.page_number,
            "chapter_title": self.chapter_title,
            "raw_paragraph": self.raw_paragraph,
            "is_noise": self.is_noise,
        }
