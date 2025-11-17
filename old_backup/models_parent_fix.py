# Add this to models_parent.py

class AllowedHours(BaseModel):
    start: int = Field(default=8, ge=0, le=23)
    end: int = Field(default=20, ge=1, le=24)

class StudentCreateWithParent(BaseModel):
    parent_id: str
    name: str
    age: int = Field(..., ge=5, le=18)
    grade: int = Field(..., ge=1, le=12)
    reading_level: Optional[int] = None
    special_needs: Optional[List[str]] = Field(default_factory=list)
    interests: Optional[List[str]] = Field(default_factory=list)
    allowed_hours: Optional[AllowedHours] = Field(default_factory=lambda: AllowedHours())
    daily_time_limit: Optional[int] = Field(default=60, ge=0, le=480)
