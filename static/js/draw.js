(function () {
    const startBtn = document.getElementById("startDraw");
    const confirmBtn = document.getElementById("confirmDraw");
    const drumList = document.getElementById("drumList");
    const statusEl = document.getElementById("drawStatus");
    const drawForm = document.getElementById("drawForm");

    if (!startBtn || !drumList || !drawForm) return;

    const names = window.DRAW_NAMES || [];
    const drawUrl = drawForm.action;
    const itemHeight = 64;
    const totalItems = 40;
    const targetIndex = totalItems - 3;
    let spinning = false;

    function randomName(exclude) {
        const pool = exclude ? names.filter((n) => n !== exclude) : names;
        if (pool.length === 0) return exclude || names[0];
        return pool[Math.floor(Math.random() * pool.length)];
    }

    function buildSequence(winnerName) {
        const sequence = [];
        for (let i = 0; i < totalItems; i++) {
            sequence.push(randomName(winnerName));
        }
        sequence[targetIndex] = winnerName;
        return sequence;
    }

    function runAnimation(winnerName, firstPrize) {
        const sequence = buildSequence(winnerName);
        drumList.innerHTML = sequence.map((n) => `<li>${escapeHtml(n)}</li>`).join("");

        const offset = targetIndex * itemHeight;
        drumList.style.transition = "none";
        drumList.style.transform = "translateY(0)";

        requestAnimationFrame(() => {
            requestAnimationFrame(() => {
                drumList.style.transition = "transform 4s cubic-bezier(0.15, 0.85, 0.2, 1)";
                drumList.style.transform = `translateY(-${offset}px)`;
            });
        });

        setTimeout(() => {
            spinning = false;
            statusEl.innerHTML = `🎉 <strong>1 место:</strong> ${escapeHtml(winnerName)}<br><span class="draw-stage__prize">Приз: ${escapeHtml(firstPrize)}</span>`;
            confirmBtn.classList.remove("hidden");
        }, 4200);
    }

    function escapeHtml(text) {
        const el = document.createElement("div");
        el.textContent = text;
        return el.innerHTML;
    }

    startBtn.addEventListener("click", async () => {
        if (spinning || names.length === 0) return;
        spinning = true;
        startBtn.disabled = true;
        statusEl.textContent = "Проводим жеребьёвку…";

        try {
            const response = await fetch(drawUrl, {
                method: "POST",
                headers: { Accept: "application/json" },
            });
            const data = await response.json();

            if (!response.ok || !data.ok) {
                throw new Error(data.error || "Не удалось провести розыгрыш");
            }

            confirmBtn.href = data.results_url;
            statusEl.textContent = "Крутим барабан…";
            runAnimation(data.first_winner, data.first_prize);
        } catch (err) {
            spinning = false;
            startBtn.disabled = false;
            statusEl.textContent = err.message || "Ошибка розыгрыша";
        }
    });
})();
