from typing import List
import uuid
from sqlalchemy import Column, Integer, Float, Text, Boolean, ForeignKey, DateTime, types, text
from sqlalchemy.sql import func, false, true
from sqlalchemy.orm import mapped_column, Mapped, relationship
from project.database import Base
from project.utils.db_types import Embedding


class Interaction(Base):
    __tablename__ = "interaction"
    id = mapped_column(types.Uuid, primary_key=True, server_default=text("uuid_generate_v4()"))
    
    # Order is Empathy/Selfishness, Fear/Greed, Rational/Intuitive, Principled/Flexible
    personality : Mapped[List[float]] = mapped_column(Embedding(4), nullable=True)
    personality_confidence : Mapped[List[float]] = mapped_column(Embedding(4), nullable=True)
    # Order is Anger, Anticipation, Joy, Trust, Fear, Surprise, Sadness, Disgust
    mood_baseline: Mapped[List[float]] = mapped_column(Embedding(8), nullable=True)
    # Order is Vocab Level, Sentence Complexity, Formality, Verboseness, Analytical
    comm_style: Mapped[List[float]] = mapped_column(Embedding(5), nullable=True)
    # Order is Assertiveness, Agreeableness, Humor Rate, Topic Switching, Question Asking, Elaboration
    behavior: Mapped[List[float]] = mapped_column(Embedding(6), nullable=True)

    memories : Mapped[List["Memory"]] = relationship(cascade="save-update")
    exchanges : Mapped[List["Exchange"]] = relationship(cascade="save-update")

    created_time = Column(DateTime(timezone=True), server_default=func.now())
    version_id = mapped_column(Integer, nullable=False, server_default="1")
    __mapper_args__ = {"version_id_col": version_id}
    

class Memory(Base):
    __tablename__ = "memory"
    id = mapped_column(types.Uuid, primary_key=True, server_default=text("uuid_generate_v4()"))

    # voyage AI Embeddings
    embedding : Mapped[List[float]] = mapped_column(Embedding(512), nullable=True)
    impact = mapped_column(Float, nullable=True)

    # Check that postgres stores this in toasted format under the hood when long
    text = mapped_column(Text, nullable=True) # unlimited length, JSON format to support multi-turn convos
    summary = mapped_column(Text, nullable=True) # unlimited length

    interaction_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("interaction.id", name="interaction_id_memory_fkey", ondelete='SET NULL', onupdate='CASCADE'), nullable=True)
    interaction : Mapped[Interaction] = relationship(back_populates="memories")

    updated_time = Column(DateTime(timezone=True), server_default=func.now())
    created_time = Column(DateTime(timezone=True), server_default=func.now())
    version_id = mapped_column(Integer, nullable=False, server_default="1")
    __mapper_args__ = {"version_id_col": version_id}


class Exchange(Base):
    __tablename__ = "exchange"
    id = mapped_column(types.Uuid, primary_key=True, server_default=text("uuid_generate_v4()"))
     
    # Check that postgres stores this in toasted format under the hood when long
    text = mapped_column(Text, nullable=True) # unlimited length, JSON format to support multi-turn convos

    interaction_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("interaction.id", name="interaction_id_exchange_fkey", ondelete='SET NULL', onupdate='CASCADE'), nullable=True)
    interaction : Mapped[Interaction] = relationship(back_populates="exchanges")

    created_time = Column(DateTime(timezone=True), server_default=func.now())
    version_id = mapped_column(Integer, nullable=False, server_default="1")
    __mapper_args__ = {"version_id_col": version_id}
