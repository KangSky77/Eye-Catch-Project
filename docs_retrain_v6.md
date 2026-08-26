# v6 재학습 절차 (익상편 데이터 반영)

> 노트북(RTX 3060 6GB)에서 학교 PC(RTX 2080 SUPER 8GB)로 옮겨 학습할 때의 순서.
> 데이터 정리는 이미 끝나 있고, **재학습 명령 한 줄만 실행**하면 된다.

## 0. 왜 재학습하는가

현재 배포 모델(v5)은 익상편을 백내장으로 오분류한다 — 정리된 원본 150개 기준
**위험 120장(80.0%) + 경계 12장(8.0%) = 88.0% 오분류**, 오분류 건 평균 점수 88.3%.
원인은 모델이 '수정체 혼탁'이 아니라 '눈이 하얗게 덮였는가'를 학습했기 때문이며,
밝은 홍채·플래시 반사 오탐과 같은 뿌리다.

익상편 225그룹을 `0_normal`(= 백내장 아님)에 넣어 그 경계를 다시 가르친다.

## 1. 학교 PC로 옮길 것

| 항목 | 크기 | 방법 |
|---|---|---|
| 코드·설정 47개 | – | `git pull` (branch: `feature/unified-polish`) |
| `data/dataset_group_map.json` | 717KB | git에 포함 — **dedup 재실행 불필요** |
| `dataset/` | **607MB** | USB·드라이브로 직접 복사 |
| `.env` | – | 직접 (DB 비밀번호 포함, git에 없음) |
| `cataract_efficientnet_b0_v4.pth` | 16MB | 선택 — 학습 전후 비교용 |

`dataset_raw/`(캐글 원본 1,749장)는 **옮기지 않아도 된다.** 정리가 이미 끝나
`dataset/0_normal/pterygium_*.jpg` 226장으로 반영돼 있다.

## 2. 학교 PC에서 확인

```bash
python -c "import torch; print(torch.cuda.is_available(), torch.cuda.get_device_name(0))"
```

`dataset/` 아래에 **폴더가 두 개뿐**이어야 한다:

```
dataset/
├── 0_normal/     15,420장 (익상편 226장 포함)
└── 1_cataract/    1,823장
```

> ⚠️ `dataset/` 안에 다른 폴더를 두면 `ImageFolder`가 그것도 클래스로 읽어
> 3클래스가 되고, 2클래스 모델과 어긋나 학습이 즉시 멈춘다(실제로 겪었다).
> 정리 전 원본은 반드시 `dataset_raw/` 같은 **바깥** 폴더에 둔다.

## 3. 학습

```bash
python scripts/train_ai_v4.py --backbone efficientnet_b0 --batch 40 --version v6
```

- `--batch 40` **유지**. 2080 SUPER(8GB)는 더 키울 수 있지만, v5와 같은 조건이라야
  성능 차이를 데이터 덕분이라고 말할 수 있다.
- 출력: `cataract_efficientnet_b0_v4.pth` (파일명은 _v4 고정, 메타데이터에 v6 기록)
- **학습 전 기존 가중치를 백업**할 것:
  ```bash
  cp cataract_efficientnet_b0_v4.pth cataract_efficientnet_b0_v5_prepterygium.pth
  ```

시작 로그가 아래와 같으면 정상이다:

```
클래스 매핑: {'0_normal': 0, '1_cataract': 1} (백내장=1 이어야 정상)
그룹 단위 분할 → train 12065 / val 2613 / test 2526 / 라벨충돌 제외 39
```

## 4. 학습 후 측정 (이게 핵심)

세 가지를 **모두** 확인해야 한다. 익상편만 좋아지고 백내장을 놓치면 실패다.

1. **익상편 오분류율** — 88.0%에서 얼마나 떨어졌나
2. **백내장 민감도** — v5의 98.9%에서 떨어지지 않았나 ← 가장 중요
3. **밝은 홍채 오탐** — v5의 18.2%에서 나빠지지 않았나

메타데이터(`cataract_efficientnet_b0_v4_metadata.json`)에 test 지표가 자동 기록된다.
익상편 오분류율은 별도 측정이 필요하다.

## 5. 결과가 나쁘면 되돌리기

```bash
cp cataract_efficientnet_b0_v5_prepterygium.pth cataract_efficientnet_b0_v4.pth
cp cataract_efficientnet_b0_v5_prepterygium_metadata.json cataract_efficientnet_b0_v4_metadata.json
```
