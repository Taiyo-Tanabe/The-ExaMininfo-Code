from sqlalchemy import Column, Integer, Float, String, Text, ForeignKey, DateTime, Date, UniqueConstraint, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base



# =====================
# School
# =====================
class School(Base):
    __tablename__ = "schools"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    yomi = Column(String, nullable=True, index=True)
    prefecture = Column(String, index=True)
    prefecture_yomi = Column(String, nullable=True, index=True)

    courses = relationship(
        "Course",
        back_populates="school",
        cascade="all, delete"
    )

    incidents = relationship(
        "Incident",
        back_populates="school",
        cascade="all, delete"
    )

    posts = relationship(
        "Post",
        back_populates="school",
        cascade="all, delete"
    )

    reviews = relationship(
        "Review",
        back_populates="school",
        cascade="all, delete"
    )


# =====================
# Course（偏差値の本体）
# =====================
class Course(Base):
    __tablename__ = "courses"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    deviation = Column(Float, index=True, nullable=False)
    source = Column(String, nullable=True, index=True)
    school_id = Column(Integer, ForeignKey("schools.id"))

    school = relationship("School", back_populates="courses")

    __table_args__ = (
        UniqueConstraint("school_id", "name", "source", name="uq_course_school_name_source"),
    )


# =====================
# Incident
# =====================
class Incident(Base):
    __tablename__ = "incidents"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    description = Column(Text)
    course_name = Column(String, nullable=True)

    school_id = Column(Integer, ForeignKey("schools.id"))
    user_id   = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    occurred_date  = Column(Date, nullable=True)
    occurred_year  = Column(Integer, nullable=True)
    occurred_month = Column(Integer, nullable=True)
    occurred_day   = Column(Integer, nullable=True)

    school = relationship("School",   back_populates="incidents")
    user   = relationship("User",     back_populates="incidents")
    posts  = relationship("Post",     back_populates="incident")


# =====================
# User
# =====================
class SiteContent(Base):
    __tablename__ = "site_contents"

    key   = Column(String, primary_key=True)   # e.g. "home_description", "about", "legal"
    value = Column(Text, nullable=True, default="")


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password = Column(String, nullable=False)
    role = Column(String, default="user")
    is_approved = Column(Boolean, nullable=False, default=False, server_default='false')
    bio = Column(Text, nullable=True)
    avatar_url = Column(String, nullable=True)
    avatar_position_x = Column(Integer, nullable=False, server_default='50')
    avatar_position_y = Column(Integer, nullable=False, server_default='50')

    posts                  = relationship("Post",              back_populates="user",    cascade="all, delete")
    reposts                = relationship("Repost",            back_populates="user",    cascade="all, delete")
    reactions              = relationship("Reaction",          back_populates="user",    cascade="all, delete")
    incidents              = relationship("Incident",          back_populates="user")
    reviews                = relationship("Review",            back_populates="user",    cascade="all, delete")
    following              = relationship("Follow", foreign_keys="Follow.follower_id",  back_populates="follower",       cascade="all, delete")
    followers              = relationship("Follow", foreign_keys="Follow.following_id", back_populates="following_user", cascade="all, delete")
    reports                = relationship("Report",            back_populates="reporter", cascade="all, delete")
    created_organizations  = relationship("Organization",      back_populates="creator",  cascade="all, delete")
    created_events         = relationship("Event",             back_populates="creator",  cascade="all, delete")
    event_attendances      = relationship("EventAttendance",   back_populates="user",    cascade="all, delete")
    event_view_requests    = relationship("EventViewRequest",  back_populates="user",    cascade="all, delete")
    org_memberships        = relationship("OrgMember",         back_populates="user",    cascade="all, delete")


