from typing import List, Optional
from pydantic import BaseModel, Field

class HighlightCoordinate(BaseModel):
    page_number: int
    start_offset: int = Field(..., description="Exact character start index relative to the text node")
    end_offset: int = Field(..., description="Exact character end index")
    color_code: str = Field(default="yellow", description="Category color, e.g., Fiqh(blue), Aqidah(green)")

class Highlight(BaseModel):
    highlight_id: str
    document_id: str
    coordinates: HighlightCoordinate
    extracted_text: str = Field(..., description="The exact highlighted string")

class MentionReference(BaseModel):
    shorthand: str = Field(..., description="The raw shorthand typed, e.g., @2:255")
    reference_type: str = Field(..., description="e.g., quran, hadith, scholar_quote")
    arabic_text: str
    translation: Optional[str] = None
    citation: str = Field(..., description="e.g., Surah Al-Baqarah, Ayah 255")

class Note(BaseModel):
    note_id: str
    user_id: str
    content: str = Field(..., description="The user's personal notes")
    anchored_highlight_id: Optional[str] = Field(None, description="Links this note to a specific highlight")
    references: List[MentionReference] = Field(default_factory=list, description="Resolved @mentions inside the note")
    tags: List[str] = Field(default_factory=list)
