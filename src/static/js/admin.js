/* Generic runner for the admin page's registry-driven actions.
 *
 * Every <form data-admin-action> rendered from pages/admin/sections.py is
 * wired up here; nothing in this file is specific to any one endpoint.
 * Each form carries its HTTP method and URL template in data-* attributes,
 * and each input declares whether it fills a URL path parameter
 * (data-location="path") or a JSON body key (data-location="body").
 */
(function () {
  "use strict";

  var script = document.currentScript;
  var LOGIN_URL = script.dataset.loginUrl;
  var LOGOUT_URL = script.dataset.logoutUrl;
  var REDIRECT_DELAY_MS = 1800;
  var CONFIRM_WINDOW_MS = 4000;
  var BODY_METHODS = { POST: true, PUT: true };

  function setStatus(element, message, variant) {
    element.classList.remove("wed-admin-status-error", "wed-admin-status-busy");
    if (!message) {
      element.classList.add("d-none");
      element.textContent = "";
      return;
    }
    if (variant) {
      element.classList.add("wed-admin-status-" + variant);
    }
    element.textContent = message;
    element.classList.remove("d-none");
  }

  function hideOutput(output) {
    output.classList.add("d-none");
    output.classList.remove("wed-admin-output-enter");
    output.textContent = "";
  }

  // Replay the "materialize" entrance so repeated runs animate again.
  function showOutput(output, data) {
    output.textContent = JSON.stringify(data, null, 2);
    output.classList.remove("d-none", "wed-admin-output-enter");
    void output.offsetWidth;
    output.classList.add("wed-admin-output-enter");
  }

  function fieldsOf(form) {
    return Array.prototype.slice.call(form.querySelectorAll("[data-location]"));
  }

  function buildUrl(template, form) {
    var url = template;
    fieldsOf(form).forEach(function (input) {
      if (input.dataset.location === "path") {
        url = url.replace("{" + input.name + "}", encodeURIComponent(input.value.trim()));
      }
    });
    return url;
  }

  // Blank values are omitted entirely, so update actions only change what
  // was filled in. A checkbox has no "unset" state, so it is always sent.
  function readBodyValue(input) {
    var type = input.dataset.type;
    if (type === "bool") {
      return { present: true, value: input.checked };
    }
    var raw = input.value.trim();
    if (raw === "") {
      return { present: false };
    }
    if (type === "integer") {
      return { present: true, value: Number(raw) };
    }
    if (type === "tri_bool") {
      return { present: true, value: raw === "true" };
    }
    if (type === "list") {
      return { present: true, value: parseList(raw) };
    }
    return { present: true, value: raw };
  }

  // "1,2,3" and "1, 2, 3" both become [1, 2, 3]; non-numeric items stay strings.
  function parseList(raw) {
    return raw
      .split(",")
      .map(function (item) {
        return item.trim();
      })
      .filter(function (item) {
        return item !== "";
      })
      .map(function (item) {
        return /^-?\d+(\.\d+)?$/.test(item) ? Number(item) : item;
      });
  }

  function buildBody(form) {
    var body = {};
    fieldsOf(form).forEach(function (input) {
      if (input.dataset.location !== "body") {
        return;
      }
      var result = readBodyValue(input);
      if (result.present) {
        body[input.name] = result.value;
      }
    });
    return body;
  }

  async function readJson(response) {
    if (response.status === 204) {
      return null;
    }
    try {
      return await response.json();
    } catch (error) {
      return null;
    }
  }

  function successMessage(result) {
    if (Array.isArray(result)) {
      return result.length === 1 ? "1 post hämtad." : result.length + " poster hämtade.";
    }
    return "Klart.";
  }

  // Destructive actions need a second, deliberate press within a short
  // window. Any other interaction (timeout, blur, Escape) disarms.
  function createConfirmGuard(form, button) {
    var timer = null;

    function disarm() {
      window.clearTimeout(timer);
      timer = null;
      delete button.dataset.armed;
      button.textContent = button.dataset.label;
    }

    button.addEventListener("blur", disarm);
    form.addEventListener("keydown", function (event) {
      if (event.key === "Escape" && button.dataset.armed !== undefined) {
        disarm();
      }
    });

    return {
      // Returns true when the action may proceed.
      check: function () {
        if (button.dataset.armed !== undefined) {
          disarm();
          return true;
        }
        button.dataset.armed = "";
        button.textContent = "Bekräfta: " + button.dataset.label.toLowerCase();
        timer = window.setTimeout(disarm, CONFIRM_WINDOW_MS);
        return false;
      },
    };
  }

  function registerAdminAction(form) {
    var method = form.dataset.method || "GET";
    var template = form.dataset.urlTemplate;
    var button = form.querySelector("button[type=submit]");
    var status = form.querySelector("[data-admin-status]");
    var output = form.querySelector("[data-admin-output]");
    var guard = form.hasAttribute("data-destructive") ? createConfirmGuard(form, button) : null;
    var inFlight = false;

    form.addEventListener("submit", async function (event) {
      event.preventDefault();
      if (inFlight || (guard && !guard.check())) {
        return;
      }

      inFlight = true;
      button.disabled = true;
      setStatus(status, "Arbetar ...", "busy");

      var init = {
        method: method,
        headers: { Accept: "application/json" },
        credentials: "same-origin",
      };
      if (BODY_METHODS[method]) {
        // A JSON content type forces a CORS preflight, blocking cross-site CSRF.
        init.headers["Content-Type"] = "application/json";
        init.body = JSON.stringify(buildBody(form));
      }

      try {
        var response = await fetch(buildUrl(template, form), init);
        var result = await readJson(response);

        if (response.ok) {
          if (result === null) {
            hideOutput(output);
          } else {
            showOutput(output, result);
          }
          setStatus(status, successMessage(result));
          return;
        }

        if (response.status === 401) {
          hideOutput(output);
          setStatus(status, "Sessionen har gått ut. Skickar dig till inloggningen ...", "error");
          window.setTimeout(function () {
            window.location.assign(LOGIN_URL);
          }, REDIRECT_DELAY_MS);
          return;
        }

        var message = (result && (result.error || result.message)) || "Något gick fel (" + response.status + ").";
        setStatus(status, message, "error");
        if (result && result.details) {
          showOutput(output, result.details);
        } else {
          hideOutput(output);
        }
      } catch (error) {
        hideOutput(output);
        setStatus(status, "Kunde inte nå servern.", "error");
      } finally {
        inFlight = false;
        button.disabled = false;
      }
    });
  }

  function registerLogout() {
    var form = document.getElementById("admin-logout-form");
    var error = document.getElementById("logout-error");
    if (!form) {
      return;
    }

    form.addEventListener("submit", async function (event) {
      event.preventDefault();
      setStatus(error, null);

      try {
        var response = await fetch(LOGOUT_URL, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          credentials: "same-origin",
          body: "{}",
        });
        var result = await readJson(response);

        if (response.ok && result && result.code === "logout_successful") {
          window.location.assign(LOGIN_URL);
          return;
        }
        setStatus(error, (result && result.message) || "Utloggningen misslyckades.", "error");
      } catch (caught) {
        setStatus(error, "Utloggningen misslyckades.", "error");
      }
    });
  }

  document.querySelectorAll("form[data-admin-action]").forEach(registerAdminAction);
  registerLogout();
})();
