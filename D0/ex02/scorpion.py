import sys
import os
import signal
import threading
import customtkinter
from tkinter import filedialog
from PIL import Image
import piexif
from iptcinfo3 import IPTCInfo
import argparse
from datetime import datetime

def main():
	args = parse_program_arguments()
	if args.gui: # BONUS DAY
		gui_scorpion(args.files)
	if len(args.files) != 0 and not args.gui:
		metadata = get_metadata(args.files)
		display_metadata_list(metadata)
	sys.exit(0)

def get_metadata(files):
	metadata_list = []
	for file in files:
		try:
			img = Image.open(file)
		except Exception as e:
			print(f"Error opening {file}: {e}")
			continue
		metadata	= {}

		# infos fichier
		metadata["Filename"] = (os.path.basename(file), "os")
		metadata["Filesize"] = (os.path.getsize(file), "os")
		metadata["Filetype"] = (img.format, "os")
		metadata["Modified"] = (datetime.fromtimestamp(os.path.getmtime(file)).strftime("%Y:%m:%d %H:%M:%S"), "os")
		metadata["Imagesize"] = (f"{img.width}x{img.height}", "os")
		metadata["Mode"] = (img.mode, "os")

		# EXIF standard via piexif
		raw = img.info.get("exif", b"")
		if raw:
			exif = piexif.load(raw)
			for ifd in ["0th", "Exif", "GPS", "1st, Interop"]:
				for tag, val in exif.get(ifd, {}).items():
					name = piexif.TAGS[ifd][tag]["name"]
					if isinstance(val, bytes):
						try:    val = val.decode("utf-8").strip("\x00")
						except: val = val.hex()
					metadata[name] = (val, ifd, tag)
	
		# IPCT INfo
		try:
			iptc = IPTCInfo(file)
			if iptc:
				for key, value in iptc.data.items():
					if value:
						metadata[f"{key}"] = (value, "IPTC")
		except: pass

		metadata_list.append(metadata)
	return metadata_list

def display_metadata_list(list):
	for i, metadata in enumerate(list):
		print("=========================\n"
			f"Images {i} \n"
			"=========================")
		for key, value in metadata.items():
			print(f"{key}: {value}")
		i = i + 1


