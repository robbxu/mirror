from typing import List
import uuid
from sqlalchemy import Column, Integer, Text, String, ForeignKey, types, text
from sqlalchemy.sql import func, false, true
from sqlalchemy.orm import mapped_column, Mapped, relationship
from project.database import Base
from project.utils.db_types import Embedding
from project.interact.models import Memory


class Category(Base):
    __tablename__ = "category"
    id = mapped_column(types.Uuid, primary_key=True, server_default=text("uuid_generate_v4()"))
    name = mapped_column(String(256), nullable=False)
    embedding : Mapped[List[float]] = mapped_column(Embedding(512), nullable=True)

    topics: Mapped[List["Topic"]] = relationship(cascade="save-update")


class Topic(Base):
    __tablename__ = "topic"
    id = mapped_column(types.Uuid, primary_key=True, server_default=text("uuid_generate_v4()"))
    
    # mixedbread word embeddings
    name = mapped_column(String(256), nullable=True) # unlimited length
    embedding : Mapped[List[float]] = mapped_column(Embedding(512), nullable=True)
    
    # pre-defined general categories
    category = relationship("Category", back_populates="topics")
    category_id : Mapped[uuid.UUID] = mapped_column(ForeignKey("category.id", name="category_id_topic_fkey", ondelete='SET NULL', onupdate='CASCADE'), nullable=True)
    # Maps to association table defined below
    belief_ids: Mapped[List["TopicBelief"]] = relationship(cascade="all, delete",back_populates="topic")


class Belief(Base):
    __tablename__ = "belief"
    id = mapped_column(types.Uuid, primary_key=True, server_default=text("uuid_generate_v4()"))
    
    # mixedbread word embeddings
    text = mapped_column(Text, nullable=True) # unlimited length
    embedding : Mapped[List[float]] = mapped_column(Embedding(512), nullable=True)
    # values are "value", "emotion", "opinion"
    type = mapped_column(String(50), nullable=True)
    
    memory_ids: Mapped[List["BeliefMemory"]] = relationship(cascade="all, delete")
    topic_ids: Mapped[List["TopicBelief"]] = relationship(cascade="all, delete", back_populates="belief")

    version_id = mapped_column(Integer, nullable=False, server_default="1")
    __mapper_args__ = {"version_id_col": version_id}


# Association Tables *******************************************************

class TopicBelief(Base):
    __tablename__ = "topic_belief"
    topic_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("topic.id", name="topic_id_belief_fkey", ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    topic: Mapped[Topic] = relationship(back_populates="belief_ids")
    belief_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("belief.id", name="topic_belief_id_fkey", ondelete='CASCADE', onupdate='CASCADE'), nullable=False, primary_key=True)
    belief: Mapped[Belief] = relationship(back_populates="topic_ids")
    version_id = mapped_column(Integer, nullable=False, server_default="1") # Optimistic locking

    __mapper_args__ = {"version_id_col": version_id}


class BeliefMemory(Base):
    __tablename__ = "belief_memory"
    belief_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("belief.id", name="belief_id_memory_fkey", ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    belief : Mapped[Belief] = relationship(back_populates="memory_ids")
    memory_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("memory.id", name="belief_memory_id_fkey", ondelete='CASCADE', onupdate='CASCADE'), nullable=False, primary_key=True)
    memory : Mapped[Memory] = relationship()
    version_id = mapped_column(Integer, nullable=False, server_default="1") # Optimistic locking

    __mapper_args__ = {"version_id_col": version_id}