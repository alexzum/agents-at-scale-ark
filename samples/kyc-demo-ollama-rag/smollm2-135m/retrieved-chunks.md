# Retrieved RAG Chunks from KYC Query

These are the exact 5 chunks retrieved from the vector store during the latest KYC assessment query.

## CHUNK 1/5: kyc_customer_profile.txt

```
## Adverse Media Screening
Comprehensive adverse media screening has been conducted across all key personnel with no significant negative findings identified.

## Risk Assessment Considerations
- Geographic Diversification: Operations span multiple jurisdictions requiring compliance with various regulatory frameworks
- Leadership Quality: Experienced board with independent directors and clear governance structure
- Screening Results: Clean screening results across all personnel with high confidence scores
- Documentation: Some nationality and residency information pending completion for certain individuals

## Regulatory Compliance
The entity demonstrates strong compliance posture with:
- Complete blacklist screening for all key personnel
- Proper identification of key controllers and beneficial owners
- Transparent ownership structure documentation
- Regular adverse media monitoring
```

## CHUNK 2/5: kyc_customer_profile.txt

```
## Business Activities
The entity appears to be a legitimate business operation with proper corporate governance structures, independent board oversight, and comprehensive compliance procedures in place.
```

## CHUNK 3/5: kyc_customer_profile.txt

```
# KYC Customer Profile Data

## Initial Profile
Based on the customer profile, this is a UK-based entity with multiple key controllers and directors from various nationalities including British, Australian, Turkish, French, and Canadian backgrounds.

## Screening Results

### Internal Blacklist Screening
All key personnel have been screened against internal blacklists with the following results:

**Graham Denis Allan**
- Role: Chair, Independent Director
- Nationality: British, Australian
- Country of Residency: England
- Type: Key Controller
- Blacklist Status: Not on blacklist
- Confidence Score: 10/10
- Justification: No match found

**Heather Victoria Rabbatts**
- Role: Senior Independent Director
- Nationality: British
- Country of Residency: United Kingdom
- Type: Key Controller
- Blacklist Status: Not on blacklist
- Confidence Score: 10/10
- Justification: No match found
```

## CHUNK 4/5: kyc_customer_profile.txt

```
## Key Controllers Analysis
The entity has a diverse international board composition with representatives from multiple jurisdictions. All key controllers have been verified and cleared through screening processes. The leadership structure includes:
- Chairman and CEO roles clearly defined
- Multiple independent directors providing governance oversight
- International experience across UK, Australia, Canada, Turkey, and France

## Ownership Structure
The ownership structure involves multiple entities and individuals with varying levels of control and influence. All controllers have been properly identified and screened.

## Adverse Media Screening
Comprehensive adverse media screening has been conducted across all key personnel with no significant negative findings identified.
```

## CHUNK 5/5: kyc_customer_profile.txt

```
**Anne Louise Murphy**
- Role: Independent Director
- Nationality: British
- Country of Residency: United Kingdom
- Type: Key Controller
- Blacklist Status: Not on blacklist
- Confidence Score: 10/10
- Justification: No match found

**Michael McLintock**
- Role: Chairman
- Nationality: Not available
- Country of Residency: Not available
- Type: Key Controller
- Blacklist Status: Not on blacklist
- Confidence Score: 10/10
- Justification: No match found

**Muhammad Anwar**
- Role: Chief Agentic Evaluation Officer
- Nationality: Not available
- Country of Residency: United Kingdom
- Type: Key Controller
- Blacklist Status: On blacklist
- Confidence Score: 7/10
- Justification: No match found

**George Weston**
- Role: Chief Executive Officer
- Nationality: Not available
- Country of Residency: Not available
- Type: Key Controller
- Blacklist Status: Not on blacklist
- Confidence Score: 10/10
- Justification: No match found
```

## Summary

- **Total chunks retrieved**: 5 out of 39 available chunks
- **Source file**: kyc_customer_profile.txt
- **Embedding model**: Azure OpenAI text-embedding-ada-002
- **Vector store**: FAISS
- **Key finding**: Muhammad Anwar identified as blacklisted personnel in Chunk 5
- **Search effectiveness**: Retrieved relevant sections covering compliance, screening results, and personnel profiles