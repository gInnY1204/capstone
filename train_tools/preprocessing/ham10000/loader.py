import os
from kaggle.api.kaggle_api_extended import KaggleApi
import kaggle

# 현재 경로
current_dir = os.path.dirname(os.path.abspath(__file__))
save_dir = os.path.join(current_dir, "ham10000_dataset")
os.makedirs(save_dir, exist_ok=True)

# Kaggle API 인증
print("[INFO] 인증 중...")
api = KaggleApi()
api.authenticate()
print("[INFO] 인증 완료")
kaggle.api.authenticate()
# 데이터 다운로드
print("[INFO] 다운로드 시작...")
kaggle.api.dataset_download_files(
    'kmader/skin-cancer-mnist-ham10000',
    path=save_dir,
    unzip=True,
    quiet=False
)
print("[INFO] 다운로드 완료!")
