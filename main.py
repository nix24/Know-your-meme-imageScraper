from bs4 import BeautifulSoup
import os
import requests
import re
from numba import jit
from multiprocessing import Pool

folder = ""


class ImageObject:
    def __init__(self, id, title, url):
        self.id = id
        self.title = title
        self.url = url


def sanitize_filename(filename: str) -> str:
    # Split the filename into name and extension
    name, ext = os.path.splitext(filename)

    name = name.replace(" ", "_")
    name = re.sub(
        r"[^a-zA-Z0-9_.-]", "", name
    )  # Remove all non-alphanumeric characters except spaces, hyphens, and periods
    name = re.sub(
        r"_{2,}", "_", name
    )  # Replace multiple underscores with a single underscore

    # Construct the sanitized filename with the original extension
    sanitized_filename = name + ext

    return sanitized_filename


def extract_image_urls(topic: str, number_pages: int, page_start: int) -> None:
    folder = f"topics/{topic}"
    url_base = f"https://knowyourmeme.com/memes/{topic}/photos/sort/score"
    os.makedirs(folder, exist_ok=True)

    image_urls = []

    for i in range(1, number_pages + 1):
        print(f"Searching page {i} of {number_pages}...")

        url = f"{url_base}/page/{page_start + i - 1}"
        print(f"Searching page #{page_start + i - 1}...")
        res = requests.get(url)
        soup = BeautifulSoup(res.text, "html.parser")

        image_links = soup.find_all("a", class_="photo")
        for j, link in enumerate(image_links):
            # FOR TESTING PURPOSES
            # if len(image_urls) > 0:
            #     break
            if "href" in link.attrs:
                image_slug = link["href"].split("/")[-1]
                image_slug_url = f"https://knowyourmeme.com/photos/{image_slug}"
                image_page_res = requests.get(image_slug_url)
                image_soup = BeautifulSoup(image_page_res.text, "html.parser")

                # make the titleElement = to the title of the head in the html
                title_element = image_soup.find("title")
                if title_element:
                    title = title_element.text.strip()
                    title = title.split(" - ")[0]
                    title = (
                        title.replace(":", "")
                        .replace("?", "")
                        .replace("/", "_")
                        .replace("\\", "_")
                        .replace(" | ", "_")
                    )
                    # clean text to make sure UnicodeEncodeError doesn't occur
                    title = title.encode("ascii", "ignore").decode("ascii")
                    print(f"Title: {title}")
                else:
                    title = f"image_{i}_{j}"

                image_element = image_soup.find("img", class_="centered_photo")
                if image_element and "src" in image_element.attrs:
                    image_url = image_element["src"]
                    image_obj = ImageObject(f"{i}_{j}", title, image_url)
                    if image_obj.url not in [obj.url for obj in image_urls]:
                        image_urls.append(image_obj)
                        print(f"Found image {i}_{j}")
                    else:
                        print(f"skipping dup image {i}_{j}")
                else:
                    print(f"Skipping image {i}_{j} due to missing src attribute")
            else:
                print(f"Skipping image {i}_{j} due to missing href attribute")

    with open(f"{folder}/image_urls.txt", "w") as file:
        for image_obj in image_urls:
            file.write(f"{image_obj.id}|{image_obj.title}|{image_obj.url}\n")

    print(f"Image URLs saved to {folder}/image_urls.txt")


# Example usage
topic = input("Enter the topic: ")
num_pages = int(input("Enter the number of pages to search through: "))
page_start = int(input("Enter the page to start from: "))
extract_image_urls(topic, num_pages, page_start)

# images successfully in .txt file
# download images
image_urls_file = f"topics/{topic}/image_urls.txt"

with open(image_urls_file, "r") as file:
    image_objs = []
    for line in file:
        id, title, url = line.strip().split("|")
        image_objs.append(ImageObject(id, title, url))

# Create the directory to store the downloaded images
images_directory = f"topics/{topic}/images"
os.makedirs(images_directory, exist_ok=True)

# Download each image
for image_obj in image_objs:
    response = requests.get(image_obj.url)
    if response.status_code == 200:
        file_extension = os.path.splitext(image_obj.url)[-1]
        if not file_extension:
            file_extension = ".jpg"  # Set default file extension to ".jpg"
        file_title = image_obj.title.replace(" ", "-")
        file_name = f"{file_title}{file_extension}"
        sanitized_file_name = sanitize_filename(file_name)
        file_path = os.path.join(images_directory, sanitized_file_name)
        with open(file_path, "wb") as file:
            file.write(response.content)
        print(f"Downloaded image {image_obj.id}: {sanitized_file_name}")
    else:
        print(f"Failed to download image {image_obj.id}: {image_obj.url}")
