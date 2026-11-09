/* Jira Test Case Generator — front-end controller (vanilla JS, no build step). */
(() => {
  "use strict";

  const API = "/api/v1";
  const STORAGE_KEY = "jtcg.history.v2";
  const REQUEST_TIMEOUT_MS = 240_000;
  const STORY_KEY_PATTERN = /^[A-Za-z][A-Za-z0-9_]*-[0-9]+$/;

  const $ = (selector) => document.querySelector(selector);
  const el = {
    form: $("#generator-form"),
    storyKey: $("#story-key"),
    language: $("#language"),
    format: $("#format"),
    maxCases: $("#max-cases"),
    maxCasesValue: $("#max-cases-value"),
    submit: $("#submit-button"),
    submitLabel: $(".btn-label"),
    banner: $("#config-banner"),
    jiraChip: $("#status-jira"),
    modelChip: $("#status-model"),
    version: $("#app-version"),
    empty: $("#empty"),
    loading: $("#loading"),
    error: $("#error"),
    errorCode: $("#error-code"),
    errorMessage: $("#error-message"),
    errorHint: $("#error-hint"),
    retry: $("#retry-button"),
    output: $("#output"),
    storyKeyBadge: $("#story-key-badge"),
    storyType: $("#story-type"),
    storyStatus: $("#story-status"),
    storySummary: $("#story-summary"),
    storyCriteria: $("#story-criteria"),
    storyLink: $("#story-link"),
    caseCount: $("#case-count"),
    generationMeta: $("#generation-meta"),
    warnings: $("#warnings"),
    cases: $("#cases"),
    criteria: $("#acceptance-criteria"),
    historyBlock: $("#history-block"),
    history: $("#history"),
    toast: $("#toast"),
    elapsed: $("#elapsed"),
    elapsedBar: $("#elapsed-bar"),
    copyAll: $("#copy-all"),
    template: $("#case-template")
  };

  const state = { config: null, result: null, controller: null, timer: null, startedAt: 0, busy: false };

  /* ---------------- Configuration ---------------- */

  async function loadConfig() {
    try {
      const response = await fetch(`${API}/config`, { headers: { Accept: "application/json" } });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      state.config = await response.json();
      renderConfig(state.config);
    } catch (error) {
      setChip(el.jiraChip, "err", "Jira indisponible");
      setChip(el.modelChip, "err", "modèle inconnu");
    }
  }

  function renderConfig(config) {
    el.version.textContent = config.version || "2.0.0";
    setChip(el.jiraChip, config.jiraConfigured ? "ok" : "warn",
      config.jiraConfigured ? `Jira ${hostOf(config.jiraBaseUrl)}` : "Jira non configuré");
    setChip(el.modelChip, "ok", config.model || "mistral");

    if (!config.jiraConfigured) {
      el.banner.classList.remove("hidden");
    }
    if (config.maxTestCases) {
      el.maxCases.max = String(Math.min(15, config.maxTestCases));
    }
    if (config.defaultTestCases) {
      el.maxCases.value = String(Math.min(config.defaultTestCases, Number(el.maxCases.max)));
      syncRange();
    }
  }

  function hostOf(url) {
    try { return new URL(url).host; } catch { return url || "configuré"; }
  }

  function setChip(chip, level, label) {
    chip.classList.remove("ok", "warn", "err");
    if (level) chip.classList.add(level);
    const target = chip.querySelector(".chip-label");
    if (target) target.textContent = label;
    else chip.textContent = label;
  }

  /* ---------------- Form ---------------- */

  function syncRange() {
    const min = Number(el.maxCases.min);
    const max = Number(el.maxCases.max);
    const value = Number(el.maxCases.value);
    const percent = ((value - min) / (max - min)) * 100;
    el.maxCases.style.setProperty("--fill", `${percent}%`);
    el.maxCasesValue.textContent = String(value);
  }

  function setBusy(busy) {
    state.busy = busy;
    document.querySelector(".results").setAttribute("aria-busy", String(busy));
    el.submit.disabled = busy;
    el.submitLabel.textContent = busy ? "Génération en cours…" : "Générer les cas de test";
  }

  function show(section) {
    for (const node of [el.empty, el.loading, el.error, el.output]) {
      node.classList.add("hidden");
    }
    section.classList.remove("hidden");
  }

  function startTimer() {
    state.startedAt = Date.now();
    el.elapsed.textContent = "0 s";
    el.elapsedBar.style.width = "3%";
    state.timer = window.setInterval(() => {
      const seconds = Math.floor((Date.now() - state.startedAt) / 1000);
      el.elapsed.textContent = `${seconds} s`;
      el.elapsedBar.style.width = `${Math.min(94, 3 + seconds * 1.6)}%`;
    }, 1000);
  }

  function stopTimer() {
    if (state.timer) window.clearInterval(state.timer);
    state.timer = null;
  }

  async function generate(event) {
    if (event) event.preventDefault();
    if (state.busy) return;

    const storyKey = el.storyKey.value.trim().toUpperCase();
    el.storyKey.value = storyKey;

    if (!STORY_KEY_PATTERN.test(storyKey)) {
      el.storyKey.setAttribute("aria-invalid", "true");
      el.storyKey.focus();
      toast("Clé invalide : utilisez le format PROJET-123.");
      return;
    }
    el.storyKey.removeAttribute("aria-invalid");

    const params = new URLSearchParams({
      storyKey,
      language: el.language.value,
      format: el.format.value,
      maxCases: el.maxCases.value
    });

    state.controller = new AbortController();
    const timeout = window.setTimeout(() => state.controller.abort(), REQUEST_TIMEOUT_MS);

    setBusy(true);
    hideError();
    show(el.loading);
    startTimer();

    try {
      const response = await fetch(`${API}/test-cases?${params}`, {
        headers: { Accept: "application/json" },
        signal: state.controller.signal
      });
      const payload = await response.json().catch(() => null);
      if (!response.ok) {
        throw new ApiError(payload || {}, response.status);
      }
      state.result = payload;
      renderResult(payload);
      remember(payload);
      show(el.output);
      toast(`${payload.testCases.length} cas de test générés.`);
    } catch (error) {
      if (error.name === "AbortError") {
        showError("TIMEOUT", "La requête a dépassé 4 minutes.", "Le modèle local est peut-être surchargé. Réessayez ou réduisez le nombre de cas.");
      } else if (error instanceof ApiError) {
        showError(error.code, error.message, hintFor(error.code));
      } else {
        showError("NETWORK_ERROR", "Impossible de contacter l'API.", "Vérifiez que le serveur est démarré et que vous êtes connecté au bon réseau.");
      }
      show(el.error);
    } finally {
      window.clearTimeout(timeout);
      stopTimer();
      setBusy(false);
      state.controller = null;
    }
  }

  class ApiError extends Error {
    constructor(problem, status) {
      super(problem.detail || problem.message || `Erreur HTTP ${status}`);
      this.code = problem.code || `HTTP_${status}`;
    }
  }

  function hintFor(code) {
    switch (code) {
      case "JIRA_NOT_CONFIGURED":
        return "Renseignez JIRA_BASE_URL, JIRA_EMAIL et JIRA_API_TOKEN dans l'environnement, puis redémarrez l'application.";
      case "JIRA_AUTH_FAILED":
        return "Le token est expiré ou ne dispose pas des droits de lecture sur ce projet. Générez un nouveau token Atlassian.";
      case "JIRA_UNAVAILABLE":
        return "Vérifiez l'URL Jira, l'accès réseau et la version de l'API (3 pour Cloud, 2 pour Server).";
      case "AI_UNAVAILABLE":
        return "Démarrez Ollama (ollama serve) et vérifiez que le modèle est téléchargé (ollama pull mistral).";
      case "AI_RESPONSE_INVALID":
        return "Le modèle n'a pas respecté le format JSON. Réessayez, ou utilisez un modèle plus grand (llama3.1, qwen2.5).";
      case "STORY_NOT_FOUND":
        return "Vérifiez la clé et vos permissions sur le projet Jira.";
      case "VALIDATION_ERROR":
        return "Corrigez les paramètres de la requête : clé de story, langue, format ou nombre de cas.";
      default:
        return "Consultez les logs du serveur pour plus de détails.";
    }
  }

  /* ---------------- Rendering ---------------- */

  function renderResult(result) {
    const { story, generation, testCases, warnings } = result;

    el.storyKeyBadge.textContent = story.key;
    el.storyType.textContent = story.issueType || "Issue";
    el.storyStatus.textContent = story.status || "—";
    el.storySummary.textContent = story.summary || "(sans titre)";
    el.storyCriteria.textContent = story.acceptanceCriteria || story.description || "Aucun critère d'acceptation disponible.";
    el.storyLink.href = story.url || "#";

    el.caseCount.textContent = `${testCases.length} cas de test`;
    el.generationMeta.textContent = `${generation.model} · ${(generation.durationMs / 1000).toFixed(1)} s · ${generation.language}/${generation.format}`;
    el.criteria.textContent = story.acceptanceCriteria || story.description || "—";

    el.warnings.innerHTML = "";
    for (const warning of warnings || []) {
      const p = document.createElement("p");
      p.textContent = warning;
      el.warnings.appendChild(p);
    }
    el.warnings.classList.toggle("hidden", !(warnings || []).length);

    el.cases.innerHTML = "";
    testCases.forEach((testCase, index) => el.cases.appendChild(buildCase(testCase, index)));
  }

  function buildCase(testCase, index) {
    const fragment = el.template.content.cloneNode(true);
    const card = fragment.querySelector(".case-card");

    fragment.querySelector(".case-id").textContent = testCase.id || `TC-${String(index + 1).padStart(3, "0")}`;
    fragment.querySelector(".case-type").textContent = testCase.type || "Fonctionnel";
    const priority = fragment.querySelector(".case-priority");
    priority.textContent = testCase.priority || "Moyenne";
    priority.classList.add(`prio-${slug(testCase.priority || "moyenne")}`);
    fragment.querySelector(".case-title").textContent = testCase.title || "Cas de test";

    const preconditions = (testCase.preconditions || []).filter(Boolean);
    if (preconditions.length) {
      const block = fragment.querySelector(".preconditions");
      block.classList.remove("hidden");
      const list = block.querySelector("ul");
      preconditions.forEach((item) => list.appendChild(li(item)));
    }

    const steps = (testCase.steps || []).filter(Boolean);
    const stepsList = fragment.querySelector(".steps");
    steps.forEach((step) => stepsList.appendChild(li(step)));

    const data = (testCase.testData || []).filter(Boolean);
    if (data.length) {
      const block = fragment.querySelector(".data-block");
      block.classList.remove("hidden");
      const list = block.querySelector(".test-data");
      data.forEach((item) => list.appendChild(li(item)));
    }

    fragment.querySelector(".expected p").textContent = testCase.expectedResult || "—";
    fragment.querySelector(".copy-case").addEventListener("click", () => {
      copy(toMarkdownCase(testCase), "Cas de test copié.");
    });

    card.dataset.index = String(index);
    return fragment;
  }

  function li(text) {
    const node = document.createElement("li");
    node.textContent = text;
    return node;
  }

  function slug(value) {
    return String(value)
      .normalize("NFD").replace(/[\u0300-\u036f]/g, "")
      .toLowerCase().replace(/[^a-z]/g, "");
  }

  function showError(code, message, hint) {
    el.errorCode.textContent = code;
    el.errorMessage.textContent = message;
    el.errorHint.textContent = hint || "";
    hideError();
    show(el.error);
  }

  function hideError() {
    el.error.classList.add("hidden");
    el.errorCode.textContent = "";
    el.errorMessage.textContent = "";
    el.errorHint.textContent = "";
  }

  /* ---------------- Exports ---------------- */

  function download(filename, content, mime) {
    const blob = new Blob([content], { type: mime });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = filename;
    document.body.appendChild(anchor);
    anchor.click();
    anchor.remove();
    URL.revokeObjectURL(url);
  }

  function timestamp() {
    return new Date().toISOString().slice(0, 19).replace(/[:T]/g, "-");
  }

  function exportJson() {
    download(`test-cases-${state.result.story.key}-${timestamp()}.json`,
      JSON.stringify(state.result, null, 2), "application/json;charset=utf-8");
  }

  function csvCell(value) {
    const text = String(value ?? "").replace(/"/g, '""');
    return `"${text}"`;
  }

  function exportCsv() {
    const rows = [["ID", "Titre", "Type", "Priorité", "Préconditions", "Étapes", "Données de test", "Résultat attendu"]];
    for (const tc of state.result.testCases) {
      rows.push([
        tc.id, tc.title, tc.type, tc.priority,
        (tc.preconditions || []).join(" | "),
        (tc.steps || []).join(" | "),
        (tc.testData || []).join(" | "),
        tc.expectedResult
      ]);
    }
    const csv = "\ufeff" + rows.map((row) => row.map(csvCell).join(";")).join("\r\n");
    download(`test-cases-${state.result.story.key}-${timestamp()}.csv`, csv, "text/csv;charset=utf-8");
  }

  function toMarkdownCase(tc) {
    const lines = [`### ${tc.id} — ${tc.title}`, "", `**Type :** ${tc.type} · **Priorité :** ${tc.priority}`, ""];
    if ((tc.preconditions || []).length) {
      lines.push("**Préconditions**", ...tc.preconditions.map((p) => `- ${p}`), "");
    }
    lines.push("**Étapes**", ...(tc.steps || []).map((step, i) => `${i + 1}. ${step}`), "");
    if ((tc.testData || []).length) {
      lines.push("**Données de test**", ...tc.testData.map((d) => `- \`${d}\``), "");
    }
    lines.push(`**Résultat attendu :** ${tc.expectedResult}`, "");
    return lines.join("\n");
  }

  function exportMarkdown() {
    const { story, generation, testCases } = state.result;
    const lines = [
      `# Cas de test — ${story.key}`, "",
      `**Story :** ${story.summary}`, "",
      `**Type :** ${story.issueType} · **Statut :** ${story.status}`,
      `**Lien Jira :** ${story.url}`,
      `**Modèle :** ${generation.model} · **Généré le :** ${new Date(generation.generatedAt).toLocaleString("fr-FR")}`,
      `**Langue :** ${generation.language} · **Format :** ${generation.format}`, "",
      `## Critères d'acceptation`, "", "```", story.acceptanceCriteria || "—", "```", "",
      `## Cas de test (${testCases.length})`, "",
      ...testCases.map(toMarkdownCase)
    ];
    download(`test-cases-${story.key}-${timestamp()}.md`, lines.join("\n"), "text/markdown;charset=utf-8");
  }

  async function copy(text, message) {
    try {
      await navigator.clipboard.writeText(text);
      toast(message || "Copié dans le presse-papiers.");
    } catch {
      toast("Copie impossible : votre navigateur bloque le presse-papiers.");
    }
  }

  function copyAll() {
    if (!state.result) return;
    const { story, testCases } = state.result;
    copy([`# Cas de test — ${story.key} : ${story.summary}`, "", ...testCases.map(toMarkdownCase)].join("\n"),
      "Tous les cas de test ont été copiés.");
  }

  /* ---------------- History ---------------- */

  function history() {
    try { return JSON.parse(localStorage.getItem(STORAGE_KEY) || "[]"); } catch { return []; }
  }

  function remember(result) {
    const entry = {
      key: result.story.key,
      summary: result.story.summary,
      count: result.testCases.length,
      at: Date.now()
    };
    const items = history().filter((item) => item.key !== entry.key);
    items.unshift(entry);
    localStorage.setItem(STORAGE_KEY, JSON.stringify(items.slice(0, 8)));
    renderHistory();
  }

  function renderHistory() {
    const items = history();
    el.history.innerHTML = "";
    el.historyBlock.classList.toggle("hidden", items.length === 0);
    for (const item of items) {
      const button = document.createElement("button");
      button.type = "button";
      button.className = "history-item";
      button.textContent = item.key;
      const detail = document.createElement("span");
      detail.textContent = `${item.count} cas`;
      button.appendChild(detail);
      button.title = item.summary || item.key;
      button.addEventListener("click", () => {
        el.storyKey.value = item.key;
        el.storyKey.focus();
        generate();
      });
      el.history.appendChild(button);
    }
  }

  let toastTimer = null;
  function toast(message) {
    el.toast.textContent = message;
    el.toast.classList.add("show");
    window.clearTimeout(toastTimer);
    toastTimer = window.setTimeout(() => el.toast.classList.remove("show"), 3200);
  }

  /* ---------------- Wiring ---------------- */

  el.form.addEventListener("submit", generate);
  el.maxCases.addEventListener("input", syncRange);
  el.retry.addEventListener("click", () => generate());
  el.copyAll.addEventListener("click", copyAll);
  el.storyKey.addEventListener("input", () => el.storyKey.removeAttribute("aria-invalid"));

  for (const button of document.querySelectorAll("[data-export]")) {
    button.addEventListener("click", () => {
      if (!state.result) return;
      const type = button.dataset.export;
      if (type === "json") exportJson();
      if (type === "csv") exportCsv();
      if (type === "md") exportMarkdown();
    });
  }

  syncRange();
  renderHistory();
  loadConfig();
})();
