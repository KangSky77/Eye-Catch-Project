import torch.nn as nn
from torchvision import models

# ============================================================
# 전이학습(Transfer Learning) 기반 백내장 분류 모델
#
# 기존: conv 3층짜리 from-scratch CNN (과적합 심하고 정확도 낮음)
# 변경: ImageNet 사전학습 ResNet18 백본 + 분류 헤드 교체
#
# - 학습 시:   build_model(pretrained=True)  → ImageNet 가중치로 시작
# - 추론 시:   build_model()                  → 우리가 학습한 .pth를 load
# 입력 전처리는 vision.py와 동일하게 224x224 + ImageNet 정규화를 사용합니다.
# ============================================================

def build_model(pretrained: bool = False) -> nn.Module:
    weights = models.ResNet18_Weights.IMAGENET1K_V1 if pretrained else None
    model = models.resnet18(weights=weights)

    # 분류 헤드를 2클래스(정상/백내장)로 교체
    in_features = model.fc.in_features
    model.fc = nn.Sequential(
        nn.Dropout(0.4),
        nn.Linear(in_features, 2),
    )
    return model
