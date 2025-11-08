# 기여 가이드

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
│   ├── main.py  
│   └── skeleton.py  
├── assets/  
│   ├── images/     # 이미지 파일  
│   └── sounds/     # 사운드 파일 (예정)  
└── docs/           # 문서 (예정)
```
