import os

def count_sol_files(root_directory):
    total_count = 0
    folder_counts = {}

    for root, dirs, files in os.walk(root_directory):
        sol_files = [file for file in files if file.endswith(".sol")]

        if sol_files:
            folder_counts[root] = len(sol_files)
            total_count += len(sol_files)

    return total_count, folder_counts


if __name__ == "__main__":
    dataset_path = r"Ethereum_smart_contract_dataset"

    total, per_folder = count_sol_files(dataset_path)

    print("\n📊 Solidity File Count Report\n")

    for folder, count in per_folder.items():
        print(f"{folder} → {count} .sol files")

    print("\n===============================")
    print(f"Total .sol files in dataset: {total}")