const ids = ["down_force", "platen_speed", "slurry_flow", "pad_age", "pattern_density"];
let model;

const value = (id) => Number(document.getElementById(id).value);
const show = (id, text) => { document.getElementById(id).textContent = text; };

function predictRemoval() {
  const c = model.coefficients;
  const x = Object.fromEntries(ids.map((id) => [id, value(id)]));
  return c.intercept + c.down_force * x.down_force + c.platen_speed * x.platen_speed
    + c.slurry_flow * x.slurry_flow + c.pad_age * x.pad_age
    + c.pattern_density * x.pattern_density
    + c.slurry_x_density * x.slurry_flow * x.pattern_density
    + c.pad_age_squared * x.pad_age ** 2;
}

function update() {
  ids.forEach((id) => show(`${id}_value`, value(id).toFixed(id === "pattern_density" ? 2 : 1)));
  if (!model?.coefficients) return;
  const removal = predictRemoval();
  const pad = value("pad_age");
  const density = value("pattern_density");
  const wiwnu = 2.4 + Math.abs(value("down_force") - 3.2) * 1.2 + pad / 65 + density * 1.8;
  const dishing = Math.min(99, Math.max(2, 12 + (value("down_force") - 2) * 13 + density * 28 - value("slurry_flow") / 16));
  const pass = removal >= 285 && removal <= 345 && wiwnu < 6.2 && dishing < 60;
  show("removal_rate", removal.toFixed(1));
  show("wiwnu", wiwnu.toFixed(2));
  show("dishing", `${dishing.toFixed(0)}%`);
  show("decision", pass ? "PASS" : "REVIEW");
  show("recommendation", pass ? "현재 교육용 Window 안입니다." : "Pad Age·압력·유량의 보수적 조정을 검토하세요.");
}

async function boot() {
  try {
    const [modelResponse, metricsResponse] = await Promise.all([
      fetch("artifacts/model_params.json"), fetch("artifacts/metrics.json")
    ]);
    model = await modelResponse.json();
    const metrics = await metricsResponse.json();
    if (!model.coefficients) throw new Error("Run build_demo.py first");
    show("baseline_rmse", metrics.baseline_rmse);
    show("improved_rmse", metrics.improved_rmse);
    show("holdout_rows", metrics.holdout_rows);
    show("audit", `${metrics.audit.missing} missing · ${metrics.audit.duplicates} duplicate`);
    ids.forEach((id) => document.getElementById(id).addEventListener("input", update));
    update();
  } catch (error) {
    show("recommendation", `Build required: ${error.message}`);
  }
}

boot();
