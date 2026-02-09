from pydantic import BaseModel, Field
from typing import List, Optional

class PolicyInfo(BaseModel):
    policy_number: Optional[str] = None
    policyholder_name: Optional[str] = None # Requirement: Policyholder Name
    effective_dates: Optional[str] = None # Requirement: Effective Dates
    carrier: Optional[str] = None
    line_of_business: Optional[str] = None

class InsuredInfo(BaseModel):
    name: Optional[str] = None
    address: Optional[str] = None
    dob: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None

class LossInfo(BaseModel):
    date: Optional[str] = None # Requirement: Date
    time: Optional[str] = None # Requirement: Time
    location: Optional[str] = None # Requirement: Location
    police_contacted: Optional[str] = None
    report_number: Optional[str] = None
    description: Optional[str] = None # Requirement: Description

class PartyInfo(BaseModel):
    claimant: Optional[str] = None # Requirement: Claimant
    third_parties: Optional[str] = None # Requirement: Third Parties
    contact_details: Optional[str] = None # Requirement: Contact Details

class AssetInfo(BaseModel):
    asset_type: Optional[str] = None # Requirement: Asset Type
    asset_id: Optional[str] = None # Requirement: Asset ID (VIN)
    estimated_damage: Optional[float] = None # Requirement: Estimated Damage

class ExtractedFields(BaseModel):
    policy: PolicyInfo = Field(default_factory=PolicyInfo)
    insured: InsuredInfo = Field(default_factory=InsuredInfo)
    loss: LossInfo = Field(default_factory=LossInfo)
    parties: PartyInfo = Field(default_factory=PartyInfo)
    asset: AssetInfo = Field(default_factory=AssetInfo)
    claim_type: Optional[str] = None # Requirement: Claim Type
    attachments: Optional[str] = None # Requirement: Attachments
    initial_estimate: Optional[float] = None # Requirement: Initial Estimate

class ClaimResponse(BaseModel):
    extractedFields: ExtractedFields
    missingFields: List[str]
    inconsistentFields: List[str]
    recommendedRoute: str
    reasoning: str
