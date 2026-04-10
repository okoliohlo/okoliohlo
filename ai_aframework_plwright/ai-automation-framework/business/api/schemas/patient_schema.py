"""
Patient Account Creation and Management Schemas
Based on Postman collection API specifications
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class ReserveUsernameRequest(BaseModel):
    """Schema for reserving a username"""
    username: str = Field(..., description="Username to reserve")


class ReserveUsernameResponse(BaseModel):
    """Schema for reserve username response"""
    clientKey: str = Field(..., description="Client key for MFA verification")


class MFAEmailRequest(BaseModel):
    """Schema for requesting MFA via email"""
    country: str = Field(..., description="Country code (e.g., GB, US)")
    email: str = Field(..., description="Email address for MFA")
    firstName: str = Field(..., description="User's first name")
    language: str = Field(..., description="Language code (e.g., en)")
    lastName: str = Field(..., description="User's last name")
    username: str = Field(..., description="Username")


class ConsentResult(BaseModel):
    """Schema for consent result"""
    key: str = Field(..., description="Consent key")
    accepted: bool = Field(..., description="Whether consent is accepted")


class PatientData(BaseModel):
    """Schema for patient data in user creation"""
    zip: Optional[str] = Field(None, description="Zip/postal code")
    therapyType: Optional[str] = Field(None, description="Therapy type")
    diabetesType: Optional[str] = Field(None, description="Diabetes type")
    gender: Optional[str] = Field(None, description="Gender")


class UserCreationData(BaseModel):
    """Schema for user creation data"""
    username: str = Field(..., description="Username")
    password: str = Field(..., description="Base64 encoded password")
    emailAddress: str = Field(..., description="Email address")
    guardianParent: bool = Field(False, description="Is guardian/parent")
    twoFaRequired: bool = Field(False, description="Two-factor auth required")
    firstName: str = Field(..., description="First name")
    lastName: str = Field(..., description="Last name")
    phoneNumber: str = Field(..., description="Phone number")
    consentResults: List[ConsentResult] = Field(..., description="Consent results")
    country: str = Field(..., description="Country code")
    language: str = Field(..., description="Language code")


class CreateUserRequest(BaseModel):
    """Schema for creating a new patient user"""
    mfaCode: str = Field(..., description="MFA verification code")
    captchaCode: str = Field(..., description="Recaptcha code")
    data: UserCreationData = Field(..., description="User data")
    patient: PatientData = Field(..., description="Patient-specific data")


class RecaptchaKeyResponse(BaseModel):
    """Schema for recaptcha key response"""
    value: str = Field(..., description="Recaptcha key value")


class LoginRequest(BaseModel):
    """Schema for login request"""
    username: str = Field(..., description="Username")
    password: str = Field(..., description="Password (not encoded for login)")
    locale: str = Field(default="en", description="Locale")
    action: str = Field(default="default", description="Action type")
    state: str = Field(..., description="OAuth state parameter")


class AuthTokenResponse(BaseModel):
    """Schema for authentication token response"""
    access_token: str = Field(..., description="Access token")
    token_type: str = Field(default="Bearer", description="Token type")
    expires_in: Optional[int] = Field(None, description="Token expiration in seconds")


class PatientConsent(BaseModel):
    """Schema for patient consent"""
    key: str = Field(..., description="Consent key identifier")
    title: Optional[str] = Field(None, description="Consent title")
    description: Optional[str] = Field(None, description="Consent description")
    required: Optional[bool] = Field(None, description="Whether consent is required")


class PatientConsentsResponse(BaseModel):
    """Schema for patient consents response"""
    consents: List[PatientConsent] = Field(default_factory=list, description="List of consents")


# Default consent configurations by country
DEFAULT_CONSENTS = {
    "GB": [
        {"key": "TOU_EMEA_1", "accepted": True},
        {"key": "DR_EMEA_1", "accepted": False},
        {"key": "PS_EMEA_1", "accepted": True}
    ],
    "US": [
        {"key": "TOU_US", "accepted": True},
        {"key": "PS_US", "accepted": True},
        {"key": "DR_US", "accepted": True}
    ],
    "CA": [
        {"key": "TOU_CANADA", "accepted": True},
        {"key": "PS_CANADA", "accepted": True},
        {"key": "DR_CANADA", "accepted": True},
        {"key": "AGGREGATE_CANADA", "accepted": True},
        {"key": "SMS_TEXT_CANADA", "accepted": True},
        {"key": "PATIENT_SMS_CP_CANADA", "accepted": False}
    ]
}
