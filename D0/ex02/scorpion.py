import sys
import os
import signal
import threading
import customtkinter
from tkinter import filedialog
from PIL import Image
import piexif
import argparse

def main():
	args = parse_program_arguments()
	if args.gui:
		gui_scorpion(args.files)
	if len(args.files) != 0:
		metada = get_metadata(args.files)
		for key, value in metada.items():
			print(f"{key}: {value}")
	sys.exit(0)

def get_metadata(files):
	metadata_list = []
	for file in files:
		img = Image.open(file)

		metadata = {}

	# infos fichier
	metadata["Filename"] = os.path.basename(file)
	metadata["Filesize"] = os.path.getsize(file)
	metadata["Filetype"] = img.format
	metadata["ImageSize"] = f"{img.width}x{img.height}"
	metadata["Mode"] = img.mode

	# EXIF standard via piexif
	raw = img.info.get("exif", b"")
	if raw:
		exif = piexif.load(raw)
		for ifd in ["0th", "Exif", "GPS"]:
			for tag, val in exif.get(ifd, {}).items():
				name = piexif.TAGS[ifd][tag]["name"]
				if isinstance(val, bytes):
					try:    val = val.decode("utf-8").strip("\x00")
					except: val = val.hex()
				metadata[name] = val
	return metadata


def parse_program_arguments():
	parser = argparse.ArgumentParser()
	parser.add_argument("files", nargs='*', help="./scorpion FILE1 [FILE2 ...]")
	parser.add_argument("-g", "--gui", action="store_true", help="display the metadata in a GUI window instead of the console.")
	args = parser.parse_args()
	return args

def gui_scorpion(files):
	app = customtkinter.CTk()
	customtkinter.set_appearance_mode("system")  # default
	app.title("Scorpion GUI")
	app.geometry("1600x700")
	signal.signal(signal.SIGINT, lambda sig, frame: app.destroy())

	# left panel
	left_frame = customtkinter.CTkFrame(app, width=300, fg_color="gray20")
	left_frame.pack(side="left", fill="y")

	# right panel
	right_frame = customtkinter.CTkFrame(app, width=400, fg_color="gray20")
	right_frame.pack(side="right", fill="y")
	right_frame.pack_propagate(False)

	preview_label = customtkinter.CTkLabel(right_frame, text="Photo sélectionnée", fg_color="gray30", corner_radius=12)
	preview_label.pack(fill="both", expand=True, padx=10, pady=10)

	# scrollable frame in left panel
	scrollable_frame = customtkinter.CTkScrollableFrame(left_frame)
	scrollable_frame.pack(fill="both", expand=True)

	# nested functions
	def add_thumbnail(file):
		try:
			img = Image.open(file)
			img.thumbnail((150, 150))
			ctk_img = customtkinter.CTkImage(light_image=img, size=(img.width, img.height))
			label = customtkinter.CTkLabel(
				scrollable_frame, 
				text=os.path.basename(file), 
				image=ctk_img,
				compound="top",
				wraplength=260)
			label.image = ctk_img
			label.pack(pady=5, fill="x")
			app.update()
		except:
			pass

	def add_files():
		selected = filedialog.askopenfilenames(
			filetypes=[("Images", "*.jpg *.jpeg *.png *.tiff")]
		)
		for file in selected:
			add_thumbnail(file)

	def add_folder():
		folder = filedialog.askdirectory()
		if not folder:
			return
		for root, dirs, filenames in os.walk(folder):
			for filename in filenames:
					add_thumbnail(os.path.join(root, filename))

	# add buttons and link with nested functions
	uploadfiles_button = customtkinter.CTkButton(left_frame, text="Upload Files", command=add_files)
	uploadfiles_button.pack(pady=5)
	uploadfolders_button = customtkinter.CTkButton(left_frame, text="Upload Folder", command=add_folder)
	uploadfolders_button.pack(pady=5)

	for file in files:
		add_thumbnail(file)

	app.mainloop()

if __name__ == "__main__":
	main()