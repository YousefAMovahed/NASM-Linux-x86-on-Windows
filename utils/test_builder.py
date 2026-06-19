import json
import base64
from cryptography.fernet import Fernet

# Shared key matching the internal IDE encryption configurations
SECRET_KEY = base64.urlsafe_b64encode(b"UniversityOfTehranAssemblyClass!".ljust(32, b'0'))
cipher = Fernet(SECRET_KEY)

# Test cases for the Palindrome Detection assignment
# '\n' simulates the user pressing 'Enter' to test input trimming subroutines
test_cases = [
    {"input": "radar\n", "expected_output": "yes"},
    {"input": "noon\n", "expected_output": "yes"},
    {"input": "hello\n", "expected_output": "no"},
    {"input": "Radar\n", "expected_output": "no"},   # Case-sensitivity validation
    {"input": "\n", "expected_output": "yes"},        # Empty string boundary condition
    {"input": "race car\n", "expected_output": "no"}  # Space symmetry validation
]

# Serialize to JSON and encrypt via Fernet platform
json_data = json.dumps(test_cases).encode('utf-8')
encrypted_data = cipher.encrypt(json_data)

# Save the encrypted test matrix asset
output_filename = "palindrome.dat"
with open(output_filename, "wb") as f:
    f.write(encrypted_data)

print(f"[SUCCESS] Secure test file '{output_filename}' generated.")
print("[INFO] Upload this file to your LMS for student distribution.")