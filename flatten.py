import json
from pymongo import MongoClient

# połączenie z MongoDB
client = MongoClient("mongodb://localhost:27017/")
db = client["kpop_db"]
source_collection = db["kpop_billboard_2020_2026"]
target_collection = db["kpop_billboard_flattened"]

flattened_documents = []

for doc in source_collection.find():
  date = doc.get("date")
  raw_ranklist = doc.get("ranklist")

  if not raw_ranklist:
    continue

  if isinstance(raw_ranklist, str):
    try:
      items = json.loads(raw_ranklist)
    except json.JSONDecodeError:
      continue
  else:
    items = raw_ranklist

  # rozbijamy każdy element listy
  for entry in items:
    if len(entry) >= 5:
      new_doc = {
          "date": date,
          "artist_name": entry[1],
          "song": entry[2],
          "rank": int(entry[3]),
      }
      flattened_documents.append(new_doc)

# spłaszczone dane do nowej kolekcji
if flattened_documents:
  target_collection.insert_many(flattened_documents)
  print(f"Sukces! Spłaszczono i zapisano {len(flattened_documents)} rekordów.")
