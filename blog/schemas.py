from pydantic import BaseModel, ConfigDict
from datetime import datetime, date
from typing import Optional, Generic, TypeVar

T = TypeVar("T")


# =====================
# Pagination
# =====================
class Page(BaseModel, Generic[T]):
    total: int
    skip: int
    limit: int
    items: list[T]


# =====================
# Course
# =====================
class CourseBase(BaseModel):
    name: str
    school_id: int
    deviation: float
    source: Optional[str] = None


class CourseCreate(CourseBase):
    pass


class CourseOut(CourseBase):
    id: int
    like_count: int = 0
    dislike_count: int = 0
    model_config = ConfigDict(from_attributes=True)




# =====================
# School
# =====================
class SchoolBase(BaseModel):
    name: str
    yomi: Optional[str] = None
    prefecture: str
    prefecture_yomi: Optional[str] = None


class SchoolCreate(SchoolBase):
    pass


class SchoolOut(SchoolBase):
    id: int
    courses: list[CourseOut] = []
    like_count: int = 0
    dislike_count: int = 0
    model_config = ConfigDict(from_attributes=True)


# =====================
# Incident
# =====================
class IncidentBase(BaseModel):
    title: str
    description: Optional[str] = None
    course_name: Optional[str] = None


class IncidentCreate(IncidentBase):
    school_id: int
    occurred_year:  Optional[int] = None
    occurred_month: Optional[int] = None
    occurred_day:   Optional[int] = None


class IncidentOut(IncidentBase):
    id: int
    school_id: int
    school_name:          Optional[str] = None
    user_id:              Optional[int] = None
    user_name:            Optional[str] = None
    user_avatar_url:      Optional[str] = None
    user_avatar_position_x: int = 50
    user_avatar_position_y: int = 50
    created_at: datetime
    occurred_date:  Optional[date] = None
    occurred_year:  Optional[int] = None
    occurred_month: Optional[int] = None
    occurred_day:   Optional[int] = None
    like_count:    int = 0
    dislike_count: int = 0
    comment_count: int = 0
    model_config = ConfigDict(from_attributes=True)


# =====================
# User
# =====================
class UserBase(BaseModel):
    name: str
    email: str


class UserCreate(UserBase):
    password: str


class UserLogin(BaseModel):
    email: str
    password: str


class UserOut(UserBase):
    id: int
    role: str
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    avatar_position_x: int = 50
    avatar_position_y: int = 50
    model_config = ConfigDict(from_attributes=True)


class UserPublicOut(BaseModel):
    id: int
    name: str
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    avatar_position_x: int = 50
    avatar_position_y: int = 50
    follower_count: int = 0
    following_count: int = 0
    model_config = ConfigDict(from_attributes=True)


class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    bio: Optional[str] = None
    avatar_position_x: Optional[int] = None
    avatar_position_y: Optional[int] = None


# =====================
# SiteContent
# =====================
class SiteContentOut(BaseModel):
    key: str
    value: Optional[str] = ""
    model_config = ConfigDict(from_attributes=True)


class SiteContentUpdate(BaseModel):
    value: str


class ChangePassword(BaseModel):
    old_password: str
    new_password: str


class DeleteSelf(BaseModel):
    password: str


# =====================
# Auth
# =====================
class Token(BaseModel):
    access_token: str
    token_type: str


class RoleUpdate(BaseModel):
    role: str


# =====================
# Post
# =====================
class PostCreate(BaseModel):
    school_id: int
    content: str
    course_name: Optional[str] = None
    reply_to_id: Optional[int] = None
    incident_id: Optional[int] = None
    review_id:   Optional[int] = None


class PostOut(BaseModel):
    id: int
    user_id: int
    user_name: Optional[str] = None
    user_avatar_url: Optional[str] = None
    user_avatar_position_x: int = 50
    user_avatar_position_y: int = 50
    school_id: int
    school_name: Optional[str] = None
    incident_id: Optional[int] = None
    review_id:   Optional[int] = None
    content: str
    course_name: Optional[str] = None
    reply_to_id: Optional[int] = None
    created_at: datetime
    like_count: int = 0
    dislike_count: int = 0
    reply_count: int = 0
    model_config = ConfigDict(from_attributes=True)


# =====================
# Repost
# =====================
class RepostCreate(BaseModel):
    comment: Optional[str] = None


class RepostOut(BaseModel):
    id: int
    user_id: int
    user_name: Optional[str] = None
    user_avatar_url: Optional[str] = None
    user_avatar_position_x: int = 50
    user_avatar_position_y: int = 50
    post_id: int
    comment: Optional[str]
    created_at: datetime
    like_count: int = 0
    dislike_count: int = 0
    original_post: Optional['PostOut'] = None
    model_config = ConfigDict(from_attributes=True)


# =====================
# Post update
# =====================
class PostUpdate(BaseModel):
    content: Optional[str] = None
    course_name: Optional[str] = None


# =====================
# Repost update
# =====================
class RepostUpdate(BaseModel):
    comment: Optional[str] = None


# =====================
# Reaction
# =====================
class ReactionCreate(BaseModel):
    reaction: str  # "like" | "dislike"


class ReactionOut(BaseModel):
    id: Optional[int]
    user_id: int
    target_type: str
    target_id: int
    reaction: str
    model_config = ConfigDict(from_attributes=True)


# =====================
# Follow
# =====================
class FollowStatus(BaseModel):
    is_following: bool


# =====================
# Review
# =====================
class ReviewCreate(BaseModel):
    rating: int   # 1–5
    comment: Optional[str] = None
    course_name: Optional[str] = None


class ReviewOut(BaseModel):
    id: int
    user_id: int
    user_name: Optional[str] = None
    user_avatar_url: Optional[str] = None
    user_avatar_position_x: int = 50
    user_avatar_position_y: int = 50
    school_id: int
    school_name: Optional[str] = None
    rating: int
    comment: Optional[str] = None
    course_name: Optional[str] = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


# =====================
# Report
# =====================
class ReportCreate(BaseModel):
    target_type: str   # "post" | "repost" | "incident" | "review"
    target_id: int
    reason: Optional[str] = None


class ReportOut(BaseModel):
    id: int
    reporter_id: int
    reporter_name: Optional[str] = None
    target_type: str
    target_id: int
    reason: Optional[str] = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
