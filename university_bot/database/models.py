from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey, String, Integer, Time, Date, Boolean
from typing import List, Optional

class Base(DeclarativeBase):
    pass

class Group(Base):
    __tablename__ = "groups"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50), unique=True)
    faculty: Mapped[str] = mapped_column(String(100))
    course: Mapped[int] = mapped_column(Integer)
    
    users: Mapped[List["User"]] = relationship(back_populates="group")
    schedules: Mapped[List["Schedule"]] = relationship(back_populates="group")
    exams: Mapped[List["Exam"]] = relationship(back_populates="group")

class Subject(Base):
    __tablename__ = "subjects"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    teacher_name: Mapped[str] = mapped_column(String(100))
    subject_type: Mapped[str] = mapped_column(String(20)) # lecture/practice/lab/seminar
    
    schedules: Mapped[List["Schedule"]] = relationship(back_populates="subject")
    exams: Mapped[List["Exam"]] = relationship(back_populates="subject")

class Schedule(Base):
    __tablename__ = "schedule"
    id: Mapped[int] = mapped_column(primary_key=True)
    group_id: Mapped[int] = mapped_column(ForeignKey("groups.id"))
    subject_id: Mapped[int] = mapped_column(ForeignKey("subjects.id"))
    weekday: Mapped[int] = mapped_column(Integer) # 0-5 (Mon-Sat)
    start_time: Mapped[str] = mapped_column(String(10)) # "HH:MM"
    end_time: Mapped[str] = mapped_column(String(10))
    room: Mapped[str] = mapped_column(String(20))
    week_type: Mapped[str] = mapped_column(String(10), default="all") # all/odd/even
    
    group: Mapped["Group"] = relationship(back_populates="schedules")
    subject: Mapped["Subject"] = relationship(back_populates="schedules")

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    telegram_id: Mapped[int] = mapped_column(unique=True)
    username: Mapped[Optional[str]] = mapped_column(String(50))
    full_name: Mapped[str] = mapped_column(String(100))
    group_id: Mapped[Optional[int]] = mapped_column(ForeignKey("groups.id"))
    notify_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)
    
    group: Mapped["Group"] = relationship(back_populates="users")

class Exam(Base):
    __tablename__ = "exams"
    id: Mapped[int] = mapped_column(primary_key=True)
    group_id: Mapped[int] = mapped_column(ForeignKey("groups.id"))
    subject_id: Mapped[int] = mapped_column(ForeignKey("subjects.id"))
    exam_date: Mapped[Date] = mapped_column(Date)
    exam_time: Mapped[str] = mapped_column(String(10))
    room: Mapped[str] = mapped_column(String(20))
    exam_type: Mapped[str] = mapped_column(String(50))
    
    group: Mapped["Group"] = relationship(back_populates="exams")
    subject: Mapped["Subject"] = relationship(back_populates="exams")
