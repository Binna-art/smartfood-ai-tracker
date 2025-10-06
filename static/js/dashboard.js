document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("uploadForm");
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const data = new FormData(form);
    const res = await fetch("/upload", { method: "POST", body: data });
    const out = await res.json();
    document.getElementById("result").innerHTML = `
      <h3>${out.food}</h3>
      <p>${out.calories} Calories</p>
      <p>${out.message}</p>`;
  });
});
