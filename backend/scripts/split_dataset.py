"""
데이터셋 분할 스크립트
- 라벨링된 자기소개서 데이터를 Train/Validation/Test로 분할 (60/20/20)
- 계층 샘플링(Stratified Split)을 사용하여 합격/불합격 비율 유지
- 분할 결과를 데이터베이스에 저장
"""

import sys
import os
from pathlib import Path

# 프로젝트 루트 경로 추가
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

import numpy as np
from sqlalchemy import create_engine, text
from sklearn.model_selection import train_test_split
from dotenv import load_dotenv
import pandas as pd
from datetime import datetime

# 환경 변수 로드
load_dotenv()

# 데이터베이스 연결 설정
DB_HOST = os.getenv('POSTGRES_HOST', '114.202.2.226')
DB_PORT = os.getenv('POSTGRES_PORT', '5433')
DB_NAME = os.getenv('POSTGRES_DB', 'postgres')
DB_USER = os.getenv('POSTGRES_USER', 'postgres')
DB_PASSWORD = os.getenv('POSTGRES_PASSWORD', '')
DB_SCHEMA = 'mlops'

# 데이터베이스 URL 생성
import urllib.parse
encoded_password = urllib.parse.quote_plus(DB_PASSWORD)
DATABASE_URL = f"postgresql://{DB_USER}:{encoded_password}@{DB_HOST}:{DB_PORT}/{DB_NAME}"


class DatasetSplitter:
    """데이터셋 분할 클래스"""
    
    def __init__(self, test_size=0.2, val_size=0.2, random_state=42):
        """
        Args:
            test_size: 테스트 데이터 비율 (기본값: 0.2)
            val_size: 검증 데이터 비율 (train+val에서의 비율, 기본값: 0.2)
            random_state: 랜덤 시드
        """
        self.test_size = test_size
        self.val_size = val_size
        self.random_state = random_state
        self.engine = create_engine(DATABASE_URL)
        
    def load_labeled_data(self):
        """라벨링된 자기소개서 데이터 로드"""
        query = f"""
        SELECT 
            id,
            company,
            position,
            content,
            CASE WHEN is_passed = true THEN 'pass' ELSE 'fail' END as label,
            created_at
        FROM {DB_SCHEMA}.cover_letter_samples
        WHERE is_passed IS NOT NULL
        ORDER BY id
        """
        
        with self.engine.connect() as conn:
            df = pd.read_sql(text(query), conn)
        
        print(f"\n라벨링된 데이터 로드 완료: {len(df)}건")
        print(f"합격: {(df['label'] == 'pass').sum()}건")
        print(f"불합격: {(df['label'] == 'fail').sum()}건")
        
        return df
    
    def add_split_column(self):
        """데이터베이스에 split 컬럼 추가"""
        alter_query = f"""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 
                FROM information_schema.columns 
                WHERE table_schema = '{DB_SCHEMA}' 
                AND table_name = 'cover_letter_samples' 
                AND column_name = 'split'
            ) THEN
                ALTER TABLE {DB_SCHEMA}.cover_letter_samples 
                ADD COLUMN split VARCHAR(20);
            END IF;
        END $$;
        """
        
        with self.engine.connect() as conn:
            conn.execute(text(alter_query))
            conn.commit()
        
        print("split 컬럼 추가/확인 완료")
    
    def split_data(self, df):
        """
        데이터를 Train/Validation/Test로 분할
        
        Args:
            df: 전체 데이터프레임
            
        Returns:
            train_ids, val_ids, test_ids
        """
        # 라벨 분포 확인
        label_counts = df['label'].value_counts()
        print(f"\n전체 라벨 분포:")
        for label, count in label_counts.items():
            print(f"  {label}: {count}건 ({count/len(df)*100:.1f}%)")
        
        # 1단계: 전체 데이터를 (Train+Val) : Test 로 분할 (80:20)
        train_val_ids, test_ids = train_test_split(
            df['id'].values,
            test_size=self.test_size,
            stratify=df['label'].values,
            random_state=self.random_state
        )
        
        # 2단계: (Train+Val)을 Train : Val 로 분할 (75:25, 전체의 60:20)
        # val_size를 조정하여 전체의 20%가 되도록 함
        train_val_df = df[df['id'].isin(train_val_ids)]
        val_size_adjusted = self.val_size / (1 - self.test_size)  # 0.2 / 0.8 = 0.25
        
        train_ids, val_ids = train_test_split(
            train_val_ids,
            test_size=val_size_adjusted,
            stratify=train_val_df['label'].values,
            random_state=self.random_state
        )
        
        # 분할 결과 출력
        print(f"\n데이터 분할 완료:")
        print(f"  Train: {len(train_ids)}건 ({len(train_ids)/len(df)*100:.1f}%)")
        print(f"  Validation: {len(val_ids)}건 ({len(val_ids)/len(df)*100:.1f}%)")
        print(f"  Test: {len(test_ids)}건 ({len(test_ids)/len(df)*100:.1f}%)")
        
        # 각 분할의 라벨 분포 확인
        for split_name, split_ids in [('Train', train_ids), ('Validation', val_ids), ('Test', test_ids)]:
            split_df = df[df['id'].isin(split_ids)]
            split_label_counts = split_df['label'].value_counts()
            print(f"\n{split_name} 라벨 분포:")
            for label, count in split_label_counts.items():
                print(f"  {label}: {count}건 ({count/len(split_df)*100:.1f}%)")
        
        return train_ids, val_ids, test_ids
    
    def save_splits(self, train_ids, val_ids, test_ids):
        """분할 결과를 데이터베이스에 저장"""
        # Train 업데이트
        train_update = f"""
        UPDATE {DB_SCHEMA}.cover_letter_samples
        SET split = 'train'
        WHERE id = ANY(:ids)
        """
        
        # Validation 업데이트
        val_update = f"""
        UPDATE {DB_SCHEMA}.cover_letter_samples
        SET split = 'validation'
        WHERE id = ANY(:ids)
        """
        
        # Test 업데이트
        test_update = f"""
        UPDATE {DB_SCHEMA}.cover_letter_samples
        SET split = 'test'
        WHERE id = ANY(:ids)
        """
        
        with self.engine.connect() as conn:
            # Train
            conn.execute(text(train_update), {'ids': train_ids.tolist()})
            print(f"Train 데이터 업데이트: {len(train_ids)}건")
            
            # Validation
            conn.execute(text(val_update), {'ids': val_ids.tolist()})
            print(f"Validation 데이터 업데이트: {len(val_ids)}건")
            
            # Test
            conn.execute(text(test_update), {'ids': test_ids.tolist()})
            print(f"Test 데이터 업데이트: {len(test_ids)}건")
            
            conn.commit()
        
        print("\n분할 결과 데이터베이스 저장 완료")
    
    def verify_splits(self):
        """분할 결과 검증"""
        query = f"""
        SELECT 
            split,
            CASE WHEN is_passed = true THEN 'pass' ELSE 'fail' END as label,
            COUNT(*) as count
        FROM {DB_SCHEMA}.cover_letter_samples
        WHERE is_passed IS NOT NULL
        GROUP BY split, is_passed
        ORDER BY split, is_passed
        """
        
        with self.engine.connect() as conn:
            result = pd.read_sql(text(query), conn)
        
        print("\n분할 결과 검증:")
        print(result.to_string(index=False))
        
        # 전체 통계
        total_query = f"""
        SELECT 
            split,
            COUNT(*) as total
        FROM {DB_SCHEMA}.cover_letter_samples
        WHERE is_passed IS NOT NULL
        GROUP BY split
        ORDER BY split
        """
        
        with self.engine.connect() as conn:
            total_result = pd.read_sql(text(total_query), conn)
        
        print("\n분할별 전체 통계:")
        print(total_result.to_string(index=False))
    
    def run(self):
        """전체 프로세스 실행"""
        print("="*60)
        print("데이터셋 분할 시작")
        print("="*60)
        print(f"분할 비율: Train 60% / Validation 20% / Test 20%")
        print(f"Random Seed: {self.random_state}")
        
        start_time = datetime.now()
        
        try:
            # 1. split 컬럼 추가
            self.add_split_column()
            
            # 2. 라벨링된 데이터 로드
            df = self.load_labeled_data()
            
            if len(df) == 0:
                print("\n경고: 라벨링된 데이터가 없습니다.")
                return
            
            # 3. 데이터 분할
            train_ids, val_ids, test_ids = self.split_data(df)
            
            # 4. 분할 결과 저장
            self.save_splits(train_ids, val_ids, test_ids)
            
            # 5. 결과 검증
            self.verify_splits()
            
            end_time = datetime.now()
            elapsed = (end_time - start_time).total_seconds()
            
            print("\n" + "="*60)
            print(f"데이터셋 분할 완료 (소요 시간: {elapsed:.2f}초)")
            print("="*60)
            
        except Exception as e:
            print(f"\n오류 발생: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    splitter = DatasetSplitter(
        test_size=0.2,      # 전체의 20%를 테스트 세트로
        val_size=0.2,       # 전체의 20%를 검증 세트로
        random_state=42     # 재현성을 위한 시드
    )
    splitter.run()
