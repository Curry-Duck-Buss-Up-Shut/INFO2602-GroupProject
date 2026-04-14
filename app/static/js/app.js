function bindPasswordToggles(root = document) {
    root.querySelectorAll("[data-password-toggle]").forEach((button) => {
        if (button.dataset.passwordToggleBound === "true") return;

        const targetId = button.dataset.passwordTarget;
        const input = targetId ? document.getElementById(targetId) : null;
        const icon = button.querySelector(".material-symbols-outlined");
        if (!input || !icon) return;

        const showLabel = button.getAttribute("aria-label") || "Show password";
        const hideLabel = showLabel.replace(/^Show/i, "Hide");

        const syncPasswordToggleState = () => {
            const isVisible = input.type === "text";
            icon.textContent = isVisible ? "visibility_off" : "visibility";
            button.setAttribute("aria-label", isVisible ? hideLabel : showLabel);
            button.setAttribute("aria-pressed", String(isVisible));
        };

        button.addEventListener("click", () => {
            input.type = input.type === "password" ? "text" : "password";
            syncPasswordToggleState();
            input.focus({ preventScroll: true });
        });

        button.dataset.passwordToggleBound = "true";
        syncPasswordToggleState();
    });
}

async function getUserData() {
    const response = await fetch("/api/users");
    return response.json();
}

function loadTable(users) {
    const table = document.querySelector("#result");
    if (!table) return;

    for (const user of users) {
        table.innerHTML += `<tr>
            <td>${user.id}</td>
            <td>${user.username}</td>
        </tr>`;
    }
}

async function main() {
    bindPasswordToggles();

    if (!document.querySelector("#result")) return;

    const users = await getUserData();
    loadTable(users);
}

window.StormScopeApp = {
    bindPasswordToggles,
};

main();
