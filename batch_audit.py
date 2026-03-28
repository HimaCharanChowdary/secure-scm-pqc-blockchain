import os
import subprocess
import json
import tempfile
import time
from blockchain_store import store_contract

DATASET_PATH = r"sample_dataset"


# PROGRESS BAR
def print_progress(current, total, start_time, approved, rejected, bar_length=38):
    percent = current / total
    filled = int(bar_length * percent)
    bar = "█" * filled + "░" * (bar_length - filled)

    elapsed = time.time() - start_time
    if current > 0:
        eta = (elapsed / current) * (total - current)
        mins, secs = divmod(int(eta), 60)
        eta_str = f"{mins}m {secs}s left"
    else:
        eta_str = "calculating..."

    print(
        f"\r  [{bar}] {current}/{total} ({percent*100:.1f}%)"
        f"  ✅ {approved}  ❌ {rejected}  ⏳ {eta_str}",
        end="",
        flush=True
    )


# FILTER SIMPLE CONTRACTS
def is_simple_contract(contract_path):
    try:
        with open(contract_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()

        if "import" in content:
            return False

        if "pragma solidity" not in content:
            return False

        return True
    except:
        return False


# GENERATE AST (0.4.x compatible)
def generate_ast(contract_path):
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".json") as tmp_file:
            ast_path = tmp_file.name

        with open(ast_path, "w") as out_file:
            subprocess.run(
                ["solc", "--combined-json", "ast", contract_path],
                stdout=out_file,
                stderr=subprocess.DEVNULL,
                check=True
            )

        with open(ast_path, "r") as f:
            data = json.load(f)

        os.remove(ast_path)
        return data
    except:
        return None



# RECURSIVE FIND (0.4.x AST)
def recursive_find(node, target_name):
    found = []

    if isinstance(node, dict):
        if node.get("name") == target_name:
            found.append(node)

        for value in node.values():
            found.extend(recursive_find(value, target_name))

    elif isinstance(node, list):
        for item in node:
            found.extend(recursive_find(item, target_name))

    return found


# ORDER-SENSITIVE REENTRANCY DETECTION
def detect_reentrancy(ast_data):
    issues = []

    for source in ast_data.get("sources", {}).values():
        ast_root = source.get("AST", {})

        contracts = recursive_find(ast_root, "ContractDefinition")

        for contract in contracts:
            functions = recursive_find(contract, "FunctionDefinition")

            # Collect state variable names
            state_vars = []
            var_decls = recursive_find(contract, "VariableDeclaration")
            for var in var_decls:
                if var.get("attributes", {}).get("stateVariable"):
                    name = var.get("attributes", {}).get("name")
                    if name:
                        state_vars.append(name)

            for func in functions:
                blocks = recursive_find(func, "Block")
                if not blocks:
                    continue

                block = blocks[0]
                statements = block.get("children", [])

                external_call_index = -1

                # STEP 1: detect external call properly
                for i, stmt in enumerate(statements):
                    member_accesses = recursive_find(stmt, "MemberAccess")

                    for ma in member_accesses:
                        member = ma.get("attributes", {}).get("member_name")

                        if member in ["call", "send", "transfer"]:
                            external_call_index = i
                            break

                    if external_call_index != -1:
                        break

                # STEP 2: detect state update AFTER call
                if external_call_index != -1:
                    for stmt in statements[external_call_index + 1:]:
                        assignments = recursive_find(stmt, "Assignment")

                        for assign in assignments:
                            identifiers = recursive_find(assign, "Identifier")
                            for ident in identifiers:
                                if ident.get("attributes", {}).get("value") in state_vars:
                                    issues.append("reentrancy")
                                    break

                            if "reentrancy" in issues:
                                break

                        if "reentrancy" in issues:
                            break

    return issues