# BONUS DAYS
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
	current_file= [None]
	signal.signal(signal.SIGINT, lambda sig, frame: app.destroy())
	entries = {}


	# left panel
	left_frame = customtkinter.CTkFrame(app, width=300)
	left_frame.pack(side="left", fill="y")

	# right panel
	right_frame = customtkinter.CTkFrame(app, width=400)
	right_frame.pack(side="right", fill="y")
	right_frame.pack_propagate(False)

	preview_label = customtkinter.CTkLabel(right_frame, text="Photo sélectionnée", corner_radius=12)
	preview_label.pack(fill="both", expand=True, padx=10, pady=10)

	# middle panel
	middle_frame = customtkinter.CTkFrame(app)
	middle_frame.pack(side="left", fill="both", expand=True)
	meta_scroll = customtkinter.CTkScrollableFrame(middle_frame)
	meta_scroll.pack(fill="both", expand=True, padx=5, pady=5)
	meta_scroll.grid_columnconfigure(1, weight=1)

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
				wraplength=260,
				cursor="hand2")
			label.image = ctk_img
			label.bind("<Button-1>", lambda event: show_image_and_metadata(file))
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

	def show_toast(message, color="#2ecc71", duration=2500):
		toast = customtkinter.CTkFrame(app, corner_radius=10, fg_color=color)
		toast_label = customtkinter.CTkLabel(toast, text=message, text_color="white")
		toast_label.pack(padx=12, pady=8)
		toast.place(relx=1.0, rely=0.0, anchor="ne", x=-10, y=10)
		app.after(duration, toast.place_forget)

	def add_folder():
		folder = filedialog.askdirectory()
		if not folder:
			return
		for root, dirs, filenames in os.walk(folder):
			for filename in filenames:
					add_thumbnail(os.path.join(root, filename))

	def show_image_and_metadata(file_path, force=False):
		try:
			if file_path == current_file[0] and not force:
				return
			current_file[0] = file_path

			# preview
			img = Image.open(file_path)
			img.thumbnail((400, 600))
			display_img = customtkinter.CTkImage(light_image=img, size=(img.width, img.height))
			preview_label.configure(image=display_img, text="")
			preview_label.image = display_img

			# clean metadata
			for widget in meta_scroll.winfo_children():
				widget.destroy()
			entries.clear()
			
			# display metadata
			metadata = get_metadata([file_path])[0]
			for i, (key, val) in enumerate(metadata.items()):
				customtkinter.CTkLabel(meta_scroll, text=str(key), anchor="w").grid(row=i, column=0, padx=(5,2), pady=2, sticky="w")
				entry = customtkinter.CTkEntry(meta_scroll)
				entry.insert(0, str(val[0]))
				if (key in ["Filename", "Filetype", "Filesize", "Imagesize", "Mode"]):
					entry.configure(state="readonly",fg_color="#8e8a8a")
					entry.grid(row=i, column=1, padx=2, pady=2, sticky="ew")
					entries[key] = (entry, str(val[0]), str(val[1]), val[2] if len(val) > 2 else None)
					continue
				else:
					entry.grid(row=i, column=1, padx=2, pady=2, sticky="ew")
					entries[key] = (entry, str(val[0]), str(val[1]), val[2] if len(val) > 2 else None)
		except Exception as e:
			preview_label.configure(text=f"Erreur: {e}", image=None)
	
	def apply_all():
		def update_metadata_os(entry, key):
			if key == "Modified":
				try:
					if entry.get() == "":
						os.utime(current_file[0], None)
					else:
						ts = datetime.strptime(entry.get(), "%Y:%m:%d %H:%M:%S").timestamp()
						os.utime(current_file[0], (ts, ts))
					show_toast("Update successfully")
				except ValueError:
					show_toast("Update denied", color="#e74c3c")
			else:
				pass

		def update_metadata_exif(entry, key, ifd, tag):
			try:
				img = Image.open(current_file[0])
				raw = img.info.get("exif", b"")
				exif = piexif.load(raw) if raw else {"0th": {}, "Exif": {}, "GPS": {}, "1st": {}, "Interop": {}}
				
				ifd_key = ifd if ifd in exif else None
				if ifd_key is None:
					show_toast("Update denied", color="#e74c3c")
					return
				
				if entry.get() != "":
					# Modifier le tag
					tag_info = piexif.TAGS.get(ifd_key, {}).get(tag, {})
					tag_type = tag_info.get("type", 3)
					new_str = entry.get()
					if tag_type in (1, 3, 4):
						value = int(new_str)
					elif tag_type == 2:
						value = new_str.encode("utf-8") + b"\x00"
					elif tag_type == 5:
						parts = new_str.split("/")
						value = (int(parts[0]), int(parts[1])) if len(parts) == 2 else (int(new_str), 1)
					else:
						value = new_str.encode("utf-8")
					exif[ifd_key][tag] = value
				else:
					# Supprimer le tag si le champ est vide
					if tag in exif[ifd_key]:
						del exif[ifd_key][tag]
				
				exif_bytes = piexif.dump(exif)
				img.save(current_file[0], exif=exif_bytes)
				show_toast("Update successfully")
			except Exception as e:
				show_toast("Update denied", color="#e74c3c")
		
		def update_metadata_iptc(entry, key):
			try:
				info = IPTCInfo(current_file[0])
				info[key] = entry.get()
				if entry.get() == "":
					del info[key]
				else:
					info[key] = entry.get()
				info.save()
				show_toast("Update successfully")
			except Exception as e:
				show_toast("Update denied", color="#e74c3c")

		modified = False
		if not current_file[0]:
			return
		for key, (entry, old_val, source, tag) in entries.items():
			new_val = entry.get()
			if new_val != old_val:
				modified = True
				if source == "os":
					update_metadata_os(entry, key)
				elif source in ["0th", "Exif", "GPS", "1st", "Interop"]:
					update_metadata_exif(entry, key, source, tag)
				elif source == "IPTC":
					update_metadata_iptc(entry, key, entry[2])
				else:
					print(f"Unknown metadata source for {key}: {source}")
		if modified:
			show_image_and_metadata(current_file[0], force=True)
	
	# add buttons and link with nested functions
	uploadfiles_button = customtkinter.CTkButton(left_frame, text="Upload Files", command=add_files)
	uploadfiles_button.pack(pady=5)
	uploadfolders_button = customtkinter.CTkButton(left_frame, text="Upload Folder", command=add_folder)
	uploadfolders_button.pack(pady=5)
	apply_button = customtkinter.CTkButton(middle_frame, text="Apply", command=apply_all)
	apply_button.pack(pady=5)

	for file in files:
		add_thumbnail(file)

	app.mainloop()

if __name__ == "__main__":
	main()