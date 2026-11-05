import pandas as pd
from pymongo import MongoClient

MONGO_URI = "mongodb://localhost:27017/"
DB_NAME = "kpop_db"
COLLECTION_NAME = "kpop_spotify_monthly_listeners" 

def fix_and_clean_data_with_report():
    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]
    collection = db[COLLECTION_NAME]

    print(f"pobieranie danych z kolekcji '{COLLECTION_NAME}' do czyszczenia ^^")
    data = list(collection.find())
    
    if not data:
        print("kolekcja jest pusta!")
        return

    df = pd.DataFrame(data)

    if '_id' in df.columns:
        df = df.drop(columns=['_id'])

    print(f"\npoczątkowa liczba wierszy = {len(df)}")

    # usuwanie zduplikowanych kolumn
    df.columns = df.columns.str.strip().str.replace('\ufeff', '')
    df = df.loc[:, ~df.columns.duplicated()]

    print("\nprzed czyszczeniem")
    print("typy kolumn:\n", df.dtypes.to_dict())
    print("liczba braków danych (NaN) w kolumnach = ", df.isnull().sum())

    # wykrywanie duplikatów
    duplicates_count = df.duplicated().sum()
    print(f"\nliczba wykrytych duplikatów do usunięcia = {duplicates_count}")

    # czyszczenie
    df = df.drop_duplicates()
    df = df.dropna(how='all')

    print(f"\npo czyszczeniu")
    print(f"liczba wierszy po usunięciu duplikatów i pustych = {len(df)}")

    # zapis do nowej kolekcji
    cleaned_collection_name = f"{COLLECTION_NAME}_clean"
    db[cleaned_collection_name].delete_many({})
    
    records = df.to_dict(orient="records")
    if records:
        db[cleaned_collection_name].insert_many(records)
        print(f"\n[SUCCESS] zapisano {len(records)} wyczyszczonych danych do kolekcji o nazwie '{cleaned_collection_name}'")

if __name__ == "__main__":
    fix_and_clean_data_with_report()