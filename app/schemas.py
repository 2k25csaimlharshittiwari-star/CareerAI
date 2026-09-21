from typing import Optional
from pydantic import BaseModel, Field, EmailStr, field_validator, model_validator

class RegisterIn(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)

class LoginIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)

class ProfileUpdate(BaseModel):
    college: Optional[str] = Field(default=None, max_length=160); degree: Optional[str] = Field(default=None, max_length=120); branch: Optional[str] = Field(default=None, max_length=120)
    year: Optional[int] = Field(default=None, ge=1, le=8); semester: Optional[int] = Field(default=None, ge=1, le=12); location: Optional[str] = Field(default=None, max_length=120)
    cgpa: Optional[float] = Field(default=None, ge=0, le=10); tenth: Optional[float] = Field(default=None, ge=0, le=100); twelfth: Optional[float] = Field(default=None, ge=0, le=100)
    backlogs: Optional[int] = Field(default=None, ge=0, le=100); target_role: Optional[str] = Field(default=None, max_length=120); career_goal: Optional[str] = Field(default=None, max_length=1000)

    @model_validator(mode='after')
    def validate_semester_for_degree(self):
        if self.semester is None or not self.degree:
            return self
        d=self.degree.lower().replace('.', ' ').replace('-', ' ')
        if any(x in d for x in ('phd','ph d','doctorate','doctoral')):
            max_sem=12; label='Doctorate (PhD)'
        elif any(x in d for x in ('master','masters','m tech','mtech','mca','msc','m sc','ma','m com','mcom','mba')):
            max_sem=4; label='Master’s degree'
        elif any(x in d for x in ('bachelor','b tech','btech','bca','bsc','b sc','ba','b com','bcom','be','b e','bba')):
            max_sem=8; label='Bachelor’s degree'
        elif any(x in d for x in ('diploma','certificate')):
            max_sem=4; label='Diploma / Certificate'
        else:
            max_sem=12; label='recognized program'
        if self.semester > max_sem:
            raise ValueError(f'{label} semester limit is {max_sem}.')
        return self

class SkillIn(BaseModel):
    name: str = Field(min_length=1, max_length=100); level: Optional[str] = Field(default=None, max_length=30); score: Optional[float] = Field(default=None, ge=0, le=10)

class ProjectIn(BaseModel):
    name: str = Field(min_length=1, max_length=160); description: Optional[str] = Field(default=None, max_length=2000); technologies: Optional[str] = Field(default=None, max_length=500); github_url: Optional[str] = None; live_url: Optional[str] = None

class CertIn(BaseModel):
    name: str = Field(min_length=1, max_length=180); platform: Optional[str] = Field(default=None, max_length=100); issuer: Optional[str] = Field(default=None, max_length=120); url: Optional[str] = None

class AcademicIn(BaseModel):
    term: str = Field(min_length=1, max_length=80); cgpa: Optional[float] = Field(default=None, ge=0, le=10); attendance: Optional[float] = Field(default=None, ge=0, le=100); backlogs: int = Field(default=0, ge=0, le=100)

class CodingIn(BaseModel):
    platform: Optional[str] = Field(default=None, max_length=80); problems_solved: int = Field(default=0, ge=0, le=100000); easy: int = Field(default=0, ge=0, le=100000); medium: int = Field(default=0, ge=0, le=100000); hard: int = Field(default=0, ge=0, le=100000); rating: Optional[float] = Field(default=None, ge=0, le=5000)

class PerformanceIn(BaseModel):
    category: str = Field(min_length=1, max_length=120); score: float = Field(ge=0, le=10); note: Optional[str] = Field(default=None, max_length=1000)

class TaskUpdate(BaseModel):
    completed: bool

class MentorIn(BaseModel):
    question: str = Field(min_length=2, max_length=1000)
