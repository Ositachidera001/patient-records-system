from pathlib import Path

def setup_ecommerce_dummies(drop_folder: Path):
    """Creates sample product images for sorting."""
    drop_folder.mkdir(parents=True, exist_ok=True)
    
    dummy_images = [
        "samsung_tv_4k.jpg",
        "lg_oled_tv.png",
        "ankara_dress.jpg",
        "designer_shirt.png",
        "garri_wholesale.png",
        "ijebu_garri_bag.jpg",
        "random_item.png"
    ]
    
    for img_name in dummy_images:
        file_path = drop_folder / img_name
        if not file_path.exists():
            file_path.touch()  # Creates empty file safely
    print("✅ Dummy product images generated.\n")

def organize_product_images(drop_folder: Path, base_products_folder: Path):
    """Sorts incoming product images into keyword-based category subfolders."""
    
    # Keyword-to-Category Mapping
    KEYWORD_MAP = {
        "tv": base_products_folder / "electronics",
        "dress": base_products_folder / "clothing",
        "shirt": base_products_folder / "clothing",
        "garri": base_products_folder / "food"
    }
    
    uncategorized_folder = base_products_folder / "uncategorized"
    category_counts = {}

    print("🛒 SORTING E-COMMERCE PRODUCT IMAGES...")
    print("-" * 55)

    for img_path in drop_folder.glob("*"):
        if not img_path.is_file():
            continue

        stem = img_path.stem    # Filename without extension
        suffix = img_path.suffix  # File extension (.jpg, .png)
        
        target_folder = uncategorized_folder
        
        # Check keywords inside filename stem
        for keyword, folder in KEYWORD_MAP.items():
            if keyword in stem.lower():
                target_folder = folder
                break
        
        # Create directory safely and move file
        target_folder.mkdir(parents=True, exist_ok=True)
        category_name = target_folder.name
        
        destination = target_folder / img_path.name
        # Line 60
        img_path.replace(destination)
        
        # Track total counts
        category_counts[category_name] = category_counts.get(category_name, 0) + 1
        
        print(f"Sorted: {stem:<22} ({suffix}) ➔ {category_name}/")

    print("-" * 55)
    print("📈 FINAL CATEGORY COUNTS:")
    for cat, count in category_counts.items():
        print(f"  • {cat.capitalize():15}: {count} image(s)")
    print("-" * 55 + "\n")

# ── RUN SCRIPT ──────────────────────────────────────────────────
if __name__ == "__main__":
    BASE_ECOM = Path.cwd() / "ecommerce_data"
    DROP_ZONE = BASE_ECOM / "new_uploads"
    PRODUCTS_DIR = BASE_ECOM / "products"
    
    # Generate and process images
    setup_ecommerce_dummies(DROP_ZONE)
    organize_product_images(DROP_ZONE, PRODUCTS_DIR)