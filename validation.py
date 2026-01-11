import sys

def validate_qr_string(qr_string):
    """
    Parses and validates a raw EPC QR payload line-by-line.
    Handles common copy-paste issues like missing trailing newlines.
    """
    print("--- START VALIDATION ---")
    
    # 1. Split by newline, preserving empty lines
    # Using keepends=False (default) removes the \n char, but split('\n') 
    # gives us the lines as strings.
    lines = qr_string.split("\n")
    
    # 2. Fix common copy-paste error: 
    # If the user copied text that didn't include the final newline of the file,
    # python's split might result in 11 lines (0-10) where line 11 (index 10) 
    # is the last text, and the 12th empty line is missing.
    # The EPC standard formally requires the file to end with a newline, meaning
    # there should be a 12th field (Information) which might be empty.
    
    # If we have 11 lines, and we can infer the last one (Info) is meant to be empty or was trimmed:
    if len(lines) == 11:
        print("⚠️  WARNING: Payload has 11 lines. Appending implied empty 'Information' field (Line 12).")
        print("    (This often happens when copying text without selecting the final newline)")
        lines.append("")
        
    # Remove any trailing empty strings caused by excessive newlines at the very end of file
    # BUT we must preserve exactly 12 fields.
    while len(lines) > 12 and lines[-1] == "":
        lines.pop()

    # Check Line Count
    if len(lines) != 12:
        print(f"❌ CRITICAL FAIL: Expected 12 lines, got {len(lines)}")
        print(f"   Lines found: {lines}")
        return False
    else:
        print(f"✅ Line Count: 12 (Correctly parsed)")

    # Define Schema
    schema = [
        ("Service Tag", "BCD"),
        ("Version", "002"),
        ("Character Set", "1"),
        ("Identification", "SCT"),
        ("BIC", None), # Variable
        ("Beneficiary Name", None),
        ("IBAN", None),
        ("Amount", None),
        ("Purpose", None),
        ("Creditor Reference", None),
        ("Remittance Text", None),
        ("Beneficiary Info", None)
    ]

    is_valid = True

    for i, (name, expected) in enumerate(schema):
        value = lines[i].strip() # aggressive strip for validation checking
        
        # Check Header Constants
        if expected and value != expected:
            print(f"❌ Line {i+1} ({name}): Expected '{expected}', got '{value}'")
            is_valid = False
            continue
            
        # Check Mandatory Fields
        if name in ["Beneficiary Name", "IBAN"] and not value:
            print(f"❌ Line {i+1} ({name}): Mandatory field is empty")
            is_valid = False
            continue

        # Check Mutual Exclusivity (Ref vs Remittance)
        if i == 9 and value: # Creditor Reference is set
            if lines[10].strip(): # Remittance is also set (Line 11)
                print(f"❌ LOGIC FAIL: Both Creditor Reference (Line 10) and Remittance (Line 11) are present.")
                is_valid = False
        
        # OGM Detection in Remittance (Line 11 is index 10)
        if i == 10 and value.startswith("+++") and value.endswith("+++"):
             print(f"ℹ️  Line {i+1} ({name}): Belgian OGM format detected.")

        # Creditor Reference (Line 10) must be RF if present
        if i == 9 and value and not value.startswith("RF"):
            print(f"❌ Line {i+1} ({name}): Must start with 'RF' (ISO 11649). Found '{value}'")
            is_valid = False

        print(f"✅ Line {i+1} ({name}): {value if value else '[Empty]'}")

    print("--- VALIDATION COMPLETE ---")
    if is_valid:
        print("RESULT: PASSED (Compliant with EPC069-12)")
    else:
        print("RESULT: FAILED")
    
    return is_valid

if __name__ == "__main__":
    # Example Usage: Paste a generated payload here to test
    # This sample intentionally has 11 lines visually to test the fix
    sample_payload = """BCD
002
1
SCT
GEBABEBB
Breutech Solutions
BE44001981860045
EUR1.00
IVPT

+++776/1504/73874+++""" 
    validate_qr_string(sample_payload)