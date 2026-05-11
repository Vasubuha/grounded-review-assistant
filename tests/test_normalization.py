import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend.services.normalization import normalize_product_name
from backend.validators import explicit_product_match

def test():
    queries = [
        "vivo T5X 5G",
        "Vivo t5x 5g review",
        "t5x 5g vivo",
        "vivo t5x"
    ]
    
    ids = set()
    for q in queries:
        try:
            res = normalize_product_name(q)
            ids.add(res['id'])
            print(f"Query: '{q}' -> ID: {res['id'][:8]}... Canonical: {res['canonical_name']}")
        except ValueError as e:
            print(f"Query: '{q}' -> Rejected: {e}")
            
    print(f"\nUnique IDs generated for full identifiers: {len(ids)}")
    
    print("\nTesting chunk validator...")
    # Assume canonical name is vivo t5x 5g
    brand = "vivo"
    model = "t5x"
    
    chunks = [
        "The vivo t5x is a great phone.",
        "I really like the t5x from vivo.",
        "The vivo t series is decent.", # Should fail (missing t5x)
        "The t5x 5g has a good camera.", # Should fail (missing vivo)
        "vivo makes good phones." # Should fail (missing t5x)
    ]
    
    for c in chunks:
        match = explicit_product_match(c, brand, model)
        print(f"Chunk: '{c}' -> Match: {match}")

if __name__ == "__main__":
    test()
