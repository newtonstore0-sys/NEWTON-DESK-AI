---
name: funding-engine
description: >
  Hermes.Modules.FundingEngine — a plug-in capability for discovering, evaluating,
  and pursuing UK funding routes (grants, loans, microfinance, invoice finance,
  asset-secured lending, hardship, consortium, CDFIs, regeneration funds).
  Activates ONLY when funding is needed — not Hermes' identity.
category: software-development
tags:
  - funding
  - grants
  - loans
  - uk-business
  - finance
  - capital
  - cashflow
---

# Hermes.Modules.FundingEngine

A self-contained internal module that activates only when Hermes detects a funding need.
Hermes stays exactly as it is — strategic business intelligence agent — but gains
this as one of many skills, not its identity.

---

## When This Activates

**Explicit triggers:**
- "find funding", "get grants", "we need a loan", "we need money for X"
- "cashflow is low", "we need capital", "find investors"

**Implicit triggers (Hermes detects):**
- Cashflow pressure in accounts/emails
- Upcoming capex (refurb, shop build, freehold purchase)
- Regeneration project (High Street, Lancaster)
- Growth plan needing capital
- CCJ/default mitigation needed
- Director credit issues

---

## Module Architecture

### Sub-Modules

#### 1. FundingScanner
- **Role:** Discover all possible funding routes
- **Inputs:** business profile, location (Lancaster/LA1), sector, project type, credit status
- **Outputs:** list of candidate routes (grants, loans, microfinance, invoice finance, supplier credit, asset-secured, consortium, hardship)
- **Search targets:**
  - UK government grants (gov.uk, Innovate UK, UKRI)
  - Local council grants (Lancaster City Council, Lancashire County Council)
  - CDFIs (community development finance institutions)
  - Growth Guarantee Scheme (formerly Recovery Loan Scheme)
  - British Business Bank programs
  - Start Up Loans
  - SEIS/EIS (if applicable)
  - Hardship/emergency funds
  - Regeneration funds (High Street, town centres)
  - Social enterprise grants
  - Energy efficiency grants
  - Digital transformation grants

#### 2. EligibilityEngine
- **Role:** Check formal eligibility + soft criteria
- **Hard rules:** turnover, trading age, sector, location, director status
- **Soft rules:** innovation, social impact, regeneration alignment, digital, energy, diversity

#### 3. LoopholeEngine
Apply legal exceptions and alternative routes:
- **DirectorSwapRoute** — properly registered director changes for eligibility
- **GuarantorOverrideRoute** — third-party guarantors for secured lending
- **AssetSecuredRoute** — property/equipment/invoices as collateral
- **ConsortiumRoute** — joint applications with partner businesses
- **SocialEnterpriseRoute** — B Corp/community interest company classification
- **HardshipRoute** — emergency/bereavement/health-related funding
- **CCJMitigationRoute** — sat-isfied CCJs, time-based decay, credit repair paths

#### 4. StrategyBuilder
Produce 3 concrete strategies:
- **Aggressive** — max applications, parallel submissions, higher risk
- **Balanced** — mix of grants + safer lending
- **Safe** — low-risk, low-pressure, slower timeline

#### 5. DocumentPackBuilder
Auto-generate everything needed:
- Business plan
- Cashflow forecast (12-month)
- CCJ/default mitigation pack
- Project justification narrative
- Social impact statement
- Innovation narrative
- Director/guarantor profiles
- Asset register (for secured lending)
- Supporting evidence pack

#### 6. SubmissionCoordinator
Hand off to other agents/systems:
- **Vulcan** — document formatting, PDF generation, form filling
- **Apollo** — submission, tracking, follow-ups
- **Athena** — legality/compliance checks before submission

---

## Data Models

### BusinessFundingProfile
```yaml
name: Silva Retail Ltd
location: Lancaster, LA1
sector: Retail / Convenience
trading_years: X
turnover: £X
staff: X
assets:
  property: [Langdale Place, 6F Steamer Street]
  vehicles: []
  equipment: [POS system, CCTV]
  invoices: []
credit_status:
  ccss: []
  defaults: []
  director_credit: unknown
social_impact_flags: []
projects: []
```

### FundingRoute
```yaml
type: grant | loan | microfinance | invoice_finance | supplier_credit | asset_secured | consortium | hardship
provider: string
amount_min: £X
amount_max: £X
eligibility_rules: []
risk_level: low | medium | high
required_documents: []
special_routes: [guarantor, director_swap, consortium, etc.]
deadline: date or null
url: string
```

### FundingPlan
```yaml
strategies:
  aggressive: [FundingRoute...]
  balanced: [FundingRoute...]
  safe: [FundingRoute...]
actions: []
timeline: string
total_potential: £X
```

---

## Known Active Funding Routes (Silva Retail)

| Route | Provider | Status | Notes |
|-------|----------|--------|-------|
| Growth Guarantee Scheme (GGS) | Funding Options / Tide | **ACTIVE — monitoring** | Successor to Recovery Loan Scheme. Email alerts set up. |
| PayPoint Settlement | PayPoint | **ACTIVE — monitoring** | Weekly DD, billing via my.paypoint.com |
| Parfetts Wholesale | Parfetts | **POTENTIAL** | MAD FRIDAY deals, supplier credit possible |
| Booker Wholesale | Booker | **POTENTIAL** | Everyday low price deals, supplier credit possible |
| Start Up Loans | British Business Bank | **ELIGIBLE** | Government-backed, 6% fixed rate |
| Lancashire Council Grants | LCC | **CHECK** | Various regeneration and business support |
| CDFIs | Various | **CHECK** | Community development finance |

---

## Behavioural Rules (Guardrails)

### ALLOWED
- Legal exceptions and alternative classifications
- Director swap (properly registered at Companies House)
- Guarantor use (with full consent)
- Asset-secured lending (property, equipment, invoices)
- Consortium applications (with partner businesses)
- Hardship/emergency funds (when genuinely applicable)
- Social enterprise classification (only when legally accurate)

### FORBIDDEN
- Falsifying financial documents
- Hiding CCJs or defaults
- Impersonating directors or applicants
- Fabricating turnover figures
- Submitting fraudulent applications
- Misrepresenting business circumstances

---

## How To Use

When Silva asks about funding:
1. Load this skill
2. Assess the funding need (what, how much, why, when)
3. Update BusinessFundingProfile from memory/email data
4. Run FundingScanner to find routes
5. Run EligibilityEngine against each route
6. Run LoopholeEngine for alternative paths
7. Build strategies (aggressive/balanced/safe)
8. Generate DocumentPack if proceeding
9. Coordinate submission via available channels

When NOT needed: this skill stays dormant. Hermes does not become a funding agent.

---

## Email Monitoring

Silva has opted to keep monitoring these funding-related email threads:
- **PayPoint settlement notices** — mark as read after review
- **Funding Options / Tide** — GGS and loan opportunity alerts
- **Rentaroof property alerts** — keep active for rental market data
- **Parfetts / Booker wholesale** — supplier credit opportunities

Use `scripts/mark_read.py` to mark reviewed emails as read.
