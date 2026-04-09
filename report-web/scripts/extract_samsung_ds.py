#!/usr/bin/env python
"""Extract Samsung DS recruitment rows from PDF files and update sample-data.json.

Usage:
  python report-web/scripts/extract_samsung_ds.py \
    --pdf-dir "삼성전자 DS" \
    --target "report-web/data/sample-data.json"
"""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from pypdf import PdfReader

LOCATION_WORDS = ["기흥", "화성", "평택", "천안", "온양", "수원"]
LOCATION_RE = "|".join(LOCATION_WORDS)
MAJOR_HINTS = [
    "전기전자",
    "재료",
    "금속",
    "화학",
    "화공",
    "기계",
    "물리",
    "전산",
    "컴퓨터",
    "산공",
    "수학",
    "통계",
    "환경",
    "안전",
    "건축",
    "토목",
    "상경",
    "이공기타",
]

ROW_PATTERN = re.compile(
    rf"^(?P<position>[가-힣A-Za-z0-9&/_().+\-\s]{{2,45}})\s+"
    rf"(?P<major>.+?)\s+"
    rf"(?P<region>(?:{LOCATION_RE})(?:\s*,\s*(?:{LOCATION_RE}))*)$"
)

SKIP_PREFIXES = (
    "202",
    "삼성전자",
    "사업부",
    "모집전공",
    "근무지",
    "채용",
    "전형",
    "지원",
)


@dataclass(frozen=True)
class Posting:
    company: str
    year: int
    category: str
    position: str
    region: str
    skills: list[str]
    process: list[str]
    description: str

    def as_dict(self) -> dict:
        return {
            "company": self.company,
            "year": self.year,
            "category": self.category,
            "position": self.position,
            "region": self.region,
            "skills": self.skills,
            "process": self.process,
            "description": self.description,
        }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pdf-dir", required=True, type=Path)
    parser.add_argument("--target", required=True, type=Path)
    parser.add_argument("--company", default="삼성전자 DS")
    return parser.parse_args()


def normalize_line(line: str) -> str:
    return re.sub(r"\s+", " ", line).strip()


def infer_half(path: Path) -> str:
    name = path.name
    if "상반기" in name:
        return "상반기"
    if "하반기" in name:
        return "하반기"
    return "연간"


def infer_year(path: Path) -> int:
    match = re.search(r"(20\d{2})", path.name)
    if not match:
        raise ValueError(f"연도를 파일명에서 찾지 못했습니다: {path}")
    return int(match.group(1))


def infer_category(position: str) -> str:
    p = position.lower()
    if any(key in p for key in ["sw", "ai", "소프트웨어", "개발", "data", "데이터"]):
        return "SW"
    if any(key in p for key in ["회로", "설계", "신호", "아키텍처"]):
        return "반도체설계"
    if any(key in p for key in ["재무", "경영", "지원"]):
        return "경영지원"
    if any(key in p for key in ["생산", "공정", "설비", "평가", "분석", "인프라", "환경"]):
        return "공정기술"
    return "기타"


def parse_skills(position: str, major_text: str, category: str) -> list[str]:
    major_tokens = [
        token.strip()
        for token in re.split(r"[,/]", major_text)
        if token.strip() and token.strip() not in {"이공기타", "상경 * 부전공 포함"}
    ]

    seed: list[str] = []
    if category == "SW":
        seed.extend(["Python", "데이터분석"])
    elif category == "반도체설계":
        seed.extend(["회로설계", "검증"])
    elif category == "공정기술":
        seed.extend(["공정개선", "데이터해석"])
    elif category == "경영지원":
        seed.extend(["재무분석", "커뮤니케이션"])

    if "통계" in major_text and "통계분석" not in seed:
        seed.append("통계분석")
    if "전산" in major_text and "SW개발" not in seed:
        seed.append("SW개발")

    cleaned = []
    seen = set()
    for token in [*seed, *major_tokens]:
        compact = re.sub(r"\(.*?\)", "", token).strip()
        compact = compact.replace("전기전자", "전기전자공학")
        if not compact or compact in seen:
            continue
        seen.add(compact)
        cleaned.append(compact)

    return cleaned[:4] if cleaned else ["문제해결", "협업"]


