import os
import urllib.request
import zipfile
import shutil

# Folder to store downloaded models
output_folder = "data/vosk_models"
os.makedirs(output_folder, exist_ok=True)

# Version to download
VERSION = "0.22"

# Vosk models URLs (version controlled by VERSION)
models = {
    "en-us": f"https://alphacephei.com/vosk/models/vosk-model-en-us-{VERSION}.zip",
    "es": f"https://alphacephei.com/vosk/models/vosk-model-es-{VERSION}.zip",
}

for lang, url in models.items():
    zip_path = os.path.join(output_folder, f"{lang}.zip")
    
    # Download the model
    print(f"Downloading {lang} model version {VERSION}...")
    urllib.request.urlretrieve(url, zip_path)
    
    # Extract the model
    print(f"Extracting {lang} model...")
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        temp_extract_path = os.path.join(output_folder, f"{lang}_temp")
        zip_ref.extractall(temp_extract_path)
    
    # Move contents to final folder without version number
    extracted_folder = next(os.scandir(temp_extract_path)).path
    final_folder = os.path.join(output_folder, lang)
    if os.path.exists(final_folder):
        shutil.rmtree(final_folder)
    shutil.move(extracted_folder, final_folder)
    
    # Clean up
    shutil.rmtree(temp_extract_path)
    os.remove(zip_path)
    
    print(f"{lang} model is ready in folder: {final_folder}\n")

print("All models have been downloaded and prepared in:", output_folder)
