import os
from py4lexis.session import LexisSession

print("Starting LEXIS interactive login...")
lexis_session = LexisSession()
token = lexis_session.get_access_token()

# Define a hidden file path in your home directory
token_path = os.path.expanduser("~/.lexis_token")

# Save the token string
with open(token_path, "w") as f:
    f.write(token)

# Restrict file permissions so only you can read/write it (Security best practice)
os.chmod(token_path, 0o600)

print(f"Token successfully saved to {token_path}!")
print("You can now submit Slurm jobs for the next few days without logging in again.")