import os # https://docs.python.org/3/library/os.html
import sys # https://docs.python.org/3/library/sys.html
import argparse # https://docs.python.org/3/library/argparse.html
import threading # https://docs.python.org/3/library/threading.html
from concurrent.futures import ThreadPoolExecutor, as_completed # https://docs.python.org/3/library/concurrent.futures.html#concurrent.futures.ThreadPoolExecutor
import requests # https://pypi.org/project/requests/
from urllib.parse import urljoin, urlparse # https://docs.python.org/3/library/urllib.parse.html#urllib.parse.urljoin
from bs4 import BeautifulSoup # https://pypi.org/project/beautifulsoup4/ 
from tqdm import tqdm # https://pypi.org/project/tqdm/

EXTENSIONS = (".jpg", ".jpeg", ".png", ".gif", ".bmp")

def main():
	urls = set()
	visited = set()
	args = parse_program_arguments()

	try:
		if args.recursive:
			lock = threading.Lock()
			crawl(args.url, 0, args.l, visited, urls, lock)
		else:
			extract_images(get_html(args.url), args.url, urls)
	except KeyboardInterrupt:
		print("\nInterrupted.")
		sys.exit(0)
	download_images(urls, args.p)

def parse_program_arguments():
	parser = argparse.ArgumentParser()
	parser.add_argument("url", help="The URL of the webpage to crawl")
	parser.add_argument("-r", "--recursive", action="store_true", help="recursively downloads the images in a URL received as a parameter.")
	parser.add_argument("-l", type=int, default=5, nargs='?', const=5, metavar="--level", help="indicates the maximum depth level of the recursive download.If not indicated, it will be 5.")
	parser.add_argument("-p", type=str, default="./data/", metavar="--path", help="indicates the path where the downloaded files will be saved.If not specified, ./data/ will be used.")
	args = parser.parse_args()

	if (args.l < 0):
		print("Error: Level must be a non-negative integer.")
		sys.exit(1)

	if not os.path.exists(args.p):
		try:
			os.makedirs(args.p)
		except OSError as e:
			print(f"Error: {e}")
			sys.exit(1)

	return args

def get_html(url):
	try:
		response = requests.get(url, timeout=10)
		return response.text
	except requests.exceptions.RequestException as e:
		print(f"Error: {e}")
		return None

def extract_links(html, base_url):
	base_domain = urlparse(base_url).netloc
	soup = BeautifulSoup(html, 'html.parser')
	links = set()

	for a in soup.find_all("a", href=True):
		link = urljoin(base_url, a["href"])
		if link.startswith("http") and urlparse(link).netloc == base_domain:
			links.add(link)

	return links

def extract_images(html, base_url, urls):
	soup = BeautifulSoup(html, 'html.parser')
	imgs = soup.find_all('img')

	for img in imgs:
		src = img.get("src")
		if src:
			src = urljoin(base_url, src)
			if src.lower().endswith(EXTENSIONS):
				urls.add(src)
	return urls

#"Crawl" vient du terme web crawling (ou web crawler), qui désigne le processus de parcourir automatiquement \
#  des pages web en suivant les liens.
def crawl(url, depth, max_depth, visited, urls, lock):
	with lock:
		if depth > max_depth or url in visited:
			return
		visited.add(url)

	print(f"Crawling: {url} (depth: {depth}) (max_depth: {max_depth})")
	html = get_html(url)
	if html is None:
		return

	with lock:
		extract_images(html, url, urls)

	links = extract_links(html, url)
	with ThreadPoolExecutor(max_workers=5) as executor:
		futures = [executor.submit(crawl, link, depth + 1, max_depth, visited, urls, lock) for link in links]
		for future in as_completed(futures):
			future.result()

def download_images(urls, path):
	if not urls:
		print("No images found.")
		sys.exit(0)
	print(f"Downloading {len(urls)} image(s) to '{path}'...")

	def download_one(url):
		try:
			filename = os.path.basename(urlparse(url).path)
			if not filename:
				return
			dest = os.path.join(path, filename)
			response = requests.get(url, timeout=10)
			response.raise_for_status()
			with open(dest, "wb") as f:
				f.write(response.content)
		except:
			pass
			
	with ThreadPoolExecutor(max_workers=10) as executor:
		futures = [executor.submit(download_one, url) for url in urls]
		with tqdm(
			total=len(urls),
			colour="green",
			dynamic_ncols=True,
			ascii="░▒█",
			desc="Downloading",
			unit="img") as pbar:
				for future in as_completed(futures):
					future.result()
					pbar.update(1)

if __name__ == "__main__":
	main()