# =====================
# Post
# =====================
class Post(Base):
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True, index=True)
    user_id     = Column(Integer, ForeignKey("users.id"),                        nullable=False)
    school_id   = Column(Integer, ForeignKey("schools.id"),                      nullable=False)
    incident_id = Column(Integer, ForeignKey("incidents.id", ondelete="SET NULL"), nullable=True)
    review_id   = Column(Integer, ForeignKey("reviews.id",   ondelete="SET NULL"), nullable=True)
    content     = Column(Text, nullable=False)
    course_name = Column(String, nullable=True)
    reply_to_id = Column(Integer, ForeignKey("posts.id", ondelete="SET NULL"),   nullable=True)
    created_at  = Column(DateTime(timezone=True), server_default=func.now())

    user     = relationship("User",     back_populates="posts")
    school   = relationship("School",   back_populates="posts")
    incident = relationship("Incident", back_populates="posts")
    review   = relationship("Review",   back_populates="posts")
    reposts  = relationship("Repost", back_populates="original_post", cascade="all, delete")
    replies  = relationship("Post", foreign_keys=[reply_to_id], backref="reply_to", remote_side="Post.id")


# =====================
# Repost
# =====================
class Repost(Base):
    __tablename__ = "reposts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    post_id = Column(Integer, ForeignKey("posts.id"), nullable=False)
    comment = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="reposts")
    original_post = relationship("Post", back_populates="reposts")


# =====================
# Reaction
# =====================
class Reaction(Base):
    __tablename__ = "reactions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    target_type = Column(String, nullable=False)   # "post" | "repost"
    target_id = Column(Integer, nullable=False)
    reaction = Column(String, nullable=False)       # "like" | "dislike"
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        UniqueConstraint("user_id", "target_type", "target_id", name="uq_user_reaction"),
    )

    user = relationship("User", back_populates="reactions")


# =====================
# Follow
# =====================
class Follow(Base):
    __tablename__ = "follows"

    id = Column(Integer, primary_key=True, index=True)
    follower_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    following_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        UniqueConstraint("follower_id", "following_id", name="uq_follow"),
    )

    follower = relationship("User", foreign_keys=[follower_id], back_populates="following")
    following_user = relationship("User", foreign_keys=[following_id], back_populates="followers")


# =====================
# Review
# =====================
class Review(Base):
    __tablename__ = "reviews"

    id        = Column(Integer, primary_key=True, index=True)
    user_id   = Column(Integer, ForeignKey("users.id",   ondelete="CASCADE"), nullable=False)
    school_id = Column(Integer, ForeignKey("schools.id", ondelete="CASCADE"), nullable=False)
    rating      = Column(Integer, nullable=False)   # 1–5
    comment     = Column(Text, nullable=True)
    course_name = Column(String, nullable=True)
    created_at  = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        UniqueConstraint("user_id", "school_id", name="uq_user_school_review"),
    )

    user   = relationship("User",   back_populates="reviews")
    school = relationship("School", back_populates="reviews")
    posts  = relationship("Post",   back_populates="review")


# =====================
# Report
# =====================
class Report(Base):
    __tablename__ = "reports"

    id          = Column(Integer, primary_key=True, index=True)
    reporter_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    target_type = Column(String, nullable=False)   # "post" | "repost" | "incident" | "review"
    target_id   = Column(Integer, nullable=False)
    reason      = Column(Text, nullable=True)
    created_at  = Column(DateTime(timezone=True), server_default=func.now())

    reporter = relationship("User", back_populates="reports")


# =====================
# BlockedEmail
# =====================
class BlockedEmail(Base):
    __tablename__ = "blocked_emails"

    id         = Column(Integer, primary_key=True, index=True)
    email      = Column(String, unique=True, nullable=False, index=True)
    blocked_at = Column(DateTime(timezone=True), server_default=func.now())


