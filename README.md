# Euro Payment QR & OGM Generator

A comprehensive Streamlit application for generating **EPC QR codes** for SEPA payments with support for **Belgian OGM (Structured Communication)**, strict IBAN validation, and multiple reference types.

---

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Installation](#installation)
- [Usage](#usage)
- [Architecture](#architecture)
- [Core Components](#core-components)
- [Validation Logic](#validation-logic)
- [Reference Types](#reference-types)
- [Technical Details](#technical-details)

---

## 🎯 Overview

This application enables users to:

1. **Generate EPC QR Codes** compliant with EPC standards for European payments
2. **Validate IBANs** using the modulo-97 checksum algorithm
3. **Support Multiple Reference Types**:
   - Unstructured remittance text
   - ISO 11649 Structured References (RF format)
   - Belgian OGM (+++XXX/XXXX/XXXXX+++)
4. **Sanitize Input Data** to ensure EPC compliance
5. **Preview QR Codes** in real-time

---

## ✨ Features

### 🔐 IBAN Validation
- Regex pattern matching for IBAN structure
- **Modulo-97 checksum verification** following the IBAN standard
- Support for IBANs with spaces (auto-sanitized)

### 🇧🇪 Belgian OGM Support
- Automatic OGM generation with check digits
- **Modulo-97 calculation** for checksum validation
- Format: `+++XXX/XXXX/XXXXX+++`
- Optional: Base number input for custom OGM generation

### 📊 SEPA Purpose Codes
Built-in dictionary of 20+ SEPA purpose codes including:
- `SALA` - Salary Payment
- `IVPT` - Invoice Payment
- `CHAR` - Charity Payment
- `RENT` - Rent
- And many more...

### 🎨 User Interface
- Clean, responsive Streamlit layout
- Hidden default Streamlit chrome (menu, footer, etc.)
- Real-time validation feedback
- Expandable sections for better UX
- Success/Error notifications

### 🔍 Data Sanitization
- Automatic space removal from IBAN/BIC
- Text trimming and length limiting
- Alphanumeric filtering for structured references
- HTML escaping for security

---

## 📦 Installation

### Prerequisites
- Python 3.8+
- pip (Python package manager)

### Setup

```bash
# Clone or download the project
cd SEPA_QR_Code

# Install dependencies
pip install -r requirements.txt
```

### Dependencies

```
streamlit>=1.0.0
segno>=1.9.0
```

---

## 🚀 Usage

### Run the Application

```bash
streamlit run app.py
```

The app will launch at `http://localhost:8501`

### Workflow

#### Step 1: Enter Beneficiary Details
- **Beneficiary Name** (Required): Company or person receiving the payment
- **IBAN** (Required): International Bank Account Number
- **BIC/SWIFT** (Optional): Bank Identifier Code

#### Step 2: Set Payment Details
- **Currency**: EUR (fixed)
- **Amount**: 0.00 - 999,999,999.99
- **SEPA Purpose Code**: Select from dropdown

#### Step 3: Choose Communication Type
- **Unstructured (Remittance)**: Free-form text up to 140 characters
- **Structured (ISO 11649 RF)**: ISO standard reference starting with "RF"
- **Belgian OGM**: Proprietary format with optional custom base number

#### Step 4: Generate & Download
- Click "Generate QR Code"
- View the QR code preview
- Inspect the cleaned payload data

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────┐
│   Streamlit Web Interface               │
│  (User Input, Validation Feedback)      │
└────────────────┬────────────────────────┘
                 │
        ┌────────▼─────────┐
        │  EuQrPayment     │
        │   (Core Logic)   │
        └────────┬─────────┘
                 │
        ┌────────┴─────────────────┐
        │                          │
    ┌───▼──────┐          ┌───────▼───┐
    │ IBAN     │          │ OGM       │
    │ Validator│          │ Generator │
    └───┬──────┘          └───────┬───┘
        │                         │
        │   Segno QR Library      │
        │   (PNG Generation)      │
        │                         │
        └────────┬────────────────┘
                 │
        ┌────────▼──────────┐
        │  PNG QR Code      │
        │  (Downloaded)     │
        └───────────────────┘
```

---

## 🔧 Core Components

### 1. **SEPAConstants Class**

Holds static configuration:

```python
class SEPAConstants:
    PURPOSE_CODES = {
        "ACCT": "Account Management",
        "SALA": "Salary Payment",
        "IVPT": "Invoice Payment",
        # ... 20+ more codes
    }
```

### 2. **EuQrPayment Class**

Main payment object with validation and QR generation:

#### Attributes
- `iban`: International Bank Account Number
- `bic`: Bank Identifier Code
- `beneficiary_name`: Recipient name (max 70 chars)
- `amount`: Payment amount in EUR
- `purpose`: SEPA purpose code
- `remittance_text`: Unstructured reference (max 140 chars)
- `creditor_reference`: ISO 11649 reference (starts with "RF")
- `information`: Additional info (max 70 chars)
- `version`: EPC standard version ("002")
- `char_set`: Character encoding ("1" = UTF-8)

#### Key Methods

**`_sanitize_alphanum(text)`**
- Removes spaces and non-alphanumeric characters
- Converts to uppercase
- Returns clean A-Z, 0-9 only

**`_sanitize_text(text, max_len)`**
- Trims whitespace
- Limits string length
- Safe for display/encoding

**`validate_iban()`**
- Regex: `^[A-Z]{2}\d{2}[A-Z0-9]{1,30}$`
- Modulo-97 checksum verification
- Returns boolean

**`get_qr_string()`**
- Assembles EPC QR payload
- Validates logic constraints
- Returns formatted string with newlines

### 3. **generate_belgian_ogm(base_num)**

Generates valid Belgian OGM with check digits:

#### Algorithm
```
Input: 10-digit base number (or random)
├─ Extract digits only
├─ Calculate: mod = base % 97
├─ If mod == 0: mod = 97
├─ Format: +++XXX/XXXX/XXXXX+++
└─ Output: Valid OGM string
```

---

## ✅ Validation Logic

### IBAN Validation Process

```
Input: "BE44 0000 0000 0000"
    │
    ├─ Sanitize: "BE4400000000000000"
    │
    ├─ Check regex: ^[A-Z]{2}\d{2}[A-Z0-9]{1,30}$
    │   ✓ Pass
    │
    ├─ Rearrange: "00000000000000BE44"
    │
    ├─ Convert to numeric:
    │   B=11, E=14 → "00000000000000111444"
    │
    ├─ Modulo 97: 111444 % 97 == 1
    │   ✓ Valid IBAN
    │
    └─ Return: true
```

### QR Payload Constraints

```
Validation Rules:
├─ Beneficiary Name: REQUIRED (1-70 chars)
├─ IBAN: REQUIRED + Valid checksum
├─ Either remittance OR creditor_ref (not both)
├─ If creditor_ref present: MUST start with "RF"
└─ Amount: 0.00 - 999,999,999.99
```

---

## 📝 Reference Types

### Type 1: Unstructured Remittance
```
Purpose: Invoice INV-2024-001
Limit: 140 characters
Use Case: Flexible, human-readable
EPC Field: AT-20
```

### Type 2: ISO 11649 Structured Reference
```
Format: RF18XXXXXXXXXXXX
Checksum: Calculated per ISO 11649
Use Case: Bank-to-bank structured payments
EPC Field: AT-44
Constraint: MUST start with "RF"
```

### Type 3: Belgian OGM
```
Format: +++XXX/XXXX/XXXXX+++
Example: +++123/1234/12345+++
Checksum: Last 2 digits = (first 10 digits) % 97
Use Case: Belgian domestic payments
Technical: Placed in remittance field (AT-20)
```

---

## 📊 Technical Details

### EPC QR Code Structure

The generated QR string follows the **EPC Standard v2.0**:

```
BCD                          ← Service tag
002                          ← Version
1                            ← Character set (UTF-8)
SCT                          ← SEPA Credit Transfer
BIC                          ← Bank Identifier Code
Beneficiary Name             ← Recipient (max 70 chars)
IBAN                         ← Account number
EUR1234.56                   ← Amount (or empty)
SALA                         ← Purpose code
RF18XXX                      ← Creditor reference (optional)
Invoice INV-001              ← Remittance text (optional)
Additional info              ← Info (optional, max 70 chars)
```

### Data Sanitization Pipeline

```
Raw Input
    │
    ├─ IBAN/BIC: [^A-Z0-9] removed, uppercase
    │
    ├─ Name/Text: whitespace trimmed, length limited
    │
    ├─ Creditor Ref: alphanumeric only
    │
    └─ Output: EPC-safe payload
```

### Segno QR Generation

```python
qr = segno.make(
    raw_payload,        # EPC string
    encoding='utf-8',   # UTF-8 encoding
    error='M'           # 15% error correction
)

qr.save(
    out_buffer,
    kind='png',
    scale=10,           # 10px per module
    border=4            # 4 modules quiet zone
)
```

---

## 🖼️ UI Layout

```
┌─────────────────────────────────────────────────────┐
│  Euro Payment QR & OGM Generator                    │
│  Strict validation & Belgian OGM support            │
└─────────────────────────────────────────────────────┘

┌──────────────────────────┬──────────────────────────┐
│                          │                          │
│  1. Beneficiary Details  │   QR Preview             │
│  ├─ Name                 │   [Generate Button]      │
│  ├─ IBAN                 │                          │
│  └─ BIC                  │   [QR Code Display]      │
│                          │                          │
│  2. Payment Details      │   [Payload Inspector]    │
│  ├─ Currency (EUR)       │                          │
│  ├─ Amount               │                          │
│  └─ Purpose Code         │                          │
│                          │                          │
│  3. Communication Type   │                          │
│  ├─ Unstructured         │                          │
│  ├─ Structured (RF)      │                          │
│  └─ Belgian OGM          │                          │
│      ├─ Base Number      │                          │
│      └─ [Generate OGM]   │                          │
│                          │                          │
└──────────────────────────┴──────────────────────────┘
```

---

## 🔒 Security & Compliance

✅ **IBAN Checksum Validation**: Prevents invalid account numbers  
✅ **HTML Escaping**: XSS protection via `unsafe_allow_html=False`  
✅ **Input Sanitization**: Removes dangerous characters  
✅ **EPC Compliance**: Follows official EPC QR standards  
✅ **Character Encoding**: UTF-8 throughout  

---

## 📈 Example Workflow

```
User Input:
  Beneficiary: "ACME Corp"
  IBAN: "BE44 0000 0000 0000"
  BIC: "GEBABE BB"
  Amount: 100.00
  Purpose: "SALA" (Salary)
  Type: "Belgian OGM"
  Base: "1234567890"

↓

Processing:
  ├─ Sanitize: IBAN → "BE4400000000000000"
  ├─ Validate: IBAN checksum ✓
  ├─ Generate: OGM → "+++123/4567/89XX+++"
  ├─ Assemble: EPC payload
  └─ Encode: QR code (PNG)

↓

Output:
  ✅ QR Code (350px width)
  ✅ Payload Inspector (7-line text)
  ✅ Success Message
```

---

## 🐛 Error Handling

```
Validation Error                  User Feedback
────────────────────────────────────────────────
Invalid IBAN                       ❌ Invalid IBAN checksum
Missing beneficiary                ⚠️ Name is required
Both remittance & creditor_ref     ❌ Cannot set both
Non-RF creditor reference          ❌ Must start with RF
System exception                   ❌ System Error
```

---

## 🎓 EPC Standard Reference

**Standard**: EPC QR Code Guidelines v2.0  
**Format**: BCD (Bank Code Distribution)  
**Fields**: 12 required/optional fields  
**Encoding**: UTF-8  
**Error Correction**: M (15%)  

---

## 📄 License & Attribution

This implementation is based on the **EPC QR Code Standard** and inspired by the `rikudou/euqrpayment` PHP library logic, adapted for Python + Streamlit.

---

## 🤝 Support

For issues, improvements, or questions:
- Check IBAN validity at: https://www.iban.com/
- EPC Standard: https://www.europeanpaymentscouncil.eu/
