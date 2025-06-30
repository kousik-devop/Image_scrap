from flask import Flask, render_template, request, redirect
import os, base64, requests
from bs4 import BeautifulSoup
import pymongo
from bson.binary import Binary

app = Flask(__name__)
SAVE_DIR = "static/images/"

if not os.path.exists(SAVE_DIR):
    os.makedirs(SAVE_DIR)

client = pymongo.MongoClient("mongodb+srv://kousikmaiti19:kousik2005@cluster0.f6enwx1.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
db = client["image_scrapper"]
collection = db["images"]

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        query = request.form["query"]
        return redirect(f"/results/{query}")
    return render_template("index.html")

@app.route("/results/<query>")
def results(query):
    # Clear old files and DB
    for file in os.listdir(SAVE_DIR):
        if file.lower().endswith((".jpg", ".jpeg", ".png", ".webp")):
            os.remove(os.path.join(SAVE_DIR, file))
    collection.delete_many({})

    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(f"https://www.google.com/search?q={query}&tbm=isch", headers=headers)
    soup = BeautifulSoup(response.content, 'html.parser')
    images = soup.find_all("img")

    saved_images = []
    for idx, img_tag in enumerate(images):
        src = img_tag.get("src")
        if not src:
            continue
        try:
            if src.startswith("data:image"):
                header, encoded = src.split(",", 1)
                img_data = base64.b64decode(encoded)
                ext = header.split(";")[0].split("/")[1]
            elif src.startswith("http"):
                img_data = requests.get(src, headers=headers).content
                ext = src.split(".")[-1].split("?")[0].lower()
                ext = ext if ext in ["jpg", "jpeg", "png", "webp"] else "jpg"
            else:
                continue

            if len(img_data) < 1000:
                continue

            filename = f"{query}_{idx}.{ext}"
            filepath = os.path.join(SAVE_DIR, filename)

            with open(filepath, "wb") as f:
                f.write(img_data)

            collection.insert_one({"index": src, "image": Binary(img_data), "filename": filename})
            saved_images.append(filename)
        except Exception as e:
            print("Error:", e)
            continue

    return render_template("results.html", images=saved_images, query=query)


if __name__ == "__main__":
    print("Starting Flask app...")
    app.run(debug=True)

