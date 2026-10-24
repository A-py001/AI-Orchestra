import os

def bundle_project(root_dir, output_file="project_bundle.txt", ignored_dirs=None, allowed_exts=None):
    # پوشه‌هایی که باید نادیده گرفته شوند
    if ignored_dirs is None:
        ignored_dirs = {'.git', 'venv', '__pycache__', '.idea', '.vscode', 'build', 'dist', 'node_modules'}
    
    # پسوندهای فایل‌هایی که می‌خواهیم جمع‌آوری کنیم
    if allowed_exts is None:
        allowed_exts = {'.py', '.md', '.txt', '.json', '.env.example'}

    print(f"Scanning directory: {os.path.abspath(root_dir)} ...")
    
    with open(output_file, 'w', encoding='utf-8') as outfile:
        file_count = 0
        for dirpath, dirnames, filenames in os.walk(root_dir):
            # فیلتر کردن پوشه‌های اضافی برای اینکه واردشان نشود
            dirnames[:] = [d for d in dirnames if d not in ignored_dirs]
            
            for filename in filenames:
                ext = os.path.splitext(filename)[1].lower()
                if ext in allowed_exts:
                    file_path = os.path.join(dirpath, filename)
                    rel_path = os.path.relpath(file_path, root_dir)
                    
                    # نادیده گرفتن خودِ فایل خروجی اگر توی همین پوشه ساخته شود
                    if rel_path == output_file:
                        continue
                    
                    print(f"Adding: {rel_path}")
                    outfile.write(f"\n{'='*70}\n")
                    outfile.write(f"FILE PATH: {rel_path}\n")
                    outfile.write(f"{'='*70}\n\n")
                    
                    try:
                        with open(file_path, 'r', encoding='utf-8') as infile:
                            outfile.write(infile.read())
                        outfile.write("\n\n")
                        file_count += 1
                    except Exception as e:
                        outfile.write(f"[Error reading file: {e}]\n\n")
                        
    print(f"\nDone! Successfully bundled {file_count} files into '{output_file}'.")

if __name__ == "__main__":
    # مسیر پوشه پروژه ('.' یعنی همین پوشه‌ای که اسکریپت داخل آن اجرا می‌شود)
    target_directory = bundle_project(".", output_file="C:/Users/Asus/Desktop/project_bundle.txt")
    bundle_project(target_directory)