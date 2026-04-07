import torch
import torch.nn as nn
import torch.optim as optim
from torchvision import datasets, transforms, models
from torch.utils.data import DataLoader
import os

# 1. 장치 설정 (RTX 2080 SUPER를 사용하기 위해 CUDA 설정)
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"🚀 현재 사용 중인 장치: {device}")

# 2. 데이터 전처리 및 증강 (Data Augmentation)
# 사진이 부족하거나 각도가 달라도 AI가 잘 인식하게 만드는 비법입니다.
data_transforms = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.RandomHorizontalFlip(), # 좌우 반전 (눈은 좌우가 비슷하니까요)
    transforms.RandomRotation(10),     # 살짝 회전 (고개가 갸우뚱할 수 있으니)
    transforms.ColorJitter(brightness=0.2, contrast=0.2), # 밝기, 대비 조절 (조명 차이 극복)
    transforms.ToTensor(),
    transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]) # 이미지 정규화
])

# 3. 데이터셋 불러오기
data_dir = './dataset'
image_datasets = datasets.ImageFolder(data_dir, data_transforms)
# batch_size는 한번에 학습할 사진 양입니다. 2080 성능이 좋으니 32로 올립니다.
dataloader = DataLoader(image_datasets, batch_size=32, shuffle=True)

# 4. 딥러닝 모델 설계 (VGG/ResNet 급의 깊은 구조)
class CataractClassifier(nn.Module):
    def __init__(self):
        super(CataractClassifier, self).__init__()
        # 특징 추출부 (Convolution Layers)
        self.features = nn.Sequential(
            nn.Conv2d(3, 32, kernel_size=3, padding=1), nn.ReLU(),
            nn.MaxPool2d(2, 2),
            nn.Conv2d(32, 64, kernel_size=3, padding=1), nn.ReLU(),
            nn.MaxPool2d(2, 2),
            nn.Conv2d(64, 128, kernel_size=3, padding=1), nn.ReLU(),
            nn.MaxPool2d(2, 2)
        )
        # 의사결정부 (Fully Connected Layers)
        self.classifier = nn.Sequential(
            nn.Linear(128 * 28 * 28, 512),
            nn.ReLU(),
            nn.Dropout(0.5), # 과적합 방지 (전부 백내장이라고 찍는 병 예방)
            nn.Linear(512, 2) # 결과는 딱 2개 (정상/백내장)
        )

    def forward(self, x):
        x = self.features(x)
        x = x.view(x.size(0), -1) # 1차원으로 펼치기
        x = self.classifier(x)
        return x

# 모델 생성 및 GPU로 보내기
model = CataractClassifier().to(device)

# 5. 손실 함수와 최적화 도구
criterion = nn.CrossEntropyLoss()
optimizer = optim.Adam(model.parameters(), lr=0.0001) # 학습률을 낮춰서 꼼꼼하게 학습

# 6. 학습 시작
epochs = 30 # 데이터가 많으면 30~50번 정도 돌려야 똑똑해집니다.
print("🏋️ 모델 학습을 시작합니다...")

for epoch in range(epochs):
    running_loss = 0.0
    model.train()
    
    for inputs, labels in dataloader:
        inputs, labels = inputs.to(device), labels.to(device) # 데이터를 GPU로 전송
        
        optimizer.zero_grad()
        outputs = model(inputs)
        loss = criterion(outputs, labels)
        loss.backward()
        optimizer.step()
        
        running_loss += loss.item()
    
    print(f"[{epoch+1}/{epochs}] 오차(Loss): {running_loss/len(dataloader):.4f}")

# 7. 최종 뇌 파일 저장
torch.save(model.state_dict(), 'cataract_v2.pth')
print("✅ 학습 완료! 'cataract_v2.pth' 파일이 저장되었습니다.")