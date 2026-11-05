from pymongo import MongoClient

# połączenie z MongoDB
client = MongoClient("mongodb://localhost:27017/")
db = client["kpop_db"]

collections = db.list_collection_names()

print("rozpoczynam usuwanie pola artist_id: 6206 ze wszystkich kolekcji:(((\n")

# iteracja po każdej kolekcji
for col_name in collections:
  collection = db[col_name]

  query = {"$or": [{"artist_id": 6206}, {"artist_id": "6206"}]}

  # operacja $unset usuwa wskazane pole z dokumentu
  update_result = collection.update_many(query, {"$unset": {"artist_id": ""}})

  if update_result.modified_count > 0:
    print(
        f"Kolekcja '{col_name}': usunięto pole z"
        f" {update_result.modified_count} dokumentów."
    )

result_plan_b = db["kpop_spotify_monthly_listeners_clean"].delete_many(
    {"group_name": "PLAN B"}
)
if result_plan_b.deleted_count > 0:
  print(
      f"Kolekcja 'kpop_spotify_monthly_listeners_clean': usunięto"
      f" {result_plan_b.deleted_count} dokumentów zespołu PLAN B."
  )

print("\n[SUCCESS] operacja została zakończona pomyślnie :))")
