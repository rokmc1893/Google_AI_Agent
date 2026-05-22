# -*- coding: utf-8 -*-
import sys
import os
import io

# Reconfigure stdout to utf-8 to prevent console encoding issues
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
else:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from api.index import get_retriever

def test_retrieval_queries():
    retriever = get_retriever()
    
    queries = {
        "Civil (민사)": "채무불이행으로 인한 손해배상 청구 및 위약금 감액 조항",
        "Criminal (형사)": "사기 행위와 업무상 배임 횡령 신임관계 위배 처벌",
        "Administrative (행정)": "행정청의 신뢰보호의 원칙 및 비례의 원칙 최소침해 규정"
    }
    
    print("=== Testing Hybrid Retrieval from Supabase Database ===")
    for category, query in queries.items():
        print(f"\n[Category: {category}]")
        print(f"Query: '{query}'")
        
        results = retriever.retrieve(query, top_k=3)
        if not results:
            print("  -> No matching documents retrieved.")
        for idx, res in enumerate(results, 1):
            print(f"  {idx}. [{res.source}] (Score: {res.score:.4f})")
            print(f"     Text: {res.text[:120]}...")

if __name__ == "__main__":
    test_retrieval_queries()

