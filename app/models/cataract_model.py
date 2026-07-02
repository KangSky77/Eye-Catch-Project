import torch.nn as nn
from torchvision import models

# ============================================================
# 전이학습(Transfer Learning) 기반 백내장 분류 모델
#
# 기존: conv 3층짜리 from-scratch CNN (과적합 심하고 정확도 낮음)
# 변경: ImageNet 사전학습 백본 + 2클래스 분류 헤드 교체
#
# 지원 백본 (train_ai_v4.py의 --backbone 인자와 대응):
# - resnet18        : v2/v3부터 사용해 온 기본 백본 (파라미터 11.7M)
# - efficientnet_b0 : v4 백본 비교 실험용 (파라미터 5.3M, 더 최신 구조)
#
# - 학습 시:   build_model(pretrained=True, backbone=...)  → ImageNet 가중치로 시작
# - 추론 시:   build_model(backbone=settings.model_backbone) → 우리가 학습한 .pth를 load
# 입력 전처리는 두 백본 모두 vision.py와 동일하게 224x224 + ImageNet 정규화를 사용합니다.
# ============================================================

def build_model(pretrained: bool = False, backbone: str = "resnet18") -> nn.Module:
    if backbone == "resnet18":
        weights = models.ResNet18_Weights.IMAGENET1K_V1 if pretrained else None
        model = models.resnet18(weights=weights)
        in_features = model.fc.in_features
        # 분류 헤드를 2클래스(정상/백내장)로 교체
        model.fc = nn.Sequential(
            nn.Dropout(0.4),
            nn.Linear(in_features, 2),
        )
    elif backbone == "efficientnet_b0":
        weights = models.EfficientNet_B0_Weights.IMAGENET1K_V1 if pretrained else None
        model = models.efficientnet_b0(weights=weights)
        in_features = model.classifier[1].in_features
        # resnet18 헤드와 동일한 구성(Dropout 0.4 + Linear)으로 맞춰 공정 비교
        model.classifier = nn.Sequential(
            nn.Dropout(0.4),
            nn.Linear(in_features, 2),
        )
    else:
        raise ValueError(f"지원하지 않는 백본: {backbone} (resnet18 | efficientnet_b0)")
    return model


def head_param_prefix(backbone: str) -> str:
    """1단계(백본 동결, 헤드만 학습)에서 학습할 파라미터 이름의 접두사."""
    return "fc." if backbone == "resnet18" else "classifier."
