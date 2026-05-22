import sys
import os
# 프로젝트 루트를 path에 추가하여 모듈을 임포트할 수 있게 함
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from modules.db_connector import PostgresDBConnector

def test_connection():
    db_url = os.getenv("DATABASE_URL")
    print(f"DATABASE_URL 로드됨: {db_url[:30]}...")
    
    print("PostgresDBConnector 초기화 시도...")
    connector = PostgresDBConnector()
    
    if connector.is_active():
        print("[SUCCESS] Supabase PostgreSQL connection and table initialization validated successfully!")
        try:
            with connector.conn.cursor() as cur:
                cur.execute("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public';
                """)
                tables = cur.fetchall()
                print(f"Current public tables in database: {tables}")
        except Exception as e:
            print(f"Error querying table list: {e}")
    else:
        print("[FAIL] Failed to connect to Supabase. Check database URL, password, or firewall settings.")

if __name__ == "__main__":
    test_connection()