# =====================
# Organization（団体）
# =====================
class Organization(Base):
    __tablename__ = "organizations"

    id          = Column(Integer, primary_key=True, index=True)
    name        = Column(String, unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    created_by  = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at  = Column(DateTime(timezone=True), server_default=func.now())

    school_id             = Column(Integer, ForeignKey("schools.id", ondelete="SET NULL"), nullable=True)
    department            = Column(String, nullable=True)
    personal_info_prompt  = Column(Text, nullable=True)
    icon_url              = Column(Text, nullable=True)
    icon_position_x       = Column(Integer, default=50, server_default='50')
    icon_position_y       = Column(Integer, default=50, server_default='50')

    creator = relationship("User",   back_populates="created_organizations")
    school  = relationship("School")
    events  = relationship("Event",     back_populates="organization", cascade="all, delete")
    members = relationship("OrgMember", back_populates="organization", cascade="all, delete")


# =====================
# Event
# =====================
class Event(Base):
    __tablename__ = "events"

    id                      = Column(Integer, primary_key=True, index=True)
    title                   = Column(String, nullable=False, index=True)
    description             = Column(Text, nullable=True)
    location                = Column(String, nullable=True)
    start_at                = Column(DateTime(timezone=True), nullable=True)
    end_at                  = Column(DateTime(timezone=True), nullable=True)
    max_participants        = Column(Integer, nullable=True)
    requires_view_approval  = Column(Boolean, nullable=False, default=False, server_default='false')
    requires_join_approval  = Column(Boolean, nullable=False, default=False, server_default='false')
    allow_member_view       = Column(Boolean, nullable=False, default=True,  server_default='true')
    allow_member_join       = Column(Boolean, nullable=False, default=True,  server_default='true')
    org_id                  = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=True)
    created_by              = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at              = Column(DateTime(timezone=True), server_default=func.now())

    organization  = relationship("Organization",    back_populates="events")
    creator       = relationship("User",            back_populates="created_events")
    attendances   = relationship("EventAttendance", back_populates="event", cascade="all, delete")
    view_requests = relationship("EventViewRequest", back_populates="event", cascade="all, delete")


# =====================
# EventAttendance
# =====================
class EventAttendance(Base):
    __tablename__ = "event_attendances"

    id         = Column(Integer, primary_key=True, index=True)
    event_id   = Column(Integer, ForeignKey("events.id",  ondelete="CASCADE"), nullable=False)
    user_id    = Column(Integer, ForeignKey("users.id",   ondelete="CASCADE"), nullable=False)
    # "attending" | "not_attending" | "pending"（承認待ち）
    status     = Column(String, nullable=False, default="attending")
    note       = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        UniqueConstraint("event_id", "user_id", name="uq_event_attendance"),
    )

    event = relationship("Event", back_populates="attendances")
    user  = relationship("User",  back_populates="event_attendances")


# =====================
# EventViewRequest（閲覧申請）
# =====================
class EventViewRequest(Base):
    __tablename__ = "event_view_requests"

    id         = Column(Integer, primary_key=True, index=True)
    event_id   = Column(Integer, ForeignKey("events.id",  ondelete="CASCADE"), nullable=False)
    user_id    = Column(Integer, ForeignKey("users.id",   ondelete="CASCADE"), nullable=False)
    # "pending" | "approved" | "rejected"
    status     = Column(String, nullable=False, default="pending")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        UniqueConstraint("event_id", "user_id", name="uq_view_request"),
    )

    event = relationship("Event", back_populates="view_requests")
    user  = relationship("User",  back_populates="event_view_requests")


# =====================
# OrgMember（団体メンバー）
# =====================
class OrgMember(Base):
    __tablename__ = "org_members"

    id        = Column(Integer, primary_key=True, index=True)
    org_id    = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    user_id   = Column(Integer, ForeignKey("users.id",         ondelete="CASCADE"), nullable=False)
    role          = Column(String, nullable=False, default="member",  server_default="member")   # "member" | "admin"
    status        = Column(String, nullable=False, default="pending", server_default="approved")  # "pending" | "approved"
    personal_info = Column(Text, nullable=True)
    joined_at     = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        UniqueConstraint("org_id", "user_id", name="uq_org_member"),
    )

    organization = relationship("Organization", back_populates="members")
    user         = relationship("User",         back_populates="org_memberships")