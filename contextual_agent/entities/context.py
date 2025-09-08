from pydantic import BaseModel

class UserData(BaseModel):
    service_provided: str

class CompanyProfile(BaseModel):
    industry_niche: str
    company_size: str | None = None
    location: str | None = None

class OpportunitySignals(BaseModel):
    green_flags: list[str] | None = []
    red_flags: list[str] | None = []

class ClientData(BaseModel):
    company_profile: CompanyProfile
    opportunity_signals: OpportunitySignals

class ContextData(BaseModel):
    user_info: UserData
    ideal_client: ClientData

    def get_profile(self):
        return self.user_info.service_provided

    def get_client(self):
        company_profile = self.ideal_client.company_profile
        industry_niche = company_profile.industry_niche
        company_size = company_profile.company_size
        location = company_profile.location
        client_profile = industry_niche
        if company_size:
            client_profile += f", size {company_size}"
        if location:
            client_profile += f", location {location}"
        return client_profile

    def get_criterias(self):
        opportunity_signals = self.ideal_client.opportunity_signals
        green_flags = opportunity_signals.green_flags or []
        red_flags = opportunity_signals.red_flags or []
        return f"Green flags: {', '.join(green_flags)}\n Red flags: {', '.join(red_flags)}"
