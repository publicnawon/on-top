const companySelect = document.getElementById("companySelect");
const yearSelect = document.getElementById("yearSelect");
const jobCategorySelect = document.getElementById("jobCategorySelect");
const regionSelect = document.getElementById("regionSelect");
const keywordInput = document.getElementById("keywordInput");

const totalCount = document.getElementById("totalCount");
const topCategory = document.getElementById("topCategory");
const topSkill = document.getElementById("topSkill");
const commonStage = document.getElementById("commonStage");

const trendTableBody = document.getElementById("trendTableBody");
const strategySummary = document.getElementById("strategySummary");
const recommendationList = document.getElementById("recommendationList");
const trendNote = document.getElementById("trendNote");
const competencyNote = document.getElementById("competencyNote");
const copyReportBtn = document.getElementById("copyReportBtn");

let rawData = [];

async function init() {
  const response = await fetch("./data/sample-data.json");
  rawData = await response.json();

  bindEvents();
  populateFilters();
  updateView();
}

function bindEvents() {
  companySelect.addEventListener("change", onCompanyChange);
  yearSelect.addEventListener("change", updateView);
  jobCategorySelect.addEventListener("change", updateView);
  regionSelect.addEventListener("change", updateView);
  keywordInput.addEventListener("input", updateView);
  copyReportBtn.addEventListener("click", copyReport);
}

function populateFilters() {
  const companies = uniqueValues(rawData, "company");
  companySelect.innerHTML = companies.map((company) => `<option value="${company}">${company}</option>`).join("");

  populateYearByCompany();
  populateCategoryByCompany();
  populateRegionByCompany();
}

function onCompanyChange() {
  populateYearByCompany();
  populateCategoryByCompany();
  populateRegionByCompany();
  updateView();
}

function populateYearByCompany() {
  const company = companySelect.value;
  const years = uniqueValues(
    rawData.filter((item) => item.company === company),
    "year"
  ).sort((a, b) => b - a);

  yearSelect.innerHTML = years.map((year) => `<option value="${year}">${year}</option>`).join("");
}

function populateCategoryByCompany() {
  const company = companySelect.value;
  const categories = uniqueValues(
    rawData.filter((item) => item.company === company),
    "category"
  );

  jobCategorySelect.innerHTML = ["all", ...categories]
    .map((category) => `<option value="${category}">${category === "all" ? "전체" : category}</option>`)
    .join("");
}

function populateRegionByCompany() {
  const company = companySelect.value;
  const regions = uniqueValues(
    rawData.filter((item) => item.company === company),
    "region"
  );

  regionSelect.innerHTML = ["all", ...regions]
    .map((region) => `<option value="${region}">${region === "all" ? "전체" : region}</option>`)
    .join("");
}

function uniqueValues(items, key) {
  return [...new Set(items.map((item) => item[key]))];
}

function filterData() {
  const company = companySelect.value;
  const baseYear = Number(yearSelect.value);
  const category = jobCategorySelect.value;
  const region = regionSelect.value;
  const keyword = keywordInput.value.trim().toLowerCase();

  const targetYears = [baseYear - 2, baseYear - 1, baseYear];

  return rawData.filter((item) => {
    const matchCompany = item.company === company;
    const matchYear = targetYears.includes(item.year);
    const matchCategory = category === "all" || item.category === category;
    const matchRegion = region === "all" || item.region === region;
    const fullText = [item.position, item.description, item.skills.join(" "), item.process.join(" ")]
      .join(" ")
      .toLowerCase();
    const matchKeyword = keyword === "" || fullText.includes(keyword);

    return matchCompany && matchYear && matchCategory && matchRegion && matchKeyword;
  });
}

function updateView() {
  const items = filterData();

  updateKpi(items);
  updateTrendTable(items);
  updateNarrative(items);
}

function updateKpi(items) {
  totalCount.textContent = String(items.length);

  if (!items.length) {
    topCategory.textContent = "-";
    topSkill.textContent = "-";
    commonStage.textContent = "-";
    return;
  }

  const categoryCount = countBy(items, "category");
  const skillCount = countNested(items, "skills");
  const processCount = countNested(items, "process");

  topCategory.textContent = topKey(categoryCount);
  topSkill.textContent = topKey(skillCount);
  commonStage.textContent = topKey(processCount);
}

function updateTrendTable(items) {
  trendTableBody.innerHTML = "";

  if (!items.length) {
    trendTableBody.innerHTML = "<tr><td colspan='4'>조건에 맞는 공고가 없습니다.</td></tr>";
    return;
  }

  const years = [...new Set(items.map((item) => item.year))].sort((a, b) => a - b);

  trendTableBody.innerHTML = years
    .map((year) => {
      const yearItems = items.filter((item) => item.year === year);
      const yearCategory = topKey(countBy(yearItems, "category"));
      const yearSkill = topKey(countNested(yearItems, "skills"));
      return `<tr>
        <td>${year}</td>
        <td>${yearItems.length}</td>
        <td>${yearCategory}</td>
        <td>${yearSkill}</td>
      </tr>`;
    })
    .join("");
}

