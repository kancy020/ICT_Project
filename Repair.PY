import os
import ast
import subprocess
import sys
import importlib.util

def find_python_files(root_dir):
    """Recursively find all .py files in the project."""
    python_files = []
    for dirpath, _, filenames in os.walk(root_dir):
        for fname in filenames:
            if fname.endswith('.py'):
                python_files.append(os.path.join(dirpath, fname))
    return python_files

def extract_imports(file_path):
    """Parse a Python file and extract imported module names."""
    with open(file_path, 'r', encoding='utf-8') as f:
        tree = ast.parse(f.read(), filename=file_path)
    modules = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                modules.add(alias.name.split('.')[0])
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.add(node.module.split('.')[0])
    return modules

def is_third_party(module_name):
    """Determine if a module is third-party (in site-packages)."""
    # Skip builtins and project modules
    if module_name in sys.builtin_module_names or module_name == "__main__":
        return False
    try:
        spec = importlib.util.find_spec(module_name)
    except (ValueError, ModuleNotFoundError):
        # treat unknown or malformed specs as third-party
        return True
    if spec and spec.origin:
        return 'site-packages' in spec.origin or 'dist-packages' in spec.origin
    return False

def install_package(package_name):
    """Install a package via pip."""
    print(f"[check_env] Installing missing package: {package_name}")
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', package_name])

def main():
    project_root = os.getcwd()
    print(f"[check_env] Scanning for Python files in {project_root}...")
    py_files = find_python_files(project_root)

    all_imports = set()
    for py in py_files:
        all_imports.update(extract_imports(py))

    # Filter to third-party modules
    to_check = sorted(m for m in all_imports if is_third_party(m))
    if not to_check:
        print("[check_env] No third-party dependencies detected or all are installed.")
        return

    print("[check_env] Detected third-party modules:", ', '.join(to_check))
    for module in to_check:
        try:
            __import__(module)
            print(f"[check_env] Module '{module}' is already installed.")
        except ImportError:
            try:
                install_package(module)
            except subprocess.CalledProcessError:
                print(f"[check_env] Failed to install '{module}'. Please install it manually.")

if __name__ == '__main__':
    main()