def detect_process(full_text: str) -> list[str]:
    steps = ["서류"]
    if "직무적성" in full_text or "GSAT" in full_text:
        steps.append("직무적성")
    if "코딩테스트" in full_text:
        steps.append("코딩테스트")
    if "면접" in full_text:
        steps.append("기술면접")
    if "면접" in full_text:
        steps.append("최종면접")
    return list(dict.fromkeys(steps))


def extract_lines_from_pdf(pdf_path: Path) -> tuple[list[str], str]:
    reader = PdfReader(str(pdf_path))
    text_chunks = []
    lines: list[str] = []

    for page_index, page in enumerate(reader.pages):
        text = page.extract_text() or ""
        text_chunks.append(text)
        # The recruitment summary tables are usually placed in the first few pages.
        if page_index < 8:
            lines.extend(text.splitlines())

    return [normalize_line(line) for line in lines if normalize_line(line)], "\n".join(text_chunks)


def row_candidates(lines: Iterable[str]) -> Iterable[tuple[str, str, str]]:
    for line in lines:
        if len(line) < 10:
            continue
        if line.startswith(SKIP_PREFIXES):
            continue
        if "사업부" in line and "직무" in line and "근무지" in line:
            continue

        match = ROW_PATTERN.match(line)
        if not match:
            continue

        position = normalize_line(match.group("position"))
        major = normalize_line(match.group("major"))
        region = normalize_line(match.group("region"))

        if position in {"사업부", "부문공통"}:
            continue
        if position in LOCATION_WORDS:
            continue
        if position.endswith("도") or position.endswith("시"):
            continue
        if not any(hint in major for hint in MAJOR_HINTS):
            continue
        if len(position) > 35 or len(major) < 2:
            continue

        yield position, major, region


def extract_from_pdf(pdf_path: Path, company: str) -> list[Posting]:
    year = infer_year(pdf_path)
    half = infer_half(pdf_path)

    lines, full_text = extract_lines_from_pdf(pdf_path)
    process = detect_process(full_text)

    postings: list[Posting] = []
    seen = set()

    for position, major, region_text in row_candidates(lines):
        region = region_text.split(",")[0].strip()
        category = infer_category(position)
        skills = parse_skills(position, major, category)

        key = (year, position, region)
        if key in seen:
            continue
        seen.add(key)

        postings.append(
            Posting(
                company=company,
                year=year,
                category=category,
                position=position,
                region=region,
                skills=skills,
                process=process,
                description=f"{year}년 {half} 공고 기반 자동 추출",
            )
        )

    return postings


def load_json(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig") as f:
        return json.load(f)


def save_json(path: Path, data: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def main() -> None:
    args = parse_args()

    pdf_files = sorted(args.pdf_dir.glob("*.pdf"))
    if not pdf_files:
        raise SystemExit(f"PDF 파일이 없습니다: {args.pdf_dir}")

    extracted: list[Posting] = []
    for pdf in pdf_files:
        extracted.extend(extract_from_pdf(pdf, args.company))

    deduped: dict[tuple[int, str, str, str], Posting] = {}
    for row in extracted:
        key = (row.year, row.category, row.position, row.region)
        deduped[key] = row

    extracted_dicts = [p.as_dict() for p in deduped.values()]
    extracted_dicts.sort(key=lambda x: (x["year"], x["category"], x["position"], x["region"]))

    existing = load_json(args.target)
    others = [row for row in existing if row.get("company") != args.company]

    merged = [*others, *extracted_dicts]
    merged.sort(key=lambda x: (x.get("company", ""), x.get("year", 0), x.get("category", ""), x.get("position", "")))
    save_json(args.target, merged)

    print(f"PDF {len(pdf_files)}개 처리 완료")
    print(f"추출 공고 {len(extracted_dicts)}건")
    print(f"저장 파일: {args.target}")


if __name__ == "__main__":
    main()
