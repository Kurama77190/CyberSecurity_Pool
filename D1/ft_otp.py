import argparse
import base64
import os
import sys
import hashlib
from cryptography.fernet import Fernet

def main():
	args = get_args()
	if args.g != None:
		store_hex(args)
	if args.k != None:
		generate_password_HOTP(args)

def get_args():
	parser = argparse.ArgumentParser()
	parser.add_argument("-g", type=str, help="he program receives as argument a hexadecimal key of at least 64 char-acters. The program stores this key safely in a file called ft_otp.key, which is encrypted")
	parser.add_argument("-k", type=str, help="-k: The program generates a new temporary password based on the key given as argument and prints it on the standard output.")
	args = parser.parse_args()
	return args
def store_hex(args):
	try:
		# Read hexadecimal key from file
		with open(args.g, 'r') as file:
			hex_key = file.read().strip()
		
		# Validate it's valid hexadecimal
		if not check_hex(hex_key):
			raise ValueError("error: key must be a valid hexadecimal string.")
		
		# Check length (at least 64 hex characters)
		if not check_length(hex_key):
			raise ValueError("error: key must be 64 hexadecimal characters minimum.")
		
		# Store in ft_otp.key (encrypted)
		secrete_key = secrete_key()
		cipher = Fernet(secrete_key)
		encrypted_key = cipher.encrypt(hex_key.encode())
		with open("ft_otp.key", 'wb') as file:
			file.write(encrypted_key)
		print("Key was successfully saved in ft_otp.key.")
		
	except FileNotFoundError:
		print("error: file not found.")
	except ValueError as e:
		print(f"error: {e}")

def check_hex(hex_string):
	try:
		int(hex_string, 16)
		return True
	except ValueError:
		return False

def check_length(hex_string):
	return len(hex_string) >= 64

# Secrete_key is the key used to encrypt the hexadecimal key and store it in ft_otp.key.
def secrete_key():
	try:
		with open("decrypted.key", 'r') as file:
			encrypted_key = file.read().strip()
			return encrypted_key
	except FileNotFoundError:
		print("error: decrypted.key not found.")
		sys.exit(1)

def generate_password_HOTP(args):
	pass

def crypted_key(hex_key):
	return hashlib.sha256(hex_key.encode()).hexdigest()

if __name__ == "__main__":
	main()