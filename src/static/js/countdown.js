/* Renders a live countdown to the wedding date into #countdown.
 *
 * The target datetime is supplied server-side via the data-wedding-datetime
 * attribute (local time, ISO-like "YYYY-MM-DDTHH:MM:SS"). Without JS the
 * <noscript> fallback in the template is shown instead.
 */
(function () {
  "use strict";

  var UNITS = [
    { key: "days", label: "Dagar" },
    { key: "hours", label: "Timmar" },
    { key: "minutes", label: "Minuter" },
    { key: "seconds", label: "Sekunder" },
  ];

  var MS_PER_SECOND = 1000;
  var MS_PER_MINUTE = MS_PER_SECOND * 60;
  var MS_PER_HOUR = MS_PER_MINUTE * 60;
  var MS_PER_DAY = MS_PER_HOUR * 24;

  function breakdown(remainingMs) {
    return {
      days: Math.floor(remainingMs / MS_PER_DAY),
      hours: Math.floor((remainingMs % MS_PER_DAY) / MS_PER_HOUR),
      minutes: Math.floor((remainingMs % MS_PER_HOUR) / MS_PER_MINUTE),
      seconds: Math.floor((remainingMs % MS_PER_MINUTE) / MS_PER_SECOND),
    };
  }

  function buildMarkup(container) {
    var list = document.createElement("ul");
    list.className = "wed-countdown";
    list.setAttribute("aria-live", "off");

    var values = {};
    UNITS.forEach(function (unit) {
      var item = document.createElement("li");
      item.className = "wed-countdown__item";

      var value = document.createElement("span");
      value.className = "wed-countdown__value";
      value.textContent = "\u2013";

      var label = document.createElement("span");
      label.className = "wed-countdown__label";
      label.textContent = unit.label;

      item.appendChild(value);
      item.appendChild(label);
      list.appendChild(item);
      values[unit.key] = value;
    });

    container.appendChild(list);
    return { list: list, values: values };
  }

  function showMessage(container, text) {
    container.innerHTML = "";
    var message = document.createElement("p");
    message.className = "wed-countdown__message";
    message.textContent = text;
    container.appendChild(message);
  }

  function init() {
    var container = document.getElementById("countdown");
    if (!container) {
      return;
    }

    var raw = container.getAttribute("data-wedding-datetime");
    if (!raw) {
      return;
    }

    var target = new Date(raw).getTime();
    if (isNaN(target)) {
      return;
    }

    if (target - Date.now() <= 0) {
      showMessage(container, "Stora dagen \u00e4r h\u00e4r \u2013 vi ses p\u00e5 br\u00f6llopet!");
      return;
    }

    var rendered = buildMarkup(container);

    var tick = function () {
      var remaining = target - Date.now();
      if (remaining <= 0) {
        window.clearInterval(timer);
        showMessage(container, "Stora dagen \u00e4r h\u00e4r \u2013 vi ses p\u00e5 br\u00f6llopet!");
        return;
      }

      var parts = breakdown(remaining);
      UNITS.forEach(function (unit) {
        rendered.values[unit.key].textContent = String(parts[unit.key]);
      });
    };

    var timer = window.setInterval(tick, MS_PER_SECOND);
    tick();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