# PRECISION ACCESS CONTROL DETECTION
def detect_access_control(ast_data):
    issues = []

    sensitive_names = ["owner", "admin", "controller"]

    for source in ast_data.get("sources", {}).values():
        ast_root = source.get("AST", {})

        contracts = recursive_find(ast_root, "ContractDefinition")

        for contract in contracts:
            functions = recursive_find(contract, "FunctionDefinition")

            for func in functions:

                # Skip constructor
                if func.get("attributes", {}).get("isConstructor"):
                    continue

                visibility = func.get("attributes", {}).get("visibility")

                if visibility not in ["public", "external"]:
                    continue

                modifies_sensitive = False
                assignments = recursive_find(func, "Assignment")

                for assign in assignments:
                    identifiers = recursive_find(assign, "Identifier")
                    for ident in identifiers:
                        if ident.get("attributes", {}).get("value") in sensitive_names:
                            modifies_sensitive = True

                if not modifies_sensitive:
                    continue

                has_require = False
                identifiers = recursive_find(func, "Identifier")

                for ident in identifiers:
                    if ident.get("attributes", {}).get("value") == "require":
                        has_require = True
                        break

                if not has_require:
                    issues.append("access_control")

    return issues


# MAIN AUDIT
def main():
    sol_files = []

    for root, dirs, files in os.walk(DATASET_PATH):
        for file in files:
            if file.endswith(".sol"):
                sol_files.append(os.path.join(root, file))

    total_in_sample = len(sol_files)
    print(f"\n📂 Total contracts in sample: {total_in_sample}")

    # Pre-filter to get testable contracts count for progress bar
    print("⚙️  Pre-filtering contracts...\n")
    simple_contracts = [c for c in sol_files if is_simple_contract(c)]
    print(f"   Simple (testable): {len(simple_contracts)}")
    print(f"   Skipped (complex): {total_in_sample - len(simple_contracts)}\n")

    total_tested = 0
    skipped_complex = total_in_sample - len(simple_contracts)
    compilation_failed = 0
    reentrancy_count = 0
    access_control_count = 0
    approved_count = 0
    rejected_count = 0

    print("🔍 Running audit pipeline...\n")
    start_time = time.time()

    for idx, contract in enumerate(simple_contracts):

        ast_data = generate_ast(contract)

        if not ast_data:
            compilation_failed += 1
            print_progress(idx + 1, len(simple_contracts), start_time, approved_count, rejected_count)
            continue

        total_tested += 1

        issues = []
        issues.extend(detect_reentrancy(ast_data))
        issues.extend(detect_access_control(ast_data))

        if "reentrancy" in issues:
            reentrancy_count += 1

        if "access_control" in issues:
            access_control_count += 1

        if issues:
            rejected_count += 1
        else:
            approved_count += 1

            with open(contract, "r", encoding="utf-8", errors="ignore") as f:
                source_code = f.read()

            store_contract(source_code)

        print_progress(idx + 1, len(simple_contracts), start_time, approved_count, rejected_count)

    elapsed = time.time() - start_time
    mins, secs = divmod(int(elapsed), 60)

    print(f"\n\n{'='*50}")
    print("📊 Audit Summary")
    print(f"{'='*50}\n")
    print(f"  Total in Sample Folder    : {total_in_sample}")
    print(f"  Skipped (Imports/Complex) : {skipped_complex}")
    print(f"  Compilation Failed        : {compilation_failed}")
    print(f"  Contracts Tested          : {total_tested}")
    print(f"  ─────────────────────────")
    print(f"  Reentrancy Issues         : {reentrancy_count}")
    print(f"  Access Control Issues     : {access_control_count}")
    print(f"  ─────────────────────────")
    print(f"  ✅ Approved & Stored      : {approved_count}")
    print(f"  ❌ Rejected               : {rejected_count}")
    print(f"  ─────────────────────────")
    print(f"  ⏱️  Total Time             : {mins}m {secs}s")
    print(f"{'='*50}\n")


if __name__ == "__main__":
    main()