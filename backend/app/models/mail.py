"""
Mail/messaging system models based on MAIL and MAILSTAT structures
"""

from sqlalchemy import Column, Integer, String, BigInteger, DateTime, Text, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .base import Base


class Mail(Base):
    """Mail message model based on MAIL structure"""
    __tablename__ = "mail"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Message identification (from MAIL)
    sender_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    recipient_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    userid = Column(String(25), nullable=False)  # MAIL.userid
    class_type = Column(Integer, nullable=False)  # MAIL.class - message class
    type = Column(Integer, default=0)             # MAIL.type
    stamp = Column(Integer, default=0)            # MAIL.stamp
    
    # Message content (from MAIL)
    dtime = Column(String(20), default="")        # MAIL.dtime
    topic = Column(String(30), default="")        # MAIL.topic
    string1 = Column(String(80), default="")      # MAIL.string1
    name1 = Column(String(25), default="")        # MAIL.name1
    name2 = Column(String(25), default="")        # MAIL.name2
    
    # Message data (from MAIL)
    int1 = Column(Integer, default=0)             # MAIL.int1
    int2 = Column(Integer, default=0)             # MAIL.int2
    int3 = Column(Integer, default=0)             # MAIL.int3
    long1 = Column(BigInteger, default=0)         # MAIL.long1
    long2 = Column(BigInteger, default=0)         # MAIL.long2
    long3 = Column(BigInteger, default=0)         # MAIL.long3
    
    # Message status
    is_read = Column(Boolean, default=False)
    is_deleted = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    sender = relationship("User", foreign_keys=[sender_id], back_populates="mail_sent")
    recipient = relationship("User", foreign_keys=[recipient_id], back_populates="mail_received")
    
    def __repr__(self):
        return f"<Mail(topic='{self.topic}', sender_id={self.sender_id}, recipient_id={self.recipient_id})>"


class MailStatus(Base):
    """Mail status model based on MAILSTAT structure"""
    __tablename__ = "mail_status"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Status identification (from MAILSTAT)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    userid = Column(String(25), nullable=False)  # MAILSTAT.userid
    class_type = Column(Integer, nullable=False)  # MAILSTAT.class
    type = Column(Integer, default=0)             # MAILSTAT.type
    stamp = Column(Integer, default=0)            # MAILSTAT.stamp
    
    # Status content (from MAILSTAT)
    dtime = Column(String(20), default="")        # MAILSTAT.dtime
    topic = Column(String(30), default="")        # MAILSTAT.topic
    name1 = Column(String(25), default="")        # MAILSTAT.name1
    int1 = Column(Integer, default=0)             # MAILSTAT.int1
    int2 = Column(Integer, default=0)             # MAILSTAT.int2
    
    # Financial data (from MAILSTAT)
    cash = Column(BigInteger, default=0)          # MAILSTAT.cash - cash on hand
    debt = Column(BigInteger, default=0)          # MAILSTAT.debt - amount owed
    tax = Column(BigInteger, default=0)           # MAILSTAT.tax - tax collected
    
    # Item quantities (from MAILSTAT.itemqty[NUMITEMS])
    # We'll store this as JSON or create a separate table for item quantities
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User")
    
    def __repr__(self):
        return f"<MailStatus(userid='{self.userid}', class_type={self.class_type}, cash={self.cash})>"


# Mail class constants from original code
class MailClass:
    DISTRESS = 1      # MAIL_CLASS_DISTRESS
    MAXOUT = 2        # MAIL_CLASS_MAXOUT  
    PRODRPT = 3       # MAIL_CLASS_PRODRPT
    GAMESTATS = 4     # MAIL_CLASS_GAMESTATS
    PLSTATS = 5       # MAIL_CLASS_PLSTATS
