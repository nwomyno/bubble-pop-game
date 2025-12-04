---

# Bubble Pop Game 

Python pygame 기반의 버블 슈터 게임

![Python](https://img.shields.io/badge/Python-3.11-blue.svg)
![Pygame](https://img.shields.io/badge/Pygame-2.5.2-green.svg)

---

## 빠른 시작 방법 

```bash
git clone https://github.com/gzntzz/bubble-pop-game.git
cd bubble-pop-game
pip install -r requirements.txt
python src/main.py
```

**매뉴 조작법**
- `↑ ↓` - 게임 or 맵 에디터 or 나가기 선택
- `Space` - 선택

**게임 조작법**:  
- `← →` - 각도 조절  
- `Space` - 버블 발사  
- `1 2 3` - 아이템 사용

**맵 에디터 조작법**:  
- 마우스 클릭 - 버블 선택 및배치  
- `ESC` - 메뉴로 복귀

---

## 주요 기능
<img width="1920" height="1108" alt="CleanShot 2025-12-04 at 23 14 22" src="https://github.com/user-attachments/assets/bd1bbb66-f085-476e-b372-d96c801a8744" />

### 🎮 핵심 게임플레이
- **육각형 격자 시스템**: 홀/짝 행 오프셋을 활용한 6방향 이웃 탐색
- **물리 엔진**: 발사 각도 계산 및 벽 반사 처리
- **DFS 알고리즘**: 같은 색 버블 3개 이상 매칭 시 제거
- **난이도 조절**: 4발마다 버블 덩어리 한 줄씩 하강
- **다단계 스테이지**: 점진적 난이도 증가

### 🎨 맵 에디터
- **통합 에디터**: 메뉴에서 직접 접근 가능
- **5가지 버블 타입**: R(빨강), Y(노랑), B(파랑), G(초록), N(장애물)
- **실시간 편집**: 마우스 드래그로 빠른 배치
- **스테이지 관리**: 저장, 불러오기, 삭제, 새로 만들기

### 💎 아이템 시스템
- **SWAP**: 현재 버블과 다음 버블 교환
- **RAISE**: 벽을 한 줄 위로 올림 (여유 공간 확보)
- **RAINBOW**: 현재 버블을 최적 색상으로 변환 (맵에 가장 많은 색)

### 🎯 반응형 UI
- **화면 크기 대응**: SCALE 시스템으로 모든 UI 요소 자동 조정
- **설정 가능한 레이아웃**: `config.py`에서 화면 크기 및 UI 위치 조정
- **이미지 에셋**: 버블, 캐릭터, 아이템 모두 이미지 지원

---

## 팀 구성 및 역할 

**기획**  
- **민기**: PM, 프로젝트 진행 주도, MVP 설정, 에셋 제작
- **준호**: 발표 자료(PPT, 대본) 제작, UI 피드백

**개발**  
- **건택**: 프로젝트 관리 및 리포지토리 구축, 메인 개발
- **민기**: 게임 로직 개발, 맵 에디터 및 UI 구현, 서브 개발

**디자인**  
- **예린**: UI/UX 디자인, 색상 팔레트, 레이아웃 설계
- **민기**: UI 레이아웃, 대지 세팅

자세한 내역은 [CONTRIBUTORS.md](CONTRIBUTORS.md)를 참고하세요.

---

## 프로젝트 구조 

```
bubble-pop-game/  
├── src/  
│   ├── main.py              # 게임 엔트리 포인트
│   ├── game.py              # 게임 메인 로직 (충돌, DFS, 아이템)
│   ├── map_editor.py        # 맵 에디터
│   ├── scene_manager.py     # Scene 전환 관리
│   ├── scene_factory.py     # Scene 생성 팩토리
│   ├── menu_scene.py        # 메뉴 Scene
│   ├── game_scene_wrapper.py  # 게임 Scene 래퍼
│   ├── editor_scene.py      # 에디터 Scene 래퍼
│   ├── obstacle.py          # 장애물 클래스
│   ├── config.py            # 게임 설정 (화면 크기, 스케일)
│   ├── asset_paths.py       # 에셋 경로 관리
│   ├── color_settings.py    # 색상 설정
│   ├── constants.py         # 상수 정의
│   └── game_settings.py     # 게임 설정값
├── assets/  
│   ├── images/              # 버블, 캐릭터, 배경, 아이템 이미지
│   ├── sounds/              # BGM 및 효과음
│   └── map_data/            # 스테이지 맵 파일 (CSV)
└── docs/                    # 프로젝트 문서
```

---

## 기술 스택

- **언어**: Python 3.11+
- **라이브러리**: Pygame 2.6+
- **알고리즘**: DFS (깊이 우선 탐색), 육각형 그리드 탐색
- **아키텍처**: Scene 패턴, Factory 패턴

---

## 설정 커스터마이징

`src/config.py`에서 다양한 설정을 조정할 수 있습니다:

```python
SCREEN_WIDTH = 1450          # 화면 가로 크기
NEXT_BUBBLE_X = 700          # NEXT 버블 X 좌표
NEXT_BUBBLE_Y_OFFSET = -80   # NEXT 버블 Y 오프셋
MAP_ROWS = 6                 # 맵 행 개수
MAP_COLS = 8                 # 맵 열 개수
```

모든 UI 요소는 SCALE에 따라 자동으로 조정됩니다.

---

**MIT License** | Made by **Team 언빌리버블**
