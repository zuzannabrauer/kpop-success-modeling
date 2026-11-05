import io
import os
import requests
import pandas as pd
from pymongo import MongoClient

# konfiguracja
MONGO_URI = "mongodb://localhost:27017/"
DB_NAME = "kpop_db"

# repozytorium
OWNER = "zuzannabrauer"
REPO = "kpop-success-modeling"
BRANCH = "main"

def get_github_contents(path=""):
    """pobiera listę plików i folderów z publicznego API githuba"""
    api_url = f"https://api.github.com/repos/{OWNER}/{REPO}/contents/{path}?ref={BRANCH}"
    
    response = requests.get(api_url)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"[ERROR] błąd API dla ścieżki '{path}': {response.status_code}")
        return []

def import_csv_from_github(path=""):
    """rekurencyjnie przeszukuje repozytorium i importuje pliki .csv do MongoDB"""
    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]
    
    items = get_github_contents(path)
    
    for item in items:
        # jeśli to plik CSV
        if item["type"] == "file" and item["name"].endswith(".csv"):
            file_url = item["download_url"]
            collection_name = os.path.splitext(item["name"])[0]
            
            print(f"pobieranie i importowanie pliku o nazwie {item['path']} do kolekcji '{collection_name}'...")
            
            file_response = requests.get(file_url)
            
            if file_response.status_code == 200:
                try:
                    # wczytanie CSV bezpośrednio z pamięci
                    df = pd.read_csv(
                        io.StringIO(file_response.text),
                        sep=None,
                        engine='python',
                        on_bad_lines='skip'
                    )
                    
                    if df.empty:
                        print(f"[INFO] plik {item['name']} jest pusty, pomijam.")
                        continue
                        
                    records = df.to_dict(orient="records")
                    collection = db[collection_name]
                    
                    # wstawienie do MongoDB
                    result = collection.insert_many(records)
                    print(f"[SUCCESS] zaimportowano {len(result.inserted_ids)} wierszy danych.")
                    
                except Exception as e:
                    print(f"[ERROR] błąd przetwarzania pliku {item['name']} o treści: {e}")
            else:
                print(f"[ERROR] nie udało się pobrać pliku, kod: {file_response.status_code}")
                
        # jeśli to folder, wejdź w niego rekurencyjnie
        elif item["type"] == "dir":
            import_csv_from_github(item["path"])

if __name__ == "__main__":
    print("rozpoczynam pobieranie danych bezpośrednio z repozytorium do MongoDB :))")
    import_csv_from_github()
    print("zakończono import!!!!")