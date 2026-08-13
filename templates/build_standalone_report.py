"""PNG 그래프를 Base64로 내장한 독립형 index.html 보고서 골격."""

import base64
import html
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "portfolio" / "index.html"
FIGURE = ROOT / "outputs" / "main_figure.png"


def image_data_uri(path: Path) -> str:
    if not path.exists():
        return ""
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:image/png;base64,{encoded}"


problem = "TODO: 누가 어떤 데이터를 보고 어떤 결정을 내려야 하는가?"
discussion = "TODO: 전공지식, 대안 가설, 반증 결과와 적용 한계를 작성한다."
figure = image_data_uri(FIGURE)
figure_html = f'<img src="{figure}" alt="핵심 분석 그래프">' if figure else "<p>outputs/main_figure.png를 만든 뒤 다시 실행하세요.</p>"

document = f"""<!doctype html>
<html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Semiconductor AI Project Report</title>
<style>body{{max-width:900px;margin:auto;padding:40px 20px;font:17px/1.7 system-ui;color:#101b2d}}img{{max-width:100%}}code{{background:#eef2f1;padding:2px 5px}}</style></head>
<body><h1>반도체 AI 프로젝트 보고서</h1><h2>문제</h2><p>{html.escape(problem)}</p>
<h2>분석 결과</h2>{figure_html}<h2>Discussion</h2><p>{html.escape(discussion)}</p>
<h2>재현</h2><p>README.md의 실행법과 Streamlit URL을 연결하세요.</p></body></html>"""

OUTPUT.parent.mkdir(parents=True, exist_ok=True)
OUTPUT.write_text(document, encoding="utf-8")
print(f"Wrote {OUTPUT}")
