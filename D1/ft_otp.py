import argparse
import os
import sys
import hashlib
import cryptography

def main():
	args = get_args()
	if args.g:
		store_hex(args):
	if: args.k:
		generate_password_HOTP(args)

def get_args():
	parser = argparse.ArgumentParser()
	parser.add_argument("-g", type=str, action="store_true", help="he program receives as argument a hexadecimal key of at least 64 char-acters. The program stores this key safely in a file called ft_otp.key, which is encrypted")
	parser.add_argument("-k", type=str, action="store_true", help="-k: The program generates a new temporary password based on the key given as argument and prints it on the standard output.")
	args = parser.parse_args()
	try:
    with open(args.g, 'r') as file: pass
	except FileNotFoundError:
    	print("The file does not exist.")
	if ' ' in args.g: raise ValueError()
def store_hex(args):
	

def generate_password_HOTP(args):
	pass

if __name__ == "__main__":
	main()