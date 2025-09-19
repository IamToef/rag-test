from utils.load_data import DataManager

def main():
    folder_path = r"c:\A\baihoc\Intern\code\data"

    print("🚀 Running smart reload...")
    dm = DataManager("my_collection")
    dm.smart_reload(folder_path=folder_path)

if __name__ == "__main__":
    main()
