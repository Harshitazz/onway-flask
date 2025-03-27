import pandas as pd
import joblib
import os
import ast
import faiss  # Fast similarity search
from sentence_transformers import SentenceTransformer
from sklearn.feature_extraction.text import TfidfVectorizer

DATA_PATH = "./database/products.csv"

# Ensure necessary folders exist
os.makedirs("./models", exist_ok=True)

# Load dataset
df = pd.read_csv(DATA_PATH)
df.fillna("", inplace=True)

print ("1")

# Extract first-level category
def extract_first_level_category(category_str):
    try:
        categories = ast.literal_eval(category_str)
        return categories[0].split(">>")[0].strip()
    except:
        return "Unknown"

df["first_level_category"] = df["product_category_tree"].apply(extract_first_level_category)

print ("2")


# Extract clean category names
def extract_clean_categories(category_str):
    try:
        categories = ast.literal_eval(category_str)
        return " ".join(cat.strip() for cat in categories[0].split(">>"))
    except:
        return "Unknown"

df["clean_category"] = df["product_category_tree"].apply(extract_clean_categories)
df["text"] = df["product_name"] + " " + df["clean_category"]

print ("1")


# Initialize SBERT Model
sbert_model = SentenceTransformer("all-MiniLM-L6-v2")  

print ("2")

# Generate Sentence Embeddings
sentence_embeddings = sbert_model.encode(
    df["text"].tolist(), 
    convert_to_numpy=True, 
    batch_size=64,  # Adjust batch size (64-128 for best performance)
    show_progress_bar=True  
)

print ("1")

# Save SBERT embeddings
joblib.dump(sentence_embeddings, "./models/sbert_embeddings.pkl")
joblib.dump(df, "./models/product_df.pkl")
print ("2")

# Store embeddings in Faiss for fast retrieval
dimension = sentence_embeddings.shape[1]  # SBERT embedding size (384 for MiniLM)
faiss_index = faiss.IndexFlatL2(dimension)
faiss_index.add(sentence_embeddings)

print ("1")

# Save Faiss index
faiss.write_index(faiss_index, "./models/faiss_index.bin")

# Save SBERT model path (optional, since it can be reloaded directly)
joblib.dump(sbert_model, "./models/sbert_model.pkl")

print("SBERT embeddings and models saved successfully!")
