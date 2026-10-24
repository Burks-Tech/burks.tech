(function () {
  var root = document.documentElement;
  var prefersDark = window.matchMedia("(prefers-color-scheme: dark)");

  function isDark() {
    var set = root.getAttribute("data-theme");
    return set ? set === "dark" : prefersDark.matches;
  }

  var toggle = document.querySelector(".theme-toggle");
  if (toggle) {
    var label = function () {
      toggle.setAttribute("aria-label", isDark() ? "Switch to light theme" : "Switch to dark theme");
    };
    label();
    prefersDark.addEventListener("change", label);
    toggle.addEventListener("click", function () {
      var next = isDark() ? "light" : "dark";
      root.setAttribute("data-theme", next);
      try { localStorage.setItem("theme", next); } catch (e) {}
      label();
    });
  }

  if (navigator.clipboard) {
    document.querySelectorAll(".code").forEach(function (block) {
      var button = block.querySelector(".copy");
      var code = block.querySelector("pre code");
      if (!button || !code) return;
      button.hidden = false;
      button.addEventListener("click", function () {
        navigator.clipboard.writeText(code.innerText.replace(/\n$/, "")).then(function () {
          button.textContent = "Copied";
          setTimeout(function () { button.textContent = "Copy"; }, 1500);
        });
      });
    });
  }
})();
