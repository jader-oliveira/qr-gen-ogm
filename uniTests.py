import unittest
import re
from decimal import Decimal
from app import EuQrPayment, generate_belgian_ogm

class TestEuQrPayment(unittest.TestCase):

    def setUp(self):
        # A valid test IBAN (Belgian format)
        self.valid_iban = "BE44001981860045"
        self.payment = EuQrPayment(self.valid_iban)

    def test_iban_sanitization(self):
        """Test that spaces and invalid chars are removed from IBAN."""
        dirty_iban = "BE44 0019 8186 0045"
        p = EuQrPayment(dirty_iban)
        self.assertEqual(p.iban, self.valid_iban)

    def test_iban_validation_valid(self):
        """Test that a valid IBAN passes the Modulo 97 check."""
        self.assertTrue(self.payment.validate_iban())

    def test_iban_validation_invalid(self):
        """Test that an invalid IBAN fails."""
        # Change one digit to invalidate checksum
        invalid_iban = "BE44001981860046" 
        p = EuQrPayment(invalid_iban)
        self.assertFalse(p.validate_iban())

    def test_bic_sanitization(self):
        """Test that spaces are removed from BIC."""
        self.payment.set_bic("GEBA BE BB")
        self.assertEqual(self.payment.bic, "GEBABEBB")

    def test_ogm_generation_math(self):
        """Test the mathematical correctness of the Belgian OGM Modulo 97."""
        # Known example: Base 5337367152 -> Mod 97 is 61 -> Result +++533/7367/15261+++
        ogm = generate_belgian_ogm("5337367152")
        self.assertEqual(ogm, "+++533/7367/15261+++")

    def test_ogm_random_generation_structure(self):
        """Test that generated OGMs always follow +++000/0000/00000+++ format."""
        ogm = generate_belgian_ogm() # Random
        pattern = r"^\+\+\+\d{3}/\d{4}/\d{5}\+\+\+$"
        self.assertTrue(re.match(pattern, ogm))

    def test_payload_structure(self):
        """Test that the generated QR string has exactly 12 lines and correct headers."""
        self.payment.beneficiary_name = "Test Company"
        self.payment.amount = Decimal("100.00")
        self.payment.remittance_text = "Test Payment"
        
        payload = self.payment.get_qr_string()
        lines = payload.split("\n")
        
        # NOTE: Split by \n on a string ending in \n might create an empty trailing element
        # depending on python version/method, but standard behavior for .join("\n") 
        # is that it creates N-1 separators.
        # However, for the QR standard, we usually expect the string to end with a content line 
        # or empty line, resulting in 12 distinct fields.
        
        self.assertEqual(len(lines), 12, f"Payload must have exactly 12 lines, got {len(lines)}")
        self.assertEqual(lines[0], "BCD", "Line 1 must be Service Tag 'BCD'")
        self.assertEqual(lines[1], "002", "Line 2 must be Version '002'")
        self.assertEqual(lines[2], "1", "Line 3 must be Charset '1' (UTF-8)")
        self.assertEqual(lines[3], "SCT", "Line 4 must be Identification 'SCT'")

    def test_mutual_exclusivity(self):
        """Test that setting both Reference AND Remittance raises an error."""
        self.payment.beneficiary_name = "Test"
        self.payment.creditor_reference = "RF18"
        self.payment.remittance_text = "Some text"
        
        with self.assertRaises(ValueError):
            self.payment.get_qr_string()

if __name__ == '__main__':
    unittest.main()