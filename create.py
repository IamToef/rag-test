from utils.indexing import DataManager

def main():
    folder_path = r"C:\A\baihoc\Intern\RAG\rag-test\data"

    print("🚀 Running smart reload...")
    dm = DataManager("my_collection")
    dm.smart_reload(folder_path=folder_path)
    print("✅ Vector store created/updated successfully!")

if __name__ == "__main__":
    main()
