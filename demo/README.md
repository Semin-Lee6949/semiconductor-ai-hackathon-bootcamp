# CMP Recipe Simulator Demo

교육용 합성 CMP 데이터로 다음 흐름을 보여주는 완성 예제입니다.

`CSV → 데이터 감사 → 기준모델/개선모델 → JSON → HTML/JS What-if → 의사결정`

## 실행

```bash
python -m pip install -r requirements.txt
python src/build_demo.py
python -m unittest discover -s tests -v
python -m http.server 8000 --directory docs
```

## 주의

모델과 추천 범위는 교육용입니다. 실제 CMP Recipe나 특정 회사의 공정 조건을 의미하지 않습니다.
