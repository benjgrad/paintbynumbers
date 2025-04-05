from sqlalchemy import Column, String, DateTime, Enum, Integer, CheckConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from datetime import datetime
import enum

Base = declarative_base()

class ProcessingStatus(enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class Upload(Base):
    __tablename__ = "uploads"

    id = Column(String, primary_key=True)
    filename = Column(String, nullable=False)
    original_name = Column(String, nullable=False)
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    status = Column(Enum(ProcessingStatus), default=ProcessingStatus.PENDING)
    processed_filename = Column(String, nullable=True)
    filled_filename = Column(String, nullable=True)
    error_message = Column(String, nullable=True)
    color_count = Column(Integer, nullable=False, default=20)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Add constraint to ensure color_count is between 2 and 30
    __table_args__ = (
        CheckConstraint('color_count >= 2 AND color_count <= 30', name='check_color_count'),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "filename": self.filename,
            "originalName": self.original_name,
            "uploadedAt": self.uploaded_at.isoformat(),
            "status": self.status.value,
            "processedFilename": self.processed_filename,
            "filledFilename": self.filled_filename,
            "errorMessage": self.error_message,
            "colorCount": self.color_count,
            "createdAt": self.created_at.isoformat() if self.created_at else None,
            "updatedAt": self.updated_at.isoformat() if self.updated_at else None
        } 