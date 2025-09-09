from pydantic import BaseModel

class TopResult(BaseModel):
    name: str
    location: str | None

class TopResults(BaseModel):
    results: list[TopResult]

class Metadata(BaseModel):
    name: str
    address: str | None = None
    phone_number: str | None = None
    email: str | None = None
    website: str | None = None
    review_rate: str | None = None
    number_of_reviews: str | None = None
    description: str | None = None