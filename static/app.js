const form = document.querySelector("#risk-form");
const score = document.querySelector("#score");
const level = document.querySelector("#level");
const summary = document.querySelector("#summary");
const breakdown = document.querySelector("#breakdown");
const recommendations = document.querySelector("#recommendations");
const uncertainty = document.querySelector("#uncertainty");

function list(target, items) {
  target.innerHTML = "";
  for (const item of items) {
    const li = document.createElement("li");
    li.textContent = item;
    target.appendChild(li);
  }
}

function render(data) {
  score.textContent = data.risk_score;
  level.textContent = data.risk_level;
  summary.textContent = data.summary;
  breakdown.innerHTML = "";

  for (const [name, bucket] of Object.entries(data.breakdown)) {
    const row = document.createElement("div");
    row.className = "bucket";
    row.innerHTML = `
      <strong>${name}</strong>
      <span class="meter"><i style="width:${bucket.score}%"></i></span>
      <span>${bucket.score}</span>
    `;
    row.title = bucket.explanation;
    breakdown.appendChild(row);
  }

  list(recommendations, data.recommendations);
  list(uncertainty, data.uncertainty);
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const fd = new FormData(form);
  const payload = {
    marketplace: fd.get("marketplace"),
    title: fd.get("title"),
    description: fd.get("description"),
    brand: fd.get("brand"),
    category: fd.get("category"),
    image_urls: String(fd.get("image_urls") || "")
      .split(",")
      .map((item) => item.trim())
      .filter(Boolean),
    seller_context: fd.get("seller_context"),
  };

  const response = await fetch("/api/risk/check", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  render(await response.json());
});
