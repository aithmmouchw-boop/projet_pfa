/**
 * AESCULIA — pages d'authentification (toggle mot de passe, chargement, ripple).
 */
(function () {
  "use strict";

  function ready(fn) {
    if (document.readyState !== "loading") fn();
    else document.addEventListener("DOMContentLoaded", fn);
  }

  ready(function () {
    var shell = document.querySelector("[data-auth-shell]");
    if (shell) {
      requestAnimationFrame(function () {
        shell.classList.add("is-ready");
      });
    }

    document.querySelectorAll("[data-toggle-password]").forEach(function (btn) {
      btn.addEventListener("click", function () {
        var wrap = btn.closest(".input-wrapper");
        var input = wrap && wrap.querySelector("input");
        if (!input) return;
        var show = input.type === "password";
        input.type = show ? "text" : "password";
        btn.setAttribute(
          "aria-label",
          show ? "Masquer le mot de passe" : "Afficher le mot de passe"
        );
      });
    });

    document.querySelectorAll(".field-group--float").forEach(function (group) {
      var inp = group.querySelector("input, select, textarea");
      if (!inp) return;
      function sync() {
        if (inp.value) group.classList.add("has-value");
        else group.classList.remove("has-value");
      }
      inp.addEventListener("input", sync);
      inp.addEventListener("change", sync);
      sync();
    });

    document.querySelectorAll("[data-auth-register-form]").forEach(function (form) {
      var role = form.querySelector("select[name='role']");
      var sections = form.querySelectorAll("[data-role-fields]");
      if (!role || !sections.length) return;

      function syncRoleFields() {
        sections.forEach(function (section) {
          var visible = section.getAttribute("data-role-fields") === role.value;
          section.hidden = !visible;
          section.querySelectorAll("input, select, textarea").forEach(function (field) {
            field.disabled = !visible;
          });
        });
      }

      role.addEventListener("change", syncRoleFields);
      syncRoleFields();
    });

    document.querySelectorAll("[data-auth-form]").forEach(function (form) {
      form.addEventListener("submit", function () {
        var btn = form.querySelector("[data-login-submit]");
        if (btn && btn.type === "submit") {
          btn.classList.add("is-loading");
          btn.disabled = true;
        }
      });
    });

    document.querySelectorAll(".btn-login").forEach(function (btn) {
      btn.addEventListener("click", function () {
        if (btn.tagName === "A" || btn.getAttribute("href")) return;
        btn.classList.remove("ripple");
        void btn.offsetWidth;
        btn.classList.add("ripple");
        window.setTimeout(function () {
          btn.classList.remove("ripple");
        }, 550);
      });
    });
  });
})();
