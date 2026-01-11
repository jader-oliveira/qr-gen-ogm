import streamlit as st
import segno
import io
import re
import random
from decimal import Decimal

# ==========================================
# 1. CORE LOGIC & VALIDATORS
# ==========================================

class SEPAConstants:
    PURPOSE_CODES = {
        "ACCT": "Account Management",
        "BONU": "Bonus Payment",
        "CHAR": "Charity Payment",
        "COLL": "Collection Payment",
        "COMC": "Commercial Payment",
        "CPYR": "Copyright",
        "DIVD": "Dividend",
        "EDUC": "Education",
        "GOVT": "Government Payment",
        "INSU": "Insurance Premium",
        "INTC": "Intra Company Payment",
        "INVS": "Investment & Securities",
        "IVPT": "Invoice Payment",
        "LOAN": "Loan",
        "PENS": "Pension Payment",
        "RENT": "Rent",
        "SALA": "Salary Payment",
        "SSBE": "Social Security Benefit",
        "SUPP": "Supplier Payment",
        "TAXCs": "Tax Payment",
        "TRAD": "Commercial",
        "UTIL": "Utilities",
    }

class EuQrPayment:
    """
    Python implementation of rikudou/euqrpayment logic with added Strict Validation.
    """
    def __init__(self, iban: str):
        self.iban = self._sanitize_alphanum(iban)
        self.bic = ""
        self.beneficiary_name = ""
        self.amount = Decimal("0.00")
        self.currency = "EUR"
        self.purpose = ""
        self.remittance_text = ""
        self.creditor_reference = ""
        self.information = ""
        self.version = "002"
        self.char_set = "1" # 1 = UTF-8

    def _sanitize_alphanum(self, text):
        """Removes spaces and non-alphanumeric characters (keeps only A-Z, 0-9)."""
        if not text:
            return ""
        return re.sub(r'[^A-Z0-9]', '', text.upper())

    def _sanitize_text(self, text, max_len):
        """Trims whitespace and limits length."""
        if not text:
            return ""
        return text.strip()[:max_len]

    def set_bic(self, bic):
        self.bic = self._sanitize_alphanum(bic)

    def validate_iban(self) -> bool:
        if not self.iban:
            return False
        # Basic regex pattern for generic IBAN structure
        if not re.match(r'^[A-Z]{2}\d{2}[A-Z0-9]{1,30}$', self.iban):
            return False
        # Move first 4 characters to the end
        rearranged = self.iban[4:] + self.iban[:4]
        # Convert letters to numbers (A=10, B=11, ...)
        numeric_iban = ""
        for char in rearranged:
            if char.isdigit():
                numeric_iban += char
            else:
                numeric_iban += str(ord(char) - 55)
        # Modulo 97 check
        return int(numeric_iban) % 97 == 1

    def get_qr_string(self) -> str:
        # 1. Clean Data strictly before generating
        final_iban = self._sanitize_alphanum(self.iban)
        final_bic = self._sanitize_alphanum(self.bic)
        final_name = self._sanitize_text(self.beneficiary_name, 70)
        final_creditor_ref = self._sanitize_alphanum(self.creditor_reference) # RF ref should be pure alphanum in payload
        final_remittance = self._sanitize_text(self.remittance_text, 140)
        final_info = self._sanitize_text(self.information, 70)

        # 2. Logic Constraints
        if not final_name:
            raise ValueError("Beneficiary Name is required.")
        if final_remittance and final_creditor_ref:
            raise ValueError("Cannot set both Remittance Text and Creditor Reference.")
        
        # 3. Reference Validation (EPC Standard)
        # The standard says AT-44 (Creditor Ref) MUST start with RF.
        if final_creditor_ref and not final_creditor_ref.startswith('RF'):
             raise ValueError("Structured Reference (AT-44) must be an ISO 11649 Reference starting with 'RF'. Use Remittance Text for other formats.")

        amount_str = f"{self.currency}{self.amount:.2f}" if self.amount > 0 else ""

        lines = [
            "BCD",
            self.version,
            self.char_set,
            "SCT",
            final_bic,
            final_name,
            final_iban,
            amount_str,
            self.purpose,
            final_creditor_ref,
            final_remittance,
            final_info
        ]
        
        return "\n".join(lines)

# --- Helper: Belgian OGM Generator ---
def generate_belgian_ogm(base_num: str = None) -> str:
    """
    Generates a valid Belgian OGM (Virement à Communication Structurée).
    Format: +++123/1234/12345+++
    Logic: Last 2 digits are Modulo 97 of the previous 10 digits.
    """
    if not base_num:
        # Generate random 10 digit number
        base_num = str(random.randint(1000000000, 9999999999))
    
    # Ensure we have digits only
    digits = re.sub(r'\D', '', base_num)
    
    # Pad or trim to 10 digits for the base (excluding check digits)
    # Standard OGM is 12 digits total (10 data + 2 check)
    if len(digits) > 10:
        digits = digits[:10]
    else:
        digits = digits.zfill(10)
        
    # Calculate Check Digits (Mod 97)
    base_int = int(digits)
    mod = base_int % 97
    if mod == 0:
        mod = 97
    
    check_digits = f"{mod:02d}"
    full_digits = digits + check_digits
    
    # Format: +++XXX/XXXX/XXXXX+++
    # Grouping: 3 / 4 / 5
    part1 = full_digits[0:3]
    part2 = full_digits[3:7]
    part3 = full_digits[7:12]
    
    return f"+++{part1}/{part2}/{part3}+++"

# ==========================================
# 2. STREAMLIT INTERFACE
# ==========================================

# 1. Page Config MUST be the first Streamlit command
st.set_page_config(
    page_title="QR Generator", 
    page_icon="💳", 
    layout="wide"
)

# 2. Your Custom CSS to Hide Menus & Footer
hide_streamlit_style = """
<style>
    /* Hide hamburger menu, header, and footer */
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Hide the top-right rerun/run buttons */
    [data-testid="stStatusWidget"] {visibility: hidden;}
    button[title="View app in Streamlit Cloud"] {display: none;}
    
    /* Remove the "Made with Streamlit" badge */
    .stAppFooter {display: none !important;}
    
    /* General clean-up for a 'web-app' feel */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
</style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

# 3. Custom Button Styling (Optional, keeps the blue buttons)
st.markdown("""
<style>
    .stButton>button { width: 100%; font-weight: bold; }
    .main { background-color: #f8f9fa; }
    .success-box { padding:10px; background-color:#d4edda; color:#155724; border-radius:5px; border:1px solid #c3e6cb; }
</style>
""", unsafe_allow_html=True)

col_header, col_logo = st.columns([4, 1])
with col_header:
    st.title("Euro Payment QR & OGM Generator")
    st.markdown("Strict validation & Belgian Structured Communication (OGM) support.")

with st.container():
    col_left, col_right = st.columns([1, 1], gap="large")

    with col_left:
        st.subheader("1. Beneficiary Details")
        with st.expander("Account Information", expanded=True):
            beneficiary_name = st.text_input("Beneficiary Name *", max_chars=70, placeholder="Company Name")
            
            # IBAN Input with auto-cleanup hint
            iban_raw = st.text_input("IBAN *", placeholder="BE44 0000 0000 0000")
            
            # BIC Input with auto-cleanup hint
            bic_raw = st.text_input("BIC / SWIFT", max_chars=15, help="Spaces will be removed automatically.")

        st.subheader("2. Payment Details")
        with st.expander("Transaction Specifics", expanded=True):
            c1, c2 = st.columns([1, 2])
            with c1:
                currency = st.selectbox("Currency", ["EUR"], disabled=True)
            with c2:
                # Fix: min_value=0.00 to allow open amounts
                amount_input = st.number_input("Amount", min_value=0.00, max_value=999999999.99, value=0.00, step=0.01, format="%.2f")
            
            purpose_options = [""] + list(SEPAConstants.PURPOSE_CODES.keys())
            purpose_labels = lambda x: f"{x} - {SEPAConstants.PURPOSE_CODES[x]}" if x in SEPAConstants.PURPOSE_CODES else "None"
            purpose_code = st.selectbox("SEPA Purpose Code", options=purpose_options, format_func=purpose_labels)

        st.subheader("3. Communication Type")
        comm_type = st.radio("Select Reference Type", 
                             ["Unstructured (Remittance)", "Structured (ISO 11649 RF)", "Belgian OGM (+++...+++)"], 
                             horizontal=True)

        final_remittance_val = ""
        final_creditor_ref_val = ""

        if comm_type == "Unstructured (Remittance)":
            final_remittance_val = st.text_area("Remittance Text", max_chars=140, placeholder="Invoice Jan 2024")
            
        elif comm_type == "Structured (ISO 11649 RF)":
            final_creditor_ref_val = st.text_input("Creditor Reference", placeholder="RF18...", help="Must start with RF")
            
        elif comm_type == "Belgian OGM (+++...+++)":
            st.info("💡 Belgian OGM is technically 'Unstructured' in strict EPC QR standards unless mapped to RF. We will generate it correctly and place it in the Remittance field to ensure validity.")
            
            ogm_col1, ogm_col2 = st.columns([2, 1])
            with ogm_col1:
                base_for_ogm = st.text_input("Base Number (Optional)", help="Enter numbers to base the OGM on, or leave empty for random.")
            with ogm_col2:
                if st.button("Generate OGM"):
                    st.session_state['generated_ogm'] = generate_belgian_ogm(base_for_ogm)
            
            if 'generated_ogm' in st.session_state:
                st.markdown(f"<div class='success-box'><b>Generated:</b> {st.session_state['generated_ogm']}</div>", unsafe_allow_html=True)
                final_remittance_val = st.session_state['generated_ogm']
            else:
                final_remittance_val = generate_belgian_ogm("0000000000") # Preview default

    # --- Generation ---
    with col_right:
        st.subheader("QR Preview")
        generate_btn = st.button("Generate QR Code", type="primary")

        if generate_btn or (iban_raw and beneficiary_name):
            try:
                # 1. Init & Sanitize
                payment = EuQrPayment(iban_raw)
                payment.set_bic(bic_raw) # Sanitize BIC
                
                # 2. Validation Checks
                if not payment.validate_iban():
                    st.error(f"❌ Invalid IBAN checksum or format: {payment.iban}")
                elif not beneficiary_name:
                    st.warning("⚠️ Beneficiary Name is required.")
                else:
                    payment.beneficiary_name = beneficiary_name
                    payment.amount = Decimal(amount_input) if amount_input > 0 else Decimal(0)
                    payment.purpose = purpose_code
                    
                    # Logic for OGM vs Standard
                    if comm_type == "Structured (ISO 11649 RF)":
                         payment.creditor_reference = final_creditor_ref_val
                    else:
                         # Belgian OGM goes here as well
                         payment.remittance_text = final_remittance_val

                    # 3. Generate
                    raw_payload = payment.get_qr_string()
                    
                    # 4. Render
                    qr = segno.make(raw_payload, encoding='utf-8', error='M')
                    out_buffer = io.BytesIO()
                    qr.save(out_buffer, kind='png', scale=10, border=4)
                    
                    st.image(out_buffer, width=350)
                    
                    st.success("✅ Valid QR Payload Generated")
                    with st.expander("Inspect Cleaned Payload"):
                        st.text(raw_payload)
                        st.caption("Note: IBAN and BIC have been stripped of spaces. Belgian OGM (if selected) is in the remittance field.")

            except ValueError as e:
                st.error(f"❌ Validation Error: {str(e)}")
            except Exception as e:
                st.error(f"❌ System Error: {str(e)}")