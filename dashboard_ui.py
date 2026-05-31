DASHBOARD_HTML = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Morpho Workbench</title>
  <style>
    :root {
      --ink: #15242c;
      --muted: #60727c;
      --soft: #eef2ec;
      --paper: #fffdf7;
      --panel: rgba(255, 253, 247, .94);
      --line: #d8dfd7;
      --line-strong: #b7c4bb;
      --accent: #0d6761;
      --accent-dark: #084d49;
      --amber: #a6631c;
      --blue: #315f8f;
      --danger: #9d3f38;
      --shadow: 0 18px 46px rgba(34, 48, 42, .12);
    }

    * { box-sizing: border-box; }

    body {
      margin: 0;
      min-height: 100vh;
      color: var(--ink);
      background:
        radial-gradient(circle at 12% 14%, rgba(13, 103, 97, .16), transparent 28rem),
        radial-gradient(circle at 84% 8%, rgba(166, 99, 28, .16), transparent 24rem),
        linear-gradient(135deg, #f7f0df 0%, #edf3ee 47%, #e7ece7 100%);
      font-family: "Aptos", "Segoe UI", sans-serif;
    }

    button, textarea, select {
      font: inherit;
    }

    button {
      border: 0;
      border-radius: 8px;
      color: white;
      cursor: pointer;
      background: var(--accent);
      padding: 10px 13px;
      transition: transform .16s ease, background .16s ease, opacity .16s ease;
    }

    button:hover { transform: translateY(-1px); background: var(--accent-dark); }
    button:disabled { cursor: wait; opacity: .62; transform: none; }
    button.danger { background: var(--danger); }
    button.danger:hover { background: #7e302b; }
    button.ghost { background: #f7faf6; color: var(--ink); border: 1px solid var(--line); }
    button.ghost:hover { background: #ebf1ea; }
    button.mini { padding: 7px 10px; font-size: 12px; }

    .shell {
      display: grid;
      grid-template-columns: 276px minmax(0, 1fr);
      min-height: 100vh;
    }

    .rail {
      position: sticky;
      top: 0;
      height: 100vh;
      overflow: auto;
      padding: 20px;
      color: #eef6f2;
      background:
        linear-gradient(180deg, rgba(21, 36, 44, .98), rgba(12, 27, 33, .98)),
        radial-gradient(circle at 20% 18%, rgba(13, 103, 97, .4), transparent 15rem);
      border-right: 1px solid rgba(255, 255, 255, .08);
    }

    .brand {
      display: flex;
      align-items: center;
      gap: 12px;
      margin-bottom: 22px;
    }

    .brand-mark {
      display: grid;
      place-items: center;
      width: 42px;
      height: 42px;
      border-radius: 8px;
      font-weight: 800;
      letter-spacing: .08em;
      color: #05211f;
      background: linear-gradient(135deg, #a8e0d7, #f0cb8d);
      box-shadow: 0 10px 26px rgba(0, 0, 0, .25);
    }

    .brand-title {
      font-size: 20px;
      font-weight: 800;
      letter-spacing: .02em;
    }

    .brand-subtitle, .rail-label {
      color: rgba(238, 246, 242, .68);
      font-size: 12px;
      letter-spacing: .06em;
      text-transform: uppercase;
    }

    .rail-section {
      padding: 16px 0;
      border-top: 1px solid rgba(255, 255, 255, .1);
    }

    .rail-actions {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 8px;
      margin-top: 10px;
    }

    .rail-actions button, .rail select {
      width: 100%;
    }

    .rail select {
      margin-top: 10px;
      border: 1px solid rgba(255, 255, 255, .18);
      border-radius: 8px;
      color: #eef6f2;
      background: rgba(255, 255, 255, .08);
      padding: 10px;
    }

    .rail select option {
      color: var(--ink);
    }

    .status-stack {
      display: grid;
      gap: 8px;
      margin-top: 10px;
    }

    .rail-stat {
      display: flex;
      justify-content: space-between;
      gap: 12px;
      padding: 9px 10px;
      border: 1px solid rgba(255, 255, 255, .1);
      border-radius: 8px;
      background: rgba(255, 255, 255, .06);
      font-size: 13px;
    }

    .workspace {
      padding: 22px;
      overflow: hidden;
    }

    .topbar {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 16px;
      margin-bottom: 16px;
    }

    .eyebrow {
      margin: 0 0 4px;
      color: var(--accent);
      font-size: 12px;
      font-weight: 800;
      letter-spacing: .12em;
      text-transform: uppercase;
    }

    h1, h2, h3, p {
      margin-top: 0;
    }

    h1 {
      margin-bottom: 0;
      font-size: clamp(30px, 4vw, 48px);
      letter-spacing: -.04em;
    }

    h2 {
      margin-bottom: 0;
      font-size: 18px;
    }

    h3 {
      margin-bottom: 12px;
      font-size: 15px;
      letter-spacing: -.01em;
    }

    .sync {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      min-width: 136px;
      justify-content: center;
      border: 1px solid var(--line);
      border-radius: 999px;
      background: rgba(255, 253, 247, .72);
      padding: 8px 12px;
      color: var(--muted);
      font-size: 13px;
    }

    .dot {
      width: 9px;
      height: 9px;
      border-radius: 50%;
      background: var(--accent);
      box-shadow: 0 0 0 5px rgba(13, 103, 97, .12);
    }

    .dot.busy { background: var(--amber); box-shadow: 0 0 0 5px rgba(166, 99, 28, .14); }
    .dot.bad { background: var(--danger); box-shadow: 0 0 0 5px rgba(157, 63, 56, .13); }

    .layout {
      display: grid;
      grid-template-columns: minmax(360px, 1.35fr) minmax(320px, .85fr);
      gap: 16px;
      align-items: start;
    }

    .panel {
      border: 1px solid var(--line);
      border-radius: 8px;
      background: var(--panel);
      box-shadow: var(--shadow);
      backdrop-filter: blur(18px);
      padding: 16px;
    }

    .section-head {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 10px;
      margin-bottom: 12px;
    }

    .chat-panel {
      min-height: calc(100vh - 120px);
      display: flex;
      flex-direction: column;
    }

    .chat-log {
      flex: 1;
      min-height: 390px;
      max-height: calc(100vh - 310px);
      overflow: auto;
      display: flex;
      flex-direction: column;
      gap: 12px;
      padding: 4px 4px 12px;
    }

    .message {
      width: fit-content;
      max-width: min(84%, 760px);
      border-radius: 8px;
      border: 1px solid var(--line);
      padding: 12px 13px;
      animation: rise .22s ease both;
    }

    .message.user {
      align-self: flex-end;
      background: #e7f3ef;
      border-color: #c7ded7;
    }

    .message.morpho {
      align-self: flex-start;
      color: #e8f2ef;
      background: linear-gradient(135deg, #101b22, #183239);
      border-color: rgba(255, 255, 255, .08);
      box-shadow: 0 14px 34px rgba(16, 27, 34, .18);
    }

    .message.error {
      background: #fff0ec;
      border-color: #f0b3aa;
      color: #722b26;
    }

    .speaker {
      margin-bottom: 5px;
      font-size: 11px;
      font-weight: 800;
      letter-spacing: .12em;
      text-transform: uppercase;
      opacity: .75;
    }

    .message-text {
      line-height: 1.5;
      white-space: pre-wrap;
    }

    .message-meta {
      margin-top: 8px;
      font-size: 12px;
      opacity: .68;
    }

    .composer {
      border-top: 1px solid var(--line);
      padding-top: 12px;
    }

    textarea {
      width: 100%;
      resize: vertical;
      min-height: 96px;
      color: var(--ink);
      background: #fffefa;
      border: 1px solid var(--line-strong);
      border-radius: 8px;
      padding: 12px;
      outline: none;
    }

    textarea:focus {
      border-color: var(--accent);
      box-shadow: 0 0 0 4px rgba(13, 103, 97, .12);
    }

    .composer-actions {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 10px;
      margin-top: 10px;
    }

    .hint {
      color: var(--muted);
      font-size: 12px;
    }

    .side-stack, .telemetry {
      display: grid;
      gap: 16px;
    }

    .telemetry {
      grid-column: 1 / -1;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      margin-top: 16px;
    }

    .panel-list {
      max-height: 288px;
      overflow: auto;
      padding-right: 4px;
    }

    .panel-list.tall {
      max-height: 380px;
    }

    .item {
      border: 1px solid var(--line);
      border-left: 4px solid var(--accent);
      border-radius: 8px;
      background: rgba(255, 255, 255, .68);
      padding: 11px;
      margin-bottom: 10px;
    }

    .item.warn { border-left-color: var(--amber); }
    .item.danger { border-left-color: var(--danger); }
    .item.info { border-left-color: var(--blue); }

    .item-title {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 8px;
      margin-bottom: 6px;
      font-weight: 800;
    }

    .item-actions {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      margin-top: 10px;
    }

    .muted {
      color: var(--muted);
      font-size: 13px;
      line-height: 1.45;
    }

    .pill-row {
      display: flex;
      flex-wrap: wrap;
      gap: 6px;
      margin: 8px 0;
    }

    .pill {
      display: inline-flex;
      align-items: center;
      gap: 5px;
      min-height: 24px;
      border-radius: 999px;
      border: 1px solid var(--line);
      color: #33454c;
      background: #f6f8f4;
      padding: 4px 8px;
      font-size: 12px;
    }

    .pill.good { color: #0b5b46; background: #e7f4ec; border-color: #c7e3d2; }
    .pill.warn { color: #704100; background: #fff3dc; border-color: #ead1a4; }
    .pill.danger { color: #7b302b; background: #ffefec; border-color: #efbab2; }
    .pill.info { color: #214e80; background: #e9f0fb; border-color: #c7d8ef; }

    .metrics {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 8px;
    }

    .metric {
      border: 1px solid var(--line);
      border-radius: 8px;
      background: rgba(255, 255, 255, .68);
      padding: 10px;
    }

    .metric span {
      display: block;
      color: var(--muted);
      font-size: 12px;
    }

    .metric strong {
      display: block;
      margin-top: 4px;
      font-size: 20px;
    }

    .raw-output {
      min-height: 142px;
      max-height: 260px;
      overflow: auto;
      border-radius: 8px;
      background: #101820;
      color: #dce8e6;
      padding: 12px;
      white-space: pre-wrap;
      font-family: "Cascadia Mono", "Consolas", monospace;
      font-size: 12px;
      line-height: 1.45;
    }

    details {
      margin-top: 10px;
    }

    summary {
      color: var(--muted);
      cursor: pointer;
      font-size: 13px;
    }

    @keyframes rise {
      from { opacity: 0; transform: translateY(6px); }
      to { opacity: 1; transform: translateY(0); }
    }

    @media (max-width: 1120px) {
      .layout, .telemetry {
        grid-template-columns: 1fr;
      }
      .chat-panel {
        min-height: auto;
      }
      .chat-log {
        max-height: 520px;
      }
    }

    @media (max-width: 640px) {
      .shell { grid-template-columns: 1fr; }
      .rail {
        position: relative;
        height: auto;
      }
      .workspace, .rail { padding: 14px; }
      .topbar, .composer-actions {
        align-items: stretch;
        flex-direction: column;
      }
      .sync {
        width: 100%;
      }
      .message {
        max-width: 100%;
      }
    }
  </style>
</head>
<body>
  <div class="shell">
    <aside class="rail">
      <div class="brand">
        <div class="brand-mark">M</div>
        <div>
          <div class="brand-title">Morpho</div>
          <div class="brand-subtitle">Local cockpit</div>
        </div>
      </div>

      <div class="rail-section">
        <div class="rail-label">Observation</div>
        <div class="rail-actions">
          <button onclick="toggle('/assistant/activity/toggle', true)">Activity on</button>
          <button class="danger" onclick="toggle('/assistant/activity/toggle', false)">Activity off</button>
          <button onclick="toggle('/assistant/screen/toggle', true)">Screen on</button>
          <button class="danger" onclick="toggle('/assistant/screen/toggle', false)">Screen off</button>
        </div>
      </div>

      <div class="rail-section">
        <div class="rail-label">Realtime</div>
        <div class="rail-actions">
          <button onclick="postJson('/assistant/realtime/start', {}, 'Starting realtime loop...')">Start loop</button>
          <button class="danger" onclick="postJson('/assistant/realtime/stop', {}, 'Stopping realtime loop...')">Stop loop</button>
        </div>
      </div>

      <div class="rail-section">
        <div class="rail-label">Permission mode</div>
        <select id="mode" onchange="setMode()">
          <option value="SAFE_MODE">SAFE_MODE</option>
          <option value="AUTO_MODE">AUTO_MODE</option>
        </select>
      </div>

      <div class="rail-section">
        <div class="rail-label">System pulse</div>
        <div id="statusSummary" class="status-stack">
          <div class="rail-stat"><span>Activity</span><strong>syncing</strong></div>
          <div class="rail-stat"><span>Screen</span><strong>syncing</strong></div>
          <div class="rail-stat"><span>Realtime</span><strong>syncing</strong></div>
        </div>
      </div>
    </aside>

    <main class="workspace">
      <header class="topbar">
        <div>
          <p class="eyebrow">Autonomous interface</p>
          <h1>Morpho Workbench</h1>
        </div>
        <div class="sync">
          <span id="syncDot" class="dot busy"></span>
          <span id="syncText">Syncing</span>
        </div>
      </header>

      <div class="layout">
        <section class="panel chat-panel">
          <div class="section-head">
            <h2>Conversation</h2>
            <span id="chatState" class="pill info">ready</span>
          </div>
          <div id="chatLog" class="chat-log">
            <div class="message morpho">
              <div class="speaker">Morpho</div>
              <div class="message-text">I am here in the local machine. Give me a thread to pull, and I will work it through with you.</div>
            </div>
          </div>
          <div class="composer">
            <textarea id="prompt" rows="3" placeholder="Speak to Morpho..."></textarea>
            <div class="composer-actions">
              <span class="hint">Ctrl + Enter sends</span>
              <div>
                <button class="ghost" onclick="clearChat()">Clear</button>
                <button id="sendButton" onclick="talk()">Send</button>
              </div>
            </div>
          </div>
        </section>

        <aside class="side-stack">
          <section class="panel">
            <div class="section-head">
              <h2>Suggestions</h2>
              <span id="suggestionCount" class="pill">0</span>
            </div>
            <div id="suggestions" class="panel-list"></div>
          </section>

          <section class="panel">
            <div class="section-head">
              <h2>Permission Inbox</h2>
              <span id="permissionCount" class="pill">0</span>
            </div>
            <div id="permissions" class="panel-list"></div>
          </section>

          <section class="panel">
            <div class="section-head">
              <h2>Behavior Model</h2>
              <span id="behaviorCount" class="pill">0 actions</span>
            </div>
            <div id="behavior" class="panel-list"></div>
          </section>
        </aside>

        <section class="telemetry">
          <div class="panel">
            <div class="section-head">
              <h2>Status</h2>
            </div>
            <div id="status" class="metrics"></div>
          </div>

          <div class="panel">
            <div class="section-head">
              <h2>Executions</h2>
              <span id="executionCount" class="pill">0</span>
            </div>
            <div id="executions" class="panel-list"></div>
          </div>

          <div class="panel">
            <div class="section-head">
              <h2>Activity Timeline</h2>
            </div>
            <div id="timeline" class="panel-list"></div>
          </div>

          <div class="panel">
            <div class="section-head">
              <h2>Action Logs</h2>
              <span id="logCount" class="pill">0</span>
            </div>
            <div id="logs" class="panel-list tall"></div>
          </div>

          <div class="panel">
            <div class="section-head">
              <h2>Raw Output</h2>
            </div>
            <pre id="output" class="raw-output">Ready.</pre>
          </div>
        </section>
      </div>
    </main>
  </div>

  <script>
    const dashboardState = { refreshing: false, chatBusy: false };

    function byId(id) { return document.getElementById(id); }

    function escapeHtml(value) {
      return String(value ?? '').replace(/[&<>"']/g, ch => ({
        '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
      }[ch]));
    }

    function lineBreaks(value) {
      return escapeHtml(value).replace(/\\n/g, '<br>');
    }

    function setSync(text, kind) {
      byId('syncText').textContent = text;
      byId('syncDot').className = 'dot ' + (kind || '');
    }

    function writeOutput(value) {
      byId('output').textContent = typeof value === 'string' ? value : JSON.stringify(value, null, 2);
    }

    function setChatBusy(isBusy) {
      dashboardState.chatBusy = isBusy;
      byId('sendButton').disabled = isBusy;
      byId('chatState').textContent = isBusy ? 'thinking' : 'ready';
      byId('chatState').className = 'pill ' + (isBusy ? 'warn' : 'info');
    }

    function confidenceValue(value) {
      const number = Number(value);
      return Number.isFinite(number) ? number.toFixed(2) : 'n/a';
    }

    function riskClass(risk) {
      const normalized = String(risk || '').toLowerCase();
      if (normalized === 'high') return 'danger';
      if (normalized === 'medium') return 'warn';
      if (normalized === 'low') return 'good';
      return 'info';
    }

    function boolText(value) {
      return value ? 'on' : 'off';
    }

    function explanationText(item) {
      const explanation = item && item.explanation;
      if (typeof explanation === 'string') return explanation;
      if (explanation && explanation.summary) return explanation.summary;
      if (item && item.explanation_detail && item.explanation_detail.summary) return item.explanation_detail.summary;
      return '';
    }

    function itemTitle(item) {
      return item.title || item.action_type || item.action || item.step || item.workflow || 'Untitled action';
    }

    function addChatMessage(role, text, meta) {
      const node = document.createElement('div');
      node.className = 'message ' + role;
      node.innerHTML = `
        <div class="speaker">${role === 'user' ? 'You' : 'Morpho'}</div>
        <div class="message-text">${lineBreaks(text)}</div>
        ${meta ? `<div class="message-meta">${escapeHtml(meta)}</div>` : ''}
      `;
      byId('chatLog').appendChild(node);
      byId('chatLog').scrollTop = byId('chatLog').scrollHeight;
      return node;
    }

    function updateChatMessage(node, text, meta, isError) {
      node.className = 'message ' + (isError ? 'error' : 'morpho');
      node.innerHTML = `
        <div class="speaker">${isError ? 'System' : 'Morpho'}</div>
        <div class="message-text">${lineBreaks(text)}</div>
        ${meta ? `<div class="message-meta">${escapeHtml(meta)}</div>` : ''}
      `;
      byId('chatLog').scrollTop = byId('chatLog').scrollHeight;
    }

    function clearChat() {
      byId('chatLog').innerHTML = `
        <div class="message morpho">
          <div class="speaker">Morpho</div>
          <div class="message-text">Cleared the surface. I still remember through the memory layer.</div>
        </div>
      `;
      writeOutput('Chat surface cleared.');
    }

    function talkMeta(data) {
      const parts = [];
      if (data.provider) parts.push(data.provider);
      if (data.model) parts.push(data.model);
      if (data.context_items !== undefined) parts.push('context ' + data.context_items);
      return parts.join(' / ');
    }

    function extractReply(data) {
      return data.response_text || data.response || data.message || data.error || JSON.stringify(data, null, 2);
    }

    async function requestJson(url, options) {
      const res = await fetch(url, options);
      const text = await res.text();
      let data = {};
      if (text) {
        try { data = JSON.parse(text); }
        catch { data = { raw: text }; }
      }
      if (!res.ok) {
        const message = data.error || data.msg || data.message || res.statusText || 'Request failed';
        const error = new Error(message);
        error.data = data;
        throw error;
      }
      return data;
    }

    async function getJson(url) {
      return requestJson(url, { cache: 'no-store' });
    }

    async function safeGet(url, fallback) {
      try { return await getJson(url); }
      catch (err) { return { ...fallback, error: err.message }; }
    }

    async function postJson(url, body, loadingText) {
      setSync(loadingText || 'Working...', 'busy');
      try {
        const data = await requestJson(url, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(body || {})
        });
        writeOutput(data);
        await refreshAll();
        setSync('Synced', '');
        return data;
      } catch (err) {
        const error = { status: 'error', message: err.message, url, detail: err.data || null };
        writeOutput(error);
        setSync('Needs attention', 'bad');
        return error;
      }
    }

    async function toggle(url, enabled) {
      await postJson(url, { enabled }, enabled ? 'Enabling...' : 'Disabling...');
    }

    async function setMode() {
      await postJson('/assistant/permissions/mode', { mode: byId('mode').value }, 'Updating mode...');
    }

    async function talk() {
      const prompt = byId('prompt').value.trim();
      if (!prompt || dashboardState.chatBusy) {
        if (!prompt) byId('prompt').focus();
        return;
      }
      addChatMessage('user', prompt);
      byId('prompt').value = '';
      const pending = addChatMessage('morpho', 'I am passing that through the local model...');
      setChatBusy(true);
      setSync('Talking to Morpho...', 'busy');
      try {
        const data = await requestJson('/talk', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            conversation_id: 'dashboard',
            prompt,
            use_external: false
          })
        });
        updateChatMessage(pending, extractReply(data), talkMeta(data), false);
        writeOutput(data);
        await refreshAll();
        setSync('Synced', '');
      } catch (err) {
        updateChatMessage(pending, err.message || 'The message did not reach Morpho.', '', true);
        writeOutput({ status: 'error', message: err.message, detail: err.data || null });
        setSync('Needs attention', 'bad');
      } finally {
        setChatBusy(false);
      }
    }

    async function resolvePermission(id, approved) {
      await postJson('/assistant/permissions/' + encodeURIComponent(id), { approved }, approved ? 'Approving...' : 'Rejecting...');
    }

    async function executeSuggestion(id) {
      await postJson('/assistant/suggestion/execute', { id }, 'Executing suggestion...');
    }

    function renderSuggestions(items) {
      byId('suggestionCount').textContent = String(items.length || 0);
      const el = byId('suggestions');
      el.innerHTML = items.length ? items.map(item => {
        const risk = riskClass(item.risk);
        const explanation = explanationText(item);
        return `
          <div class="item ${risk}">
            <div class="item-title">
              <span>${escapeHtml(itemTitle(item))}</span>
              ${item.auto_execute ? '<span class="pill good">auto</span>' : ''}
            </div>
            <div class="muted">${escapeHtml(item.detail || (item.payload && item.payload.query) || '')}</div>
            <div class="pill-row">
              <span class="pill info">confidence ${confidenceValue(item.confidence)}</span>
              <span class="pill ${risk}">risk ${escapeHtml(item.risk || 'unknown')}</span>
            </div>
            ${explanation ? `<div class="muted">${escapeHtml(explanation)}</div>` : ''}
            <div class="item-actions"><button class="mini" data-execute="${escapeHtml(item.id)}">Execute</button></div>
          </div>
        `;
      }).join('') : '<div class="muted">No live suggestions yet.</div>';
    }

    function renderPermissions(items) {
      byId('permissionCount').textContent = String(items.length || 0);
      const el = byId('permissions');
      el.innerHTML = items.length ? items.map(item => {
        const risk = riskClass(item.risk);
        const explanation = explanationText(item);
        return `
          <div class="item ${risk}">
            <div class="item-title"><span>${escapeHtml(item.action || 'Permission request')}</span></div>
            <div class="muted">${escapeHtml(item.prompt || '')}</div>
            <div class="pill-row">
              <span class="pill info">confidence ${confidenceValue(item.confidence)}</span>
              <span class="pill ${risk}">risk ${escapeHtml(item.risk || 'unknown')}</span>
            </div>
            ${explanation ? `<div class="muted">${escapeHtml(explanation)}</div>` : ''}
            <div class="item-actions">
              <button class="mini" data-approve="${escapeHtml(item.id)}">Approve</button>
              <button class="mini danger" data-reject="${escapeHtml(item.id)}">Reject</button>
            </div>
          </div>
        `;
      }).join('') : '<div class="muted">No pending permissions.</div>';
    }

    function renderTimeline(items) {
      const el = byId('timeline');
      el.innerHTML = items.length ? items.slice().reverse().map(item => `
        <div class="item info">
          <div class="item-title"><span>${escapeHtml(item.event || 'activity')}</span></div>
          <div class="muted">${escapeHtml(item.timestamp || '')}</div>
        </div>
      `).join('') : '<div class="muted">Timeline is quiet.</div>';
    }

    function renderExecutions(items) {
      byId('executionCount').textContent = String(items.length || 0);
      const el = byId('executions');
      el.innerHTML = items.length ? items.slice().reverse().map(item => `
        <div class="item ${item.status === 'success' ? 'info' : 'warn'}">
          <div class="item-title">
            <span>${escapeHtml(item.action_type || 'execution')}</span>
            ${item.auto_execute ? '<span class="pill good">auto</span>' : ''}
          </div>
          <div class="muted">status: ${escapeHtml(item.status || 'unknown')}</div>
          <div class="muted">${escapeHtml(item.timestamp || '')}</div>
        </div>
      `).join('') : '<div class="muted">No executions yet.</div>';
    }

    function renderLogs(permissionLogs, automationLogs, executionLogs) {
      const items = [...permissionLogs, ...automationLogs, ...executionLogs].slice(-24).reverse();
      byId('logCount').textContent = String(items.length || 0);
      const el = byId('logs');
      el.innerHTML = items.length ? items.map(item => `
        <div class="item">
          <div class="item-title"><span>${escapeHtml(itemTitle(item))}</span></div>
          <div class="muted">${escapeHtml(item.status || '')}</div>
          <div class="muted">${escapeHtml(item.timestamp || '')}</div>
        </div>
      `).join('') : '<div class="muted">No logs yet.</div>';
    }

    function renderStatus(status, rt) {
      const activity = status.activity_monitor && status.activity_monitor.enabled;
      const screen = status.screen_observer && status.screen_observer.enabled;
      const realtime = rt && rt.running;
      const mode = status.permission_mode || 'SAFE_MODE';

      byId('statusSummary').innerHTML = `
        <div class="rail-stat"><span>Activity</span><strong>${boolText(activity)}</strong></div>
        <div class="rail-stat"><span>Screen</span><strong>${boolText(screen)}</strong></div>
        <div class="rail-stat"><span>Realtime</span><strong>${boolText(realtime)}</strong></div>
      `;

      byId('status').innerHTML = `
        <div class="metric"><span>Activity</span><strong>${boolText(activity)}</strong></div>
        <div class="metric"><span>Screen</span><strong>${boolText(screen)}</strong></div>
        <div class="metric"><span>Mode</span><strong>${escapeHtml(mode)}</strong></div>
        <div class="metric"><span>Realtime</span><strong>${boolText(realtime)}</strong></div>
      `;

      if (mode) byId('mode').value = mode;
    }

    function renderBehavior(model) {
      const actions = (model && model.actions) || {};
      const entries = Object.entries(actions).slice(0, 8);
      byId('behaviorCount').textContent = `${Object.keys(actions).length} actions`;
      byId('behavior').innerHTML = entries.length ? entries.map(([name, data]) => `
        <div class="item info">
          <div class="item-title"><span>${escapeHtml(name)}</span></div>
          <div class="pill-row">
            <span class="pill good">approved ${escapeHtml(data.approvals || 0)}</span>
            <span class="pill danger">rejected ${escapeHtml(data.rejections || 0)}</span>
          </div>
          <div class="muted">${escapeHtml(data.last_result || 'no recent result')}</div>
        </div>
      `).join('') + `<details><summary>Raw model</summary><pre class="raw-output">${escapeHtml(JSON.stringify(model, null, 2))}</pre></details>` : '<div class="muted">No behavior data yet.</div>';
    }

    async function refreshAll() {
      if (dashboardState.refreshing) return;
      dashboardState.refreshing = true;
      try {
        const [status, perms, logs, rt, behavior] = await Promise.all([
          safeGet('/assistant/status', { activity_monitor: {}, screen_observer: {}, permission_mode: 'SAFE_MODE' }),
          safeGet('/assistant/permissions', { pending: [], logs: [] }),
          safeGet('/assistant/logs', { permissions: [], automation: [], executions: [] }),
          safeGet('/assistant/realtime', { running: false, suggestions: [], timeline: [], executions: [] }),
          safeGet('/assistant/behavior', {})
        ]);
        renderStatus(status, rt);
        renderSuggestions(rt.suggestions || []);
        renderPermissions(perms.pending || []);
        renderTimeline(rt.timeline || []);
        renderExecutions(rt.executions || []);
        renderLogs(logs.permissions || [], logs.automation || [], logs.executions || []);
        renderBehavior(behavior);
        if (!dashboardState.chatBusy) setSync('Synced', '');
      } catch (err) {
        writeOutput({ status: 'dashboard_error', message: err.message });
        setSync('Needs attention', 'bad');
      } finally {
        dashboardState.refreshing = false;
      }
    }

    document.addEventListener('click', event => {
      const executeButton = event.target.closest('[data-execute]');
      if (executeButton) executeSuggestion(executeButton.dataset.execute);

      const approveButton = event.target.closest('[data-approve]');
      if (approveButton) resolvePermission(approveButton.dataset.approve, true);

      const rejectButton = event.target.closest('[data-reject]');
      if (rejectButton) resolvePermission(rejectButton.dataset.reject, false);
    });

    byId('prompt').addEventListener('keydown', event => {
      if ((event.ctrlKey || event.metaKey) && event.key === 'Enter') {
        event.preventDefault();
        talk();
      }
    });

    refreshAll();
    setInterval(refreshAll, 5000);
  </script>
</body>
</html>
"""
