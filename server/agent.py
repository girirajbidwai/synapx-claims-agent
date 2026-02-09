import re
from .models import (
    ExtractedFields, ClaimResponse, PolicyInfo, 
    InsuredInfo, LossInfo, PartyInfo, AssetInfo
)

class ClaimsAgent:
    def __init__(self):
        # Mandatory fields as per Step 4 routing rules
        self.mandatory_fields = {
            "policy.policy_number": "Policy Number",
            "policy.policyholder_name": "Policyholder Name",
            "loss.date": "Incident Date",
            "loss.location": "Location",
            "loss.description": "Description",
            "parties.claimant": "Claimant",
            "asset.asset_id": "Asset ID (VIN)",
            "asset.estimated_damage": "Estimated Damage",
            "claim_type": "Claim Type"
        }

    def _extract_robust(self, text, keywords):
        """Extracts value regardless of colon presence and handles multi-line spaces."""
        for kw in keywords:
            # Try keyword with colon
            pattern = rf"(?i){kw}[:\s]+(.*?)(?=\n|[ ]{{4}}|$)"
            match = re.search(pattern, text)
            if match:
                val = match.group(1).strip()
                if val and "[MISSING]" not in val.upper():
                    return val
        return None

    def _clean_numeric(self, val):
        if val is None: return None
        cleaned = re.sub(r'[^\d.]', '', str(val))
        try:
            return float(cleaned)
        except ValueError:
            return None

    def process_claim(self, content: str) -> ClaimResponse:
        # 1. Extraction (Robust mapping to Step 3 requirements)
        policy = PolicyInfo(
            policy_number=self._extract_robust(content, ["POLICY NUMBER", "POLICY #"]),
            policyholder_name=self._extract_robust(content, ["NAME OF INSURED", "POLICYHOLDER"]),
            effective_dates=self._extract_robust(content, ["EFFECTIVE DATES", "PERIOD"]),
            carrier=self._extract_robust(content, ["CARRIER"]),
            line_of_business=self._extract_robust(content, ["LINE OF BUSINESS", "LOB"])
        )

        insured = InsuredInfo(
            name=policy.policyholder_name,
            address=self._extract_robust(content, ["INSURED'S MAILING ADDRESS", "ADDRESS"]),
            dob=self._extract_robust(content, ["DATE OF BIRTH", "DOB"]),
            phone=self._extract_robust(content, ["PRIMARY PHONE #", "PHONE"]),
            email=self._extract_robust(content, ["PRIMARY E-MAIL ADDRESS", "EMAIL"])
        )

        loss = LossInfo(
            date=self._extract_robust(content, ["DATE OF LOSS AND TIME", "DATE OF LOSS"]),
            time=self._extract_robust(content, ["TIME OF LOSS", "TIME"]),
            location=self._extract_robust(content, ["LOCATION OF LOSS", "LOCATION"]),
            police_contacted=self._extract_robust(content, ["POLICE OR FIRE DEPARTMENT CONTACTED"]),
            report_number=self._extract_robust(content, ["REPORT NUMBER"]),
            description=self._extract_robust(content, ["DESCRIPTION OF ACCIDENT", "ACCIDENT DESCRIPTION", "DESCRIPTION"])
        )

        # Basic parsing for time if merged in date field
        if loss.date and not loss.time:
            time_match = re.search(r"(\d{1,2}:\d{2}\s*(?:AM|PM)?)", loss.date, re.I)
            if time_match:
                loss.time = time_match.group(1)
                loss.date = loss.date.replace(loss.time, "").strip()

        parties = PartyInfo(
            claimant=self._extract_robust(content, ["CLAIMANT", "NAME OF INSURED"]),
            third_parties=self._extract_robust(content, ["THIRD PARTIES", "OTHER VEHICLE OWNER", "DRIVER OF OTHER"]),
            contact_details=self._extract_robust(content, ["CONTACT DETAILS", "PRIMARY PHONE #", "PRIMARY E-MAIL ADDRESS"])
        )

        asset = AssetInfo(
            asset_type=self._extract_robust(content, ["YEAR", "MAKE", "MODEL", "ASSET TYPE"]),
            asset_id=self._extract_robust(content, ["V.I.N.", "VIN", "ASSET ID"]),
            estimated_damage=self._clean_numeric(self._extract_robust(content, ["ESTIMATE AMOUNT", "ESTIMATED DAMAGE"]))
        )

        claim_type = self._extract_robust(content, ["CLAIM TYPE", "TYPE OF CLAIM"]) or "Collision"
        attachments = self._extract_robust(content, ["ATTACHMENTS"])
        initial_estimate = self._clean_numeric(self._extract_robust(content, ["INITIAL ESTIMATE", "ESTIMATE AMOUNT"]))

        fields = ExtractedFields(
            policy=policy,
            insured=insured,
            loss=loss,
            parties=parties,
            asset=asset,
            claim_type=claim_type,
            attachments=attachments,
            initial_estimate=initial_estimate
        )

        # 2. Identify missing mandatory fields
        missing = []
        if not policy.policy_number: missing.append("Policy Number")
        if not policy.policyholder_name: missing.append("Policyholder Name")
        if not loss.date: missing.append("Incident Date")
        if not loss.location: missing.append("Location")
        if not loss.description: missing.append("Description")
        if not parties.claimant: missing.append("Claimant")
        if not asset.asset_id: missing.append("Asset ID (VIN)")
        if asset.estimated_damage is None: missing.append("Estimated Damage")
        if not claim_type: missing.append("Claim Type")

        # 3. Identify Inconsistencies
        inconsistent = []
        if asset.estimated_damage and initial_estimate:
            if abs(asset.estimated_damage - initial_estimate) > 10.0:
                inconsistent.append("Discrepancy between Current and Initial Estimate")
        
        # 4. Routing Logic (Step 4)
        recommended_route = "Standard Workflow"
        reasoning = "The claim data is complete and follows standard criteria."

        # Priority 1: Manual Review for missing data
        if missing:
            recommended_route = "Manual Review"
            reasoning = f"Essential mandatory fields are missing: {', '.join(missing)}."
        
        # Priority 2: Inconsistency check
        elif inconsistent:
            recommended_route = "Manual Review"
            reasoning = f"Data validation failed: {', '.join(inconsistent)}."

        # Priority 3: Fraud detection
        elif loss.description and any(w in loss.description.lower() for w in ["fraud", "inconsistent", "staged"]):
            recommended_route = "Investigation Flag"
            reasoning = "Incident description contains flagged keywords (fraud/staged) indicating high risk."

        # Priority 4: Injury routing
        elif claim_type.lower() == "injury" or "injury" in (loss.description or "").lower():
            recommended_route = "Specialist Queue"
            reasoning = "Claim involves potential bodily injuries, routed to the specialized Medical Queue."

        # Priority 5: Auto-approval (Fast-track)
        elif asset.estimated_damage is not None and asset.estimated_damage < 25000:
            recommended_route = "Fast-track"
            reasoning = f"Damage estimate (${asset.estimated_damage:,.2f}) is below the $25,000 threshold for automated fast-tracking."

        # Priority 6: High Value
        elif asset.estimated_damage is not None and asset.estimated_damage >= 25000:
            recommended_route = "High-Value Review"
            reasoning = f"Claim estimate (${asset.estimated_damage:,.2f}) requires senior adjuster oversight due to high value."

        return ClaimResponse(
            extractedFields=fields,
            missingFields=missing,
            inconsistentFields=inconsistent,
            recommendedRoute=recommended_route,
            reasoning=reasoning
        )