function updateNarrative(items) {
  if (!items.length) {
    strategySummary.textContent = "현재 조건에서 분석 가능한 공고가 없어 전략을 생성할 수 없습니다. 조건을 완화해 다시 확인해 주세요.";
    recommendationList.innerHTML = "<li>기업/연도/직무/키워드 조건을 단계적으로 줄여 표본 수를 확보하세요.</li>";
    trendNote.textContent = "데이터가 부족한 구간은 추세 해석보다 표본 확장이 우선입니다.";
    competencyNote.textContent = "최소 10건 이상 표본을 확보한 뒤 역량 우선순위를 고정하는 것을 권장합니다.";
    return;
  }

  const company = companySelect.value;
  const baseYear = Number(yearSelect.value);
  const years = [baseYear - 2, baseYear - 1, baseYear];

  const categoryCount = countBy(items, "category");
  const skillCount = countNested(items, "skills");
  const processCount = countNested(items, "process");
  const regionCount = countBy(items, "region");

  const top3Skills = sortedKeys(skillCount).slice(0, 3);
  const majorCategory = topKey(categoryCount);
  const majorProcess = topKey(processCount);
  const majorRegion = topKey(regionCount);

  strategySummary.textContent = `${company}의 ${years[0]}-${years[2]} 채용공고를 기준으로 보면 '${majorCategory}' 직무 비중이 가장 높고, '${top3Skills.join(", ")}' 역량이 반복적으로 요구됩니다. 컨설팅에서는 직무별 프로젝트 경험을 위 역량과 1:1로 매핑해 자기소개서 사례를 재구성하는 전략이 효과적입니다.`;

  recommendationList.innerHTML = [
    `핵심 역량 상위 3개(${top3Skills.join(", ")})를 중심으로 이력서 기술 스택 섹션을 재배열하세요.`,
    `가장 빈도가 높은 전형 단계('${majorProcess}')를 기준으로 예상 질문 풀과 답변 구조를 미리 고정하세요.`,
    `채용 비중이 높은 지역('${majorRegion}') 기준으로 근무지 선호도와 배치 가능성을 상담 초기부터 명확히 정리하세요.`,
    `주요 직무군('${majorCategory}')에 맞는 최근 2개 프로젝트를 성과 지표 중심으로 재작성해 제출 문서에 반영하세요.`
  ]
    .map((text) => `<li>${text}</li>`)
    .join("");

  const yearlyCounts = years.map((year) => items.filter((item) => item.year === year).length);
  const trendDirection = yearlyCounts[2] >= yearlyCounts[0] ? "확대" : "축소";

  trendNote.textContent = `3개년 공고 수는 ${years[0]}년 ${yearlyCounts[0]}건, ${years[1]}년 ${yearlyCounts[1]}건, ${years[2]}년 ${yearlyCounts[2]}건으로 ${trendDirection} 흐름입니다. 컨설팅 시 최근 연도 공고의 직무 요건 가중치를 높여 포지셔닝하는 것이 유리합니다.`;
  competencyNote.textContent = `우선 준비 역량: ${top3Skills.join(" > ")} (상위 빈도 순). 면접 대비는 '${majorProcess}' 단계 기준으로 질문-근거-성과 3단 구조를 권장합니다.`;
}

function countBy(items, key) {
  return items.reduce((acc, item) => {
    const value = item[key];
    acc[value] = (acc[value] || 0) + 1;
    return acc;
  }, {});
}

function countNested(items, key) {
  return items.reduce((acc, item) => {
    item[key].forEach((value) => {
      acc[value] = (acc[value] || 0) + 1;
    });
    return acc;
  }, {});
}

function sortedKeys(obj) {
  return Object.keys(obj).sort((a, b) => obj[b] - obj[a]);
}

function topKey(obj) {
  const keys = sortedKeys(obj);
  return keys.length ? keys[0] : "-";
}

function buildReportText() {
  const recommendations = [...recommendationList.querySelectorAll("li")]
    .map((item) => `- ${item.textContent}`)
    .join("\n");

  return [
    "[대기업 채용공고 분석 리포트]",
    `기업: ${companySelect.value}`,
    `기준 연도: ${yearSelect.value}`,
    `직무 카테고리: ${jobCategorySelect.value === "all" ? "전체" : jobCategorySelect.value}`,
    `지역: ${regionSelect.value === "all" ? "전체" : regionSelect.value}`,
    `공고 수: ${totalCount.textContent}`,
    `최다 직무군: ${topCategory.textContent}`,
    `최다 요구 역량: ${topSkill.textContent}`,
    `대표 전형 단계: ${commonStage.textContent}`,
    "",
    `[요약 전략] ${strategySummary.textContent}`,
    "",
    "[실행 권고안]",
    recommendations,
    "",
    `[트렌드 노트] ${trendNote.textContent}`,
    `[역량 노트] ${competencyNote.textContent}`
  ].join("\n");
}

async function copyReport() {
  const reportText = buildReportText();
  await navigator.clipboard.writeText(reportText);

  copyReportBtn.textContent = "복사 완료";
  setTimeout(() => {
    copyReportBtn.textContent = "리포트 복사";
  }, 1400);
}

init();
