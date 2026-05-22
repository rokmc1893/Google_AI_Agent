# -*- coding: utf-8 -*-
import os
import sys
import numpy as np
from pathlib import Path
from dotenv import load_dotenv

# Load env
load_dotenv()

# Insert project root to path
root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from modules.rag_retriever import LegalDocument
from modules.law_api_ingester import LawDataIngester
from api.index import get_embed_fn

# 1. Define the collection of laws
laws_data = [
    # --- 민법 (Civil Act) ---
    {
        "id": "statute_civil_390",
        "source": "민법 제390조 (채무불이행과 손해배상)",
        "source_type": "statute",
        "text": "제390조(채무불이행과 손해배상) 채무자가 채무의 내용에 좇은 이행을 하지 아니한 때에는 채권자는 손해배상을 청구할 수 있다. 그러나 채무자의 고의나 과실없이 이행할 수 없게 된 때에는 그러하지 아니하다.",
        "tags": ["민법", "채무불이행", "손해배상", "계약불이행"]
    },
    {
        "id": "statute_civil_398",
        "source": "민법 제398조 (손해배상액의 예정)",
        "source_type": "statute",
        "text": "제398조(손해배상액의 예정) ①당사자는 채무불이행에 관한 손해배상액을 예정할 수 있다. ②손해배상의 예정액이 부당히 과다한 경우에는 법원은 적당히 감액할 수 있다. ③손해배상액의 예정은 이행의 청구나 계약의 해제에 영향을 미치지 아니한다. ④위약금의 약정은 손해배상액의 예정으로 추정한다.",
        "tags": ["민법", "손해배상액의예정", "위약금", "감액", "지체상금"]
    },
    {
        "id": "statute_civil_543",
        "source": "민법 제543조 (해제, 해지권)",
        "source_type": "statute",
        "text": "제543조(해제, 해지권) ①계약 또는 법률의 규정에 의하여 당사자의 일방 또는 쌍방이 해지 또는 해제의 권리가 있는 때에는 그 해지 또는 해제는 상대방에 대한 의사표시로 한다. ②전항의 의사표시는 철회하지 못한다.",
        "tags": ["민법", "계약해제", "계약해지", "해제권", "해지권"]
    },
    {
        "id": "statute_civil_548",
        "source": "민법 제548조 (해제의 효과, 원상회복의무)",
        "source_type": "statute",
        "text": "제548조(해제의 효과, 원상회복의무) ①당사자 일방이 계약을 해제한 때에는 각 당사자는 그 상대방에 대하여 원상회복의 의무가 있다. 그러나 제삼자의 권리를 해하지 못한다. ②전항의 경우에 반환할 금전에는 그 받은 날로부터 이자를 가하여야 한다.",
        "tags": ["민법", "원상회복", "계약해제", "원상회복의무"]
    },
    {
        "id": "statute_civil_2",
        "source": "민법 제2조 (신의성실)",
        "source_type": "statute",
        "text": "제2조(신의성실) ①권리의 행사와 의무의 이행은 신의에 좇아 성실히 하여야 한다. ②권리는 남용하지 못한다.",
        "tags": ["민법", "신의성실", "권리남용", "신의칙"]
    },
    # --- 형법 (Criminal Act) ---
    {
        "id": "statute_criminal_347",
        "source": "형법 제347조 (사기)",
        "source_type": "statute",
        "text": "제347조(사기) ①사람을 기망하여 재물의 교부를 받거나 재산상의 이익을 취득한 자는 10년 이하의 징역 또는 2천만원 이하의 벌금에 처한다. ②전항의 방법으로 제삼자로 하여금 재물의 교부를 받게 하거나 재산상의 이익을 취득하게 한 때에도 전항의 형과 같다.",
        "tags": ["형법", "사기", "기망", "형사처벌"]
    },
    {
        "id": "statute_criminal_355",
        "source": "형법 제355조 (횡령, 배임)",
        "source_type": "statute",
        "text": "제355조(횡령, 배임) ①타인의 재물을 보관하는 자가 그 재물을 횡령하거나 그 반환을 거부한 때에는 5년 이하의 징역 또는 1천500만원 이하의 벌금에 처한다. ②타인의 사무를 처리하는 자가 그 임무에 위배하는 행위로써 재산상의 이익을 취득하거나 제삼자로 하여금 이를 취득하게 하여 본인에게 손해를 가한 때에도 전항의 형과 같다.",
        "tags": ["형법", "횡령", "배임", "신임관계"]
    },
    {
        "id": "statute_criminal_356",
        "source": "형법 제356조 (업무상의 횡령과 배임)",
        "source_type": "statute",
        "text": "제356조(업무상의 횡령과 배임) 업무상의 임무에 위배하여 제355조의 죄를 범한 자는 10년 이하의 징역 또는 3천만원 이하의 벌금에 처한다.",
        "tags": ["형법", "업무상배임", "업무상횡령", "배임죄"]
    },
    # --- 약관의 규제에 관한 법률 (약관법) ---
    {
        "id": "statute_terms_6",
        "source": "약관의 규제에 관한 법률 제6조 (일반원칙)",
        "source_type": "statute",
        "text": "제6조(일반원칙) ① 신의성실의 원칙을 위반하여 공정성을 잃은 약관 조항은 무효이다. ② 약관의 내용 중 다음 각 호의 어느 하나에 해당하는 조항은 공정성을 잃은 것으로 추정된다.\n1. 고객에게 부당하게 불리한 조항\n2. 고객이 계약의 거래형태 등 관련된 모든 사정에 비추어 예상하기 어려운 조항\n3. 계약의 목적을 달성할 수 없을 정도로 계약에 따르는 고객의 본질적 권리를 제한하는 조항",
        "tags": ["약관법", "불공정약관", "무효", "부당하게불리한조항"]
    },
    {
        "id": "statute_terms_8",
        "source": "약관의 규제에 관한 법률 제8조 (손해배상액의 예정)",
        "source_type": "statute",
        "text": "제8조(손해배상액의 예정) 고객에게 부당하게 과중한 지체상금이나 그 밖의 손해배상 의무를 부과하는 약관 조항은 무효로 한다.",
        "tags": ["약관법", "손해배상액의예정", "무효", "과중한지체상금"]
    },
    {
        "id": "statute_terms_9",
        "source": "약관의 규제에 관한 법률 제9조 (계약의 해제·해지)",
        "source_type": "statute",
        "text": "제9조(계약의 해제·해지) 계약의 해제·해지에 관하여 정하고 있는 약관의 내용 중 다음 각 호의 어느 하나에 해당하는 조항은 무효로 한다.\n1. 법률에 따른 고객의 해제권 또는 해지권을 부당하게 제한하는 조항\n2. 사업자에게 법률에서 규정하지 아니한 해제권 또는 해지권을 부여하여 고객에게 부당하게 불이익을 줄 우려가 있는 조항\n3. 법률에 따른 사업자의 해제권 또는 해지권의 행사 조건을 완화하여 고객에게 부당하게 불이익을 줄 우려가 있는 조항\n4. 계약의 해제 또는 해지로 인한 고객의 원상회복의무를 부당하게 무겁게 하는 조항",
        "tags": ["약관법", "계약해제", "계약해지", "해제권제한", "원상회복의무가중"]
    },
    # --- 독점규제 및 공정거래에 관한 법률 (공정거래법) ---
    {
        "id": "statute_ft_45",
        "source": "독점규제 및 공정거래에 관한 법률 제45조 (불공정거래행위의 금지)",
        "source_type": "statute",
        "text": "제45조(불공정거래행위의 금지) ① 사업자는 다음 각 호의 어느 하나에 해당하는 행위로서 공정한 거래를 저해할 우려가 있는 행위를 하거나, 계열회사 또는 다른 사업자로 하여금 이를 행하도록 하여서는 아니 된다.\n1. 거래를 거절하거나 거래의 상대방을 차별하여 취급하는 행위\n2. 경쟁사업자를 배제하는 행위\n3. 부당하게 경쟁사업자의 고객을 자기와 거래하도록 유인하거나 강제하는 행위\n4. 자기의 거래상의 지위를 부당하게 이용하여 상대방과 거래하는 행위\n5. 거래의 상대방의 사업활동을 부당하게 구속하거나 다른 사업자의 사업활동을 방해하는 행위",
        "tags": ["공정거래법", "불공정거래행위", "지위남용", "갑질방지"]
    },
    # --- 행정기본법 (Administrative Basic Act) ---
    {
        "id": "statute_admin_12",
        "source": "행정기본법 제12조 (신뢰보호의 원칙)",
        "source_type": "statute",
        "text": "제12조(신뢰보호의 원칙) ① 행정청은 공익 또는 제3자의 이익을 현저히 해칠 우려가 있는 경우를 제외하고는 행정에 대한 국민의 정당하고 합리적인 신뢰를 보호하여야 한다. ② 행정청은 국민이 행정에 대하여 개인의 귀책사유가 없음에도 불구하고 정당하고 합리적인 신뢰를 가졌다면 그 신뢰를 보호하여야 한다.",
        "tags": ["행정기본법", "신뢰보호", "행정원칙"]
    },
    {
        "id": "statute_admin_13",
        "source": "행정기본법 제13조 (비례의 원칙)",
        "source_type": "statute",
        "text": "제13조(비례의 원칙) 행정청은 다음 각 호의 원칙에 따라 행정작용을 하여야 한다.\n1. 행정목적을 달성하는 데 유효하고 적절할 것\n2. 행정목적을 달성하는 데 필요한 최소한도에 그칠 것\n3. 행정작용으로 인한 국민의 이익 침해가 그 행정작용이 의도하는 공익보다 크지 아니할 것",
        "tags": ["행정기본법", "비례의원칙", "최소침해"]
    }
]

def populate():
    # Convert data to LegalDocument list
    docs = []
    for d in laws_data:
        docs.append(LegalDocument(
            id=d["id"],
            source=d["source"],
            source_type=d["source_type"],
            text=d["text"],
            tags=d["tags"]
        ))
        
    print(f"[Populate] Preparing to load {len(docs)} real laws across Civil, Criminal, and Administrative fields...")
    
    # Calculate embeddings
    embed_fn = get_embed_fn()
    embeddings = []
    
    for i, doc in enumerate(docs):
        print(f"[{i+1}/{len(docs)}] Generating embedding for: {doc.source}")
        emb = embed_fn(doc.text)
        embeddings.append(np.array(emb, dtype=np.float32))
        
    # Save to JSON database (which automatically syncs to Supabase if DATABASE_URL is active)
    db_path = root_dir / "tests" / "fixtures" / "sample_legal_db.json"
    ingester = LawDataIngester(db_path)
    
    print("[Populate] Writing documents to DB (Supabase & JSON)...")
    ingester.save_to_json_db(docs, embeddings)
    print("[Populate] Ingestion completed successfully!")

if __name__ == "__main__":
    populate()
