## 커밋 컨벤션

프로젝트의 일관성을 위해 아래 규칙을 따라주세요.

### 커밋 메시지 형식

```
타입: 간단한 설명
```

### 타입 종류

* `feat`: 새 기능 추가
* `fix`: 버그 수정
* `design`: 디자인 에셋 추가
* `docs`: 문서 수정
* `refactor`: 코드 리팩토링

### 예시

```bash
git commit -m "feat: 벽 반사 로직 구현"
git commit -m "fix: 충돌 감지 버그 수정"
git commit -m "design: 버블 스프라이트 추가"
git commit -m "docs: README 설치 방법 추가"
```

---

## 파일 구조

새 파일 추가 시 아래 구조를 따라주세요.

```
bubble-pop-game/  
├── src/  
│   ├── main.py              # 게임 엔트리 포인트
│   ├── game.py              # 게임 메인 로직
│   ├── map_editor.py        # 맵 에디터
│   ├── scene_manager.py     # Scene 관리
│   ├── scene_factory.py     # Scene 팩토리
│   ├── *_scene.py          # 각종 Scene 파일
│   ├── obstacle.py          # 게임 오브젝트
│   ├── config.py            # 설정 파일
│   ├── asset_paths.py       # 에셋 경로
│   └── *.py                # 기타 모듈
├── assets/  
│   ├── images/              # 이미지 에셋
│   │   ├── bubble_*.png    # 버블 이미지
│   │   ├── item_*.png      # 아이템 이미지
│   │   └── *.png           # 기타 이미지
│   ├── sounds/              # 사운드 파일
│   └── map_data/            # 맵 데이터 (CSV)
└── docs/                    # 문서
```

---

## 개발 가이드라인

### 1. 스케일링 시스템 사용

모든 UI 요소는 `SCALE` 변수를 사용하여 화면 크기에 대응해야 합니다:

```python
from config import SCALE

# 좋은 예
button_width = int(100 * SCALE)
offset_x = int(50 * SCALE)

# 나쁜 예
button_width = 100  # 하드코딩
```

### 2. 에셋 경로 관리

새 에셋 추가 시 `asset_paths.py`에 등록:

```python
ASSET_PATHS = {
    'new_asset': 'assets/images/new_asset.png',
}
```

### 3. 맵 에디터 개발

맵 파일은 CSV 형식으로 `assets/map_data/` 폴더에 저장:
- 파일명: `stage{숫자}.csv`
- 형식: 각 셀은 버블 코드 ('R', 'Y', 'B', 'G', 'N', '.')

### 4. Scene 패턴

새 Scene 추가 시:
1. `*_scene.py` 파일 생성 및 `run()` 메서드 구현
2. `scene_factory.py`에 Scene 등록
3. 다른 Scene에서 Scene 이름으로 전환

---

## 코드 스타일

- **들여쓰기**: 4칸 스페이스
- **함수/변수명**: snake_case
- **클래스명**: PascalCase
- **상수**: UPPER_CASE
- **타입 힌팅**: 가능한 경우 사용 권장

```python
def process_collision(bubble: Bubble, grid: HexGrid) -> bool:
    pass
```
