import os
import shutil
from pathlib import Path

BASE_DIR = Path(r"c:\Users\alibr\OneDrive\Desktop\bot zuura")

def clean_project():
    print("🧹 Tozalash jarayoni boshlandi...")
    
    # 1. Barcha __pycache__ papkalarini guruhlab o'chirish
    cache_count = 0
    for p in BASE_DIR.rglob("__pycache__"):
        if p.is_dir():
            try:
                shutil.rmtree(p)
                cache_count += 1
            except Exception as e:
                print(f"Xato: {p} o'chirilmadi - {e}")
                
    if cache_count:
        print(f"✅ {cache_count} ta __pycache__ papkasi o'chirildi.")
    
    # 2. Eski university.db ni o'chirish
    old_db = BASE_DIR / "university.db"
    if old_db.exists() and old_db.is_file():
        try:
            old_db.unlink()
            print("✅ Eski 'university.db' o'chirildi.")
        except Exception as e:
            print(f"Xato: university.db o'chirilmadi - {e}")

    # 3. tmp papkasini o'chirish
    tmp_dir = BASE_DIR / "tmp"
    if tmp_dir.exists() and tmp_dir.is_dir():
        try:
            shutil.rmtree(tmp_dir)
            print("✅ 'tmp' papkasi va uning ichidagi test skriptlar o'chirildi.")
        except Exception as e:
            print(f"Xato: tmp papkasi o'chirilmadi - {e}")
            
    print("✨ Barcha keraksiz narsalar tozalandi!")
    
    # O'z-o'zini o'chirish (cleaner.py)
    try:
        os.remove(__file__)
        print("✅ cleaner.py ham o'zini o'chirdi.")
    except:
        pass

if __name__ == "__main__":
    clean_project()
