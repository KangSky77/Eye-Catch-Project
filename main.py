from fastapi import FastAPI, HTTPException, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import psycopg2
import torch
import torch.nn as nn
from torchvision import transforms
from PIL import Image
import io

app = FastAPI()

# 1. CORS 설정 (5500번 포트 친구 맺기)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. DB 연결 (비밀번호 본인 것으로 꼭 확인!)
def get_db_connection():
    try:
        return psycopg2.connect(
            host="localhost", database="eyecatch_db",
            user="postgres", password="Team23!", port="5432"
        )
    except Exception as e:
        print(f"🚨 DB 연결 실패: {e}")
        return None

class DiagnosisData(BaseModel):
    cataract_score: int
    macular_score: int
    glaucoma_score: int
    diabetic_score: int
    ai_result: str

# [교체 대상 1] AI 모델 구조 (train_ai.py와 100% 똑같아야 함!)
class CataractClassifier(nn.Module):
    def __init__(self):
        super(CataractClassifier, self).__init__()
        self.features = nn.Sequential(
            nn.Conv2d(3, 32, kernel_size=3, padding=1), nn.ReLU(),
            nn.MaxPool2d(2, 2),
            nn.Conv2d(32, 64, kernel_size=3, padding=1), nn.ReLU(),
            nn.MaxPool2d(2, 2),
            nn.Conv2d(64, 128, kernel_size=3, padding=1), nn.ReLU(),
            nn.MaxPool2d(2, 2)
        )
        self.classifier = nn.Sequential(
            nn.Linear(128 * 28 * 28, 512),
            nn.ReLU(),
            nn.Dropout(0.5), 
            nn.Linear(512, 2) # 정상(0), 백내장(1)
        )

    def forward(self, x):
        x = self.features(x)
        x = x.view(x.size(0), -1)
        x = self.classifier(x)
        return x

# [교체 대상 2] GPU로 뇌 파일 불러오기
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
ai_model = CataractClassifier().to(device)

try:
    # 학습 완료된 v2 파일을 불러옵니다
    ai_model.load_state_dict(torch.load('cataract_v2.pth', map_location=device, weights_only=True))
    ai_model.eval()
    print(f"✅ RTX 2080 Super 파워 장착 완료!")
except Exception as e:
    print(f"🚨 뇌 이식 실패 (파일 이름을 확인하세요): {e}")


# [교체 대상 1] AI 모델 구조 (train_ai.py와 100% 똑같아야 함!)
class CataractClassifier(nn.Module):
    def __init__(self):
        super(CataractClassifier, self).__init__()
        self.features = nn.Sequential(
            nn.Conv2d(3, 32, kernel_size=3, padding=1), nn.ReLU(),
            nn.MaxPool2d(2, 2),
            nn.Conv2d(32, 64, kernel_size=3, padding=1), nn.ReLU(),
            nn.MaxPool2d(2, 2),
            nn.Conv2d(64, 128, kernel_size=3, padding=1), nn.ReLU(),
            nn.MaxPool2d(2, 2)
        )
        self.classifier = nn.Sequential(
            nn.Linear(128 * 28 * 28, 512),
            nn.ReLU(),
            nn.Dropout(0.5), 
            nn.Linear(512, 2) # 정상(0), 백내장(1)
        )

    def forward(self, x):
        x = self.features(x)
        x = x.view(x.size(0), -1)
        x = self.classifier(x)
        return x

# [교체 대상 2] GPU로 뇌 파일 불러오기
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
ai_model = CataractClassifier().to(device)

try:
    # 학습 완료된 v2 파일을 불러옵니다
    ai_model.load_state_dict(torch.load('cataract_v2.pth', map_location=device, weights_only=True))
    ai_model.eval()
    print(f"✅ RTX 2080 Super 파워 장착 완료!")
except Exception as e:
    print(f"🚨 뇌 이식 실패 (파일 이름을 확인하세요): {e}")


# [교체 대상 3] AI 분석 엔드포인트 (로직 업데이트)
@app.post("/api/analyze-eye")
async def analyze_eye(file: UploadFile = File(...)):
    try:
        contents = await file.read()
        image = Image.open(io.BytesIO(contents)).convert('RGB')
        
        # 학습할 때 썼던 정규화 그대로 적용! (중요)
        preprocess = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
        ])
        
        input_tensor = preprocess(image).unsqueeze(0).to(device)

        with torch.no_grad():
            output = ai_model(input_tensor)
            probabilities = torch.nn.functional.softmax(output, dim=1)[0]
            
            # 인덱스 0: 정상, 1: 백내장
            prob_normal = probabilities[0].item() * 100
            prob_cataract = probabilities[1].item() * 100
            
        # 확률 비교 후 결과 도출
        if prob_cataract > prob_normal:
            result_text = "백내장 위험 단계 (정밀 검사 권장)"
            final_prob = prob_cataract
        else:
            result_text = "특이 소견 없음 (정상)"
            final_prob = prob_normal

        return {
            "status": "success", 
            "probability": round(final_prob, 1), 
            "result": result_text
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"분석 실패: {str(e)}")