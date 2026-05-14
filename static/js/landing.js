/**
 * AESCULIA — Ivory & Moss (final)
 * Header, navigation mobile, révélations, compteurs easeOutExpo,
 * parallaxe, parcours auto-carrousel, créneaux, spy nav, barre de chargement.
 */
(function () {
  "use strict";

  var body = document.body;
  var reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  function ready(fn) {
    if (document.readyState !== "loading") fn();
    else document.addEventListener("DOMContentLoaded", fn);
  }

  ready(function () {
    initPageLoaderBar();
    requestAnimationFrame(function () {
      body.classList.add("aes-loaded");
    });

    initHeader();
    initNav();
    initNavSpy();
    initReveal();
    initCounters();
    initParallax();
    initJourneyCarousel();
    initSlots();
  });

  /** Barre de progression en tête de page au chargement */
  function initPageLoaderBar() {
    var bar = document.getElementById("page-loader-bar");
    if (!bar) return;
    requestAnimationFrame(function () {
      bar.style.width = "100%";
    });
    window.setTimeout(function () {
      bar.style.opacity = "0";
      window.setTimeout(function () {
        bar.style.visibility = "hidden";
      }, 400);
    }, 450);
  }

  function initHeader() {
    var el = document.getElementById("aes-header");
    if (!el) return;
    function tick() {
      if (window.scrollY > 24) el.classList.add("aes-header--shadow");
      else el.classList.remove("aes-header--shadow");
    }
    tick();
    window.addEventListener("scroll", tick, { passive: true });
  }

  function initNav() {
    var btn = document.getElementById("aes-nav-toggle");
    var overlay = document.getElementById("aes-nav-overlay");
    if (!btn || !overlay) return;

    function open(v) {
      overlay.hidden = !v;
      btn.setAttribute("aria-expanded", v ? "true" : "false");
      document.documentElement.style.overflow = v ? "hidden" : "";
    }

    btn.addEventListener("click", function () {
      open(overlay.hidden);
    });
    overlay.addEventListener("click", function (e) {
      if (e.target === overlay) open(false);
    });
    overlay.querySelectorAll("a").forEach(function (a) {
      a.addEventListener("click", function () {
        open(false);
      });
    });
  }

  /** Lien de nav actif : IntersectionObserver (bande centrale du viewport) */
  function initNavSpy() {
    var links = document.querySelectorAll("a[data-nav-section]");
    if (!links.length) return;

    var order = ["hero", "soins", "medecins", "parcours", "a-propos", "temoignages", "contact"];

    function setActive(id) {
      links.forEach(function (a) {
        a.classList.toggle("is-active", a.getAttribute("data-nav-section") === id);
      });
    }

    function pickFromScroll() {
      var y = window.scrollY + Math.min(140, window.innerHeight * 0.18);
      var current = order[0];
      order.forEach(function (id) {
        var el = document.getElementById(id);
        if (el && el.offsetTop <= y) current = id;
      });
      setActive(current);
    }

    if (!("IntersectionObserver" in window)) {
      pickFromScroll();
      window.addEventListener("scroll", pickFromScroll, { passive: true });
      window.addEventListener("resize", pickFromScroll);
      return;
    }

    var ratios = {};
    order.forEach(function (id) {
      ratios[id] = 0;
    });

    var io = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (entry) {
          ratios[entry.target.id] = entry.isIntersecting ? entry.intersectionRatio : 0;
        });
        var best = null;
        var bestRatio = 0;
        order.forEach(function (id) {
          var r = ratios[id] || 0;
          if (r > bestRatio) {
            bestRatio = r;
            best = id;
          }
        });
        if (bestRatio > 0) setActive(best);
        else pickFromScroll();
      },
      { root: null, rootMargin: "-40% 0px -40% 0px", threshold: [0, 0.05, 0.1, 0.2, 0.35, 0.5, 0.75, 1] }
    );

    order.forEach(function (id) {
      var el = document.getElementById(id);
      if (el) io.observe(el);
    });

    pickFromScroll();
    window.addEventListener("scroll", pickFromScroll, { passive: true });
    window.addEventListener("resize", pickFromScroll);
  }

  function initReveal() {
    var nodes = document.querySelectorAll("[data-reveal]");
    if (!nodes.length) return;

    if (!("IntersectionObserver" in window) || reduceMotion) {
      nodes.forEach(function (n) {
        n.classList.add("is-visible");
      });
      return;
    }

    var io = new IntersectionObserver(
      function (entries, obs) {
        entries.forEach(function (entry) {
          if (entry.isIntersecting) {
            entry.target.classList.add("is-visible");
            obs.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.15, rootMargin: "0px 0px -8% 0px" }
    );

    nodes.forEach(function (n) {
      io.observe(n);
    });
  }

  function formatInt(n) {
    return new Intl.NumberFormat("fr-FR").format(Math.round(n));
  }

  function easeOutExpo(t) {
    return t >= 1 ? 1 : 1 - Math.pow(2, -10 * t);
  }

  function animateCounter(el, target, duration) {
    var start = performance.now();
    function frame(now) {
      var u = Math.min((now - start) / duration, 1);
      var v = easeOutExpo(u);
      el.textContent = formatInt(v * target);
      if (u < 1) requestAnimationFrame(frame);
      else el.textContent = formatInt(target);
    }
    requestAnimationFrame(frame);
  }

  function initCounters() {
    var els = document.querySelectorAll(".js-counter");
    if (!els.length) return;

    if (!("IntersectionObserver" in window) || reduceMotion) {
      els.forEach(function (el) {
        el.textContent = formatInt(parseInt(el.getAttribute("data-target"), 10) || 0);
      });
      return;
    }

    var io = new IntersectionObserver(
      function (entries, obs) {
        entries.forEach(function (entry) {
          if (!entry.isIntersecting) return;
          var el = entry.target;
          var t = parseInt(el.getAttribute("data-target"), 10) || 0;
          el.textContent = formatInt(0);
          animateCounter(el, t, 2000);
          obs.unobserve(el);
        });
      },
      { threshold: 0.35 }
    );

    els.forEach(function (e) {
      io.observe(e);
    });
  }

  function initParallax() {
    if (reduceMotion) return;

    var heroRight = document.querySelector('[data-parallax="hero-right"]');
    var editorial = document.querySelector('[data-parallax="editorial-bg"]');
    var ctaBg = document.querySelector('[data-parallax="cta-bg"]');
    var reelStrip = document.querySelector('[data-parallax="reel-strip"]');
    var reelImgs = document.querySelectorAll("[data-parallax-child]");

    var ticking = false;

    function update() {
      ticking = false;
      var y = window.scrollY || 0;

      if (heroRight) {
        heroRight.style.transform = "translate3d(0, " + y * -0.15 + "px, 0)";
      }

      if (editorial) {
        var er = editorial.getBoundingClientRect();
        var eTop = y + er.top;
        var rel = y - eTop + window.innerHeight * 0.35;
        editorial.style.transform = "translate3d(0, " + rel * 0.4 + "px, 0)";
      }

      if (ctaBg) {
        var cr = ctaBg.getBoundingClientRect();
        var cTop = y + cr.top;
        var crel = y - cTop + window.innerHeight * 0.4;
        ctaBg.style.transform = "translate3d(0, " + crel * 0.5 + "px, 0)";
      }

      if (reelStrip) {
        var rr = reelStrip.getBoundingClientRect();
        var rTop = y + rr.top;
        var rrel = y - rTop;
        reelStrip.style.transform = "translate3d(0, " + rrel * -0.08 + "px, 0)";
        reelImgs.forEach(function (img) {
          img.style.transform = "translate3d(0, " + rrel * -0.2 + "px, 0)";
        });
      }
    }

    function onScroll() {
      if (!ticking) {
        ticking = true;
        requestAnimationFrame(update);
      }
    }

    window.addEventListener("scroll", onScroll, { passive: true });
    update();
  }

  /**
   * Parcours : une étape visible, auto-avance 4s, barre de progression,
   * pause au survol, points cliquables.
   */
  function initJourneyCarousel() {
    var section = document.querySelector(".journey-section");
    var steps = document.querySelectorAll(".journey-step");
    var dots = document.querySelectorAll(".journey-dots .dot");
    var fill = document.getElementById("journey-progress-fill");
    if (!section || !steps.length || !fill || !dots.length) return;

    var STEP_DURATION = 4000;
    var currentStep = 0;
    var autoTimer = null;

    function setDots(i) {
      dots.forEach(function (d, j) {
        var on = j === i;
        d.classList.toggle("active", on);
        d.setAttribute("aria-selected", on ? "true" : "false");
      });
    }

    function goToAbsolute(i) {
      i = ((i % steps.length) + steps.length) % steps.length;
      steps[currentStep].classList.remove("active");
      currentStep = i;
      steps[currentStep].classList.add("active");
      setDots(currentStep);
      resetProgress();
    }

    function resetProgress() {
      fill.style.transition = "none";
      fill.style.width = "0%";
      requestAnimationFrame(function () {
        requestAnimationFrame(function () {
          if (reduceMotion) {
            fill.style.width = "100%";
            return;
          }
          fill.style.transition = "width " + STEP_DURATION + "ms linear";
          fill.style.width = "100%";
        });
      });
    }

    function stopAutoPlay() {
      if (autoTimer) {
        clearInterval(autoTimer);
        autoTimer = null;
      }
      fill.style.transition = "none";
    }

    function startAutoPlay() {
      if (reduceMotion) return;
      stopAutoPlay();
      resetProgress();
      autoTimer = window.setInterval(function () {
        goToAbsolute(currentStep + 1);
      }, STEP_DURATION);
    }

    dots.forEach(function (dot, i) {
      dot.addEventListener("click", function () {
        stopAutoPlay();
        goToAbsolute(i);
        startAutoPlay();
      });
    });

    section.addEventListener("mouseenter", stopAutoPlay);
    section.addEventListener("mouseleave", startAutoPlay);

    if (!reduceMotion) {
      startAutoPlay();
    } else {
      fill.style.width = "100%";
    }
  }

  function initSlots() {
    document.querySelectorAll("[data-slot]").forEach(function (chip) {
      chip.addEventListener("click", function () {
        var root = chip.closest(".aes-hero__card-slots");
        if (!root) return;
        root.querySelectorAll("[data-slot]").forEach(function (c) {
          c.classList.remove("is-active");
        });
        chip.classList.add("is-active");
      });
    });
  }
})();
