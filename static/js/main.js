document.addEventListener("DOMContentLoaded", () => {
    document.querySelectorAll(".flash").forEach((el) => {
        setTimeout(() => {
            el.style.opacity = "0";
            el.style.transform = "translateY(-8px)";
            el.style.transition = "opacity 0.4s, transform 0.4s";
            setTimeout(() => el.remove(), 400);
        }, 5000);
    });

    document.querySelectorAll("[data-copy-target]").forEach((btn) => {
        btn.addEventListener("click", async () => {
            const input = document.getElementById(btn.dataset.copyTarget);
            if (!input) return;
            try {
                await navigator.clipboard.writeText(input.value);
                const label = btn.textContent;
                btn.textContent = "Скопировано!";
                setTimeout(() => { btn.textContent = label; }, 2000);
            } catch {
                input.select();
                document.execCommand("copy");
            }
        });
    });
});