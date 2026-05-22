import sys
import os
import psycopg2

def test_param_connection():
    print("파라미터 직접 지정 방식(URL 파싱 우회)으로 Supabase 연결 시도...")
    try:
        conn = psycopg2.connect(
            host="aws-1-ap-southeast-1.pooler.supabase.com",
            port=6543,
            user="postgres.hdkqbhxhderykyabsfna",
            password="@@Pmj0611101",
            database="postgres"
        )
        print("✅ 성공: 파라미터 직접 접속으로 Supabase 연결에 성공했습니다!")
        conn.close()
    except Exception as e:
        print(f"❌ 실패: 파라미터 직접 접속도 실패했습니다. 에러 메시지: {e}")

if __name__ == "__main__":
    test_param_connection()
