from typing import List, Optional
from pydantic import BaseModel, Field

class QuranAyah(BaseModel):
    surah_number: int
    ayah_number: int
    text_hafs: str = Field(..., description="Arabic text in Hafs reading")
    text_translation_sahih: Optional[str] = None
    roots: List[str] = Field(default_factory=list, description="Extracted morphological roots")

class Narrator(BaseModel):
    narrator_id: str = Field(..., description="Unique ID for the narrator")
    primary_name: str
    aliases: List[str] = Field(default_factory=list)
    tabaqat: Optional[int] = Field(None, description="Generation classification")
    reliability_grade: str = Field(..., description="E.g., Thiqah, Sadooq, Da'if")

class IsnadChain(BaseModel):
    chain_id: str
    narrators: List[str] = Field(..., description="Ordered list of narrator_ids from source to collector")
    validity_score: Optional[float] = None

class HadithMatn(BaseModel):
    hadith_id: str
    collection: str = Field(..., description="E.g., Sahih Bukhari")
    chapter: str
    text_arabic: str
    text_english: Optional[str] = None
    isnad_chain_ids: List[str] = Field(default_factory=list, description="Transmission chains linking to this text")
