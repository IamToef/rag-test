from utils.load_data import DataManager

def main():
    folder_path = r"C:\A\baihoc\Intern\RAG\data"

    print("🚀 Running smart reload...")
    dm = DataManager("my_collection")
    dm.smart_reload(folder_path=folder_path)

if __name__ == "__main__":
    main()
