from pymongo import MongoClient, UpdateOne
import pandas as pd
import time
import re

mongo_uri = "mongodb://localhost:27017/"
db_name = "kpop_db"

def clean_circle_artist(artist_str):
    s = str(artist_str).strip()
    match = re.search(r'^(.*?)\s*\((.*?)\)$', s)
    if match:
        part1 = match.group(1).strip()
        part2 = match.group(2).strip()
        hangul = re.compile(r'[\uac00-\ud7a3]')
        p1_has_hangul = bool(hangul.search(part1))
        p2_has_hangul = bool(hangul.search(part2))
        
        if p2_has_hangul and not p1_has_hangul:
            return part1
        elif p1_has_hangul and not p2_has_hangul:
            return part2
            
    return s

def link_all_collections():
    client = MongoClient(mongo_uri)
    db = client[db_name]

    collections_mapping = {
        "kpop_spotify_monthly_listeners_clean": "group_name",
        "kpop_mainstream_lvl": "name",
        "kpop_artists_success": "group_name",
        "kpop_idols_data_cleaned": "Group",
        "circlechart_streaming_2022_2026": "ARTIST_NAME",
        "circlechart_digital_2022_2026": "ARTIST_NAME",
        "circlechart_album_2022_2026": "ARTIST_NAME",
        "circlechart_global_kpop_2022_2026": "Artist",
        "kpop_billboard_2020_2026": "artist_name",
        "kpop_music_show_awards_2006_2026": "artist"
    }

    print("wczytywanie słownika do pamięci :))")
    master_docs = db["artists_master"].find({}, {"artist_id": 1, "artist_normalized": 1})
    artist_to_id = {doc["artist_normalized"]: doc["artist_id"] for doc in master_docs}
    print(f"załadowano słownik: {len(artist_to_id)} artystów.")

    print("\naktualizowanie kolekcji paczkami ^^")
    
    for col_name, col_field in collections_mapping.items():
        if col_name not in db.list_collection_names():
            print(f"kolekcja {col_name} nie istnieje, pomijam.")
            continue
            
        collection = db[col_name]
        cursor = collection.find({}, {col_field: 1})
        
        bulk_operations = []
        updated_count = 0
        
        for doc in cursor:
            val = doc.get(col_field)
            if val and pd.notna(val):
                if col_name == "circlechart_global_kpop_2022_2026":
                    cleaned_val = clean_circle_artist(val)
                else:
                    cleaned_val = str(val).strip()
                    
                normalized_name = cleaned_val.lower()
                matched_id = artist_to_id.get(normalized_name)
                
                if matched_id:
                    bulk_operations.append(
                        UpdateOne(
                            {"_id": doc["_id"]},
                            {"$set": {"artist_id": matched_id}}
                        )
                    )
            
            if len(bulk_operations) >= 5000:
                collection.bulk_write(bulk_operations)
                updated_count += len(bulk_operations)
                bulk_operations = []
        
        if bulk_operations:
            collection.bulk_write(bulk_operations)
            updated_count += len(bulk_operations)
            
        print(f"zaktualizowano kolekcję {col_name}: {updated_count} dokumentów")
        time.sleep(0.5)

    print("\nwszystkie kolekcje zostały powiązane!")

if __name__ == "__main__":
    link_all_collections()