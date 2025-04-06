document.addEventListener("DOMContentLoaded", function () {
    // 🔽 Expand/Collapse Feature
    document.querySelectorAll(".read-more-btn").forEach(button => {
        button.addEventListener("click", function () {
            const textElement = this.previousElementSibling;
            const isExpanded = textElement.getAttribute("data-expanded") === "true";

            textElement.setAttribute("data-expanded", isExpanded ? "false" : "true");
            this.textContent = isExpanded ? "Read more" : "Read less";
        });
    });

    // Disable the confirmation prompt
    window.onbeforeunload = function () {
        return null;
    };
});
