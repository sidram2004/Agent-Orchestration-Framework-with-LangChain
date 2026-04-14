document.addEventListener('DOMContentLoaded', () => {

    // ── Parse historical Markdown ─────────────────────────────────────────
    document.querySelectorAll('.message-content[data-markdown]').forEach(el => {
        const md = el.getAttribute('data-markdown');
        el.innerHTML = typeof marked !== 'undefined' ? marked.parse(md) : md;
        el.removeAttribute('data-markdown');
        // Attach copy+tts to historical messages
        attachAiActions(el.closest('.ai-message'));
    });

    // ── Active workspace always on top of sidebar on load ───────────────
    (function () {
        const histList = document.getElementById('chat-history-list');
        if (!histList) return;
        const activeItem = histList.querySelector('.chat-item.active');
        if (activeItem) {
            const parentLink = activeItem.closest('a') || activeItem;
            histList.prepend(parentLink);
        }

        // Handle scroll_to param on load
        const params = new URLSearchParams(window.location.search);
        const scrollToId = params.get('scroll_to');
        if (scrollToId) {
            setTimeout(() => {
                const target = document.querySelector(`[data-msg-id="${scrollToId}"]`);
                if (target) {
                    target.scrollIntoView({ behavior: 'smooth', block: 'center' });
                    target.classList.add('highlight-active');
                    setTimeout(() => target.classList.remove('highlight-active'), 3000);
                }
            }, 800);
        }
    })();

    // ── Active workspace always on top ────────────────────────────────────
    // ── Theme Toggle ──────────────────────────────────────────────────────
    const themeToggle = document.getElementById('theme-toggle');
    if (themeToggle) {
        if (localStorage.getItem('theme') === 'light') document.body.classList.add('light-mode');
        themeToggle.addEventListener('click', () => {
            document.body.classList.toggle('light-mode');
            localStorage.setItem('theme', document.body.classList.contains('light-mode') ? 'light' : 'dark');
        });
    }

    const chatForm = document.getElementById('chat-form');
    if (!chatForm) return;

    const userInput = document.getElementById('user-msg');
    const chatFlow = document.getElementById('chat-flow');
    const chatIdInput = document.getElementById('chat_id');
    const chatHistoryList = document.getElementById('chat-history-list');
    const langInput = document.getElementById('user-language');
    let currentChatId = chatIdInput ? chatIdInput.value : "Chat 1";

    const scrollToBottom = () => { chatFlow.scrollTop = chatFlow.scrollHeight; };

    // ── Modal helpers ─────────────────────────────────────────────────────
    function openModal(id) { document.getElementById(id).classList.add('show'); }
    function closeModal(id) { document.getElementById(id).classList.remove('show'); }

    document.querySelectorAll('.modal-close').forEach(btn => {
        btn.addEventListener('click', () => {
            btn.closest('.modal-overlay').classList.remove('show');
        });
    });
    document.querySelectorAll('.modal-overlay').forEach(overlay => {
        overlay.addEventListener('click', e => { if (e.target === overlay) overlay.classList.remove('show'); });
    });

    // ── Settings Modal ────────────────────────────────────────────────────
    document.getElementById('btn-settings')?.addEventListener('click', () => openModal('settings-modal'));

    // ── Voice Dictation ───────────────────────────────────────────────────
    const voiceBtn = document.getElementById('voice-btn');
    if (voiceBtn) {
        const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
        if (SR) {
            const rec = new SR();
            rec.continuous = false; rec.interimResults = false;
            rec.onstart = () => { voiceBtn.innerHTML = '<i class="fa-solid fa-microphone-lines pulse" style="color:var(--accent-red)"></i>'; userInput.placeholder = "Listening..."; };
            rec.onresult = e => { userInput.value = e.results[0][0].transcript; };
            rec.onend = () => { voiceBtn.innerHTML = '<i class="fa-solid fa-microphone"></i>'; userInput.placeholder = "Command the orchestration agents..."; };
            voiceBtn.addEventListener('click', () => rec.start());
        } else { voiceBtn.style.display = 'none'; }
    }

    // ── New Workspace ─────────────────────────────────────────────────────
    document.getElementById('btn-new-chat')?.addEventListener('click', () => {
        const newId = `Chat ${Date.now().toString().slice(-4)}`;
        document.querySelectorAll('.chat-item').forEach(el => el.classList.remove('active'));
        const item = document.createElement('div');
        item.className = 'chat-item active';
        item.setAttribute('data-chat-id', newId);
        item.innerHTML = `<i class="fa-regular fa-message"></i><span>${newId}</span><i class="fa-solid fa-trash delete-chat hover-red"></i>`;
        chatHistoryList.prepend(item);
        currentChatId = newId;
        if (chatIdInput) chatIdInput.value = newId;
        chatFlow.innerHTML = `
            <div class="message ai-message slide-in">
                <div class="avatar ai-avatar"><i class="fa-solid fa-robot"></i></div>
                <div class="message-content glass-pill"><p>New workspace initialized. All agent pipelines standing by.</p></div>
            </div>`;
    });

    // ── Export Chat ───────────────────────────────────────────────────────
    document.getElementById('btn-export')?.addEventListener('click', () => {
        let text = "# OrchestAI Execution Log\n\n";
        chatFlow.querySelectorAll('.glass-pill').forEach(n => {
            const isAI = n.parentElement.classList.contains('ai-message');
            text += (isAI ? "### OrchestAI:\n" : "### User:\n") + n.innerText + "\n\n";
        });
        const a = Object.assign(document.createElement('a'), {
            href: URL.createObjectURL(new Blob([text], { type: 'text/markdown' })),
            download: `OrchestAI_${Date.now()}.md`
        });
        a.click(); URL.revokeObjectURL(a.href);
    });

    // ── Clear Chat ────────────────────────────────────────────────────────
    document.getElementById('btn-clear')?.addEventListener('click', () => {
        if (!confirm(`Clear all history in "${currentChatId}"?`)) return;
        const fd = new FormData(); fd.append('chat_id', currentChatId);
        fetch('/clear_chat', { method: 'POST', body: fd }).then(r => r.json())
            .then(res => { if (res.success) window.location.reload(); });
    });

    // ── File Attachment ───────────────────────────────────────────────────
    const pdfUpload = document.getElementById('pdf-upload');
    const fileIndicator = document.getElementById('file-indicator');

    function getFileIcon(name) {
        const ext = name.split('.').pop().toLowerCase();
        return {
            pdf: 'fa-file-pdf', docx: 'fa-file-word', doc: 'fa-file-word',
            xlsx: 'fa-file-excel', xls: 'fa-file-excel', pptx: 'fa-file-powerpoint', csv: 'fa-file-csv'
        }[ext] || 'fa-file-lines';
    }
    pdfUpload?.addEventListener('change', () => {
        if (!pdfUpload.files[0]) { fileIndicator.style.display = 'none'; return; }
        const f = pdfUpload.files[0];
        fileIndicator.innerHTML = `<i class="fa-solid ${getFileIcon(f.name)}"></i><span id="file-name">${f.name}</span><i class="fa-solid fa-xmark remove-file" id="remove-file-btn"></i>`;
        fileIndicator.style.display = 'flex';
        document.getElementById('remove-file-btn').addEventListener('click', () => { pdfUpload.value = ""; fileIndicator.style.display = 'none'; });
    });

    // ══════════════════════════════════════════════════════════════
    // FEATURE 4: Search History
    // ══════════════════════════════════════════════════════════════
    const searchInput = document.getElementById('search-input');
    const searchResults = document.getElementById('search-results');
    let searchTimer;
    searchInput?.addEventListener('input', () => {
        clearTimeout(searchTimer);
        const q = searchInput.value.trim();
        if (!q) { searchResults.style.display = 'none'; return; }
        searchTimer = setTimeout(async () => {
            const res = await fetch(`/search_history?q=${encodeURIComponent(q)}`);
            const data = await res.json();
            if (!data.results.length) { searchResults.style.display = 'none'; return; }
            searchResults.innerHTML = data.results.map(r => `
                <div class="search-result-item" onclick="window.location.href='/chat?chat_id=${encodeURIComponent(r.chat_id)}'">
                    <div class="sr-chat"><i class="fa-regular fa-message"></i> ${r.chat_id}</div>
                    <div class="sr-msg">${r.message.substring(0, 80)}...</div>
                </div>`).join('');
            searchResults.style.display = 'block';
        }, 400);
    });
    document.addEventListener('click', e => {
        if (!searchResults.contains(e.target) && e.target !== searchInput) searchResults.style.display = 'none';
    });

    // ══════════════════════════════════════════════════════════════
    // FEATURE 8: Language Selector
    // ══════════════════════════════════════════════════════════════
    document.getElementById('lang-select')?.addEventListener('change', function () {
        if (langInput) langInput.value = this.value;
        const fd = new FormData();
        fd.append('action', 'change_language');
        fd.append('language', this.value);
        fetch('/profile', { method: 'POST', body: fd });
    });

    // ══════════════════════════════════════════════════════════════
    // FEATURE 11: Quick Prompts
    // ══════════════════════════════════════════════════════════════
    const quickBar = document.getElementById('quick-prompts-bar');
    function toggleQuickPrompts() {
        const visible = quickBar.style.display !== 'none';
        quickBar.style.display = visible ? 'none' : 'block';
    }
    document.getElementById('btn-templates')?.addEventListener('click', toggleQuickPrompts);
    document.getElementById('btn-templates-inline')?.addEventListener('click', toggleQuickPrompts);
    document.querySelectorAll('.qp-chip').forEach(chip => {
        chip.addEventListener('click', () => {
            userInput.value = chip.dataset.prompt;
            userInput.focus();
            quickBar.style.display = 'none';
        });
    });

    // ══════════════════════════════════════════════════════════════
    // FEATURE 1: Analytics Dashboard
    // ══════════════════════════════════════════════════════════════
    let dailyChart, distChart;
    document.getElementById('btn-analytics')?.addEventListener('click', async () => {
        openModal('analytics-modal');
        const res = await fetch('/api/analytics');
        const data = await res.json();

        // 1. Stats Cards with specific icons and trend delta
        document.getElementById('analytics-stats').innerHTML = `
            <div class="analytics-stat-card">
                <div class="stat-val">${data.total_messages}</div>
                <div class="stat-label">Total Queries <span class="stat-delta up">▲ 12%</span></div>
            </div>
            <div class="analytics-stat-card">
                <div class="stat-val">${data.total_chats}</div>
                <div class="stat-label">Active Workspaces</div>
            </div>
            <div class="analytics-stat-card">
                <div class="stat-val">${data.avg_response_time}s</div>
                <div class="stat-label">Pipeline Speed <span class="stat-delta up">▲ 4%</span></div>
            </div>
            <div class="analytics-stat-card">
                <div class="stat-val" style="font-size:1.1rem; color:var(--secondary-neon)">${data.peak_workspace}</div>
                <div class="stat-label">Peak Workspace</div>
            </div>`;

        const isDark = !document.body.classList.contains('light-mode');
        const textColor = isDark ? '#c5c6c7' : '#4a4a4a';
        const gridColor = isDark ? 'rgba(255,255,255,0.05)' : 'rgba(0,0,0,0.05)';

        // 2. Main Trend Chart (Line with Gradient)
        if (dailyChart) dailyChart.destroy();
        const dCtx = document.getElementById('daily-chart').getContext('2d');
        const gradient = dCtx.createLinearGradient(0, 0, 0, 300);
        gradient.addColorStop(0, 'rgba(102, 252, 241, 0.4)');
        gradient.addColorStop(1, 'rgba(102, 252, 241, 0)');

        dailyChart = new Chart(dCtx, {
            type: 'line',
            data: {
                labels: data.daily.map(d => d.day),
                datasets: [{
                    label: 'Activity', data: data.daily.map(d => d.cnt),
                    borderColor: '#66fcf1', borderWidth: 3, pointBackgroundColor: '#66fcf1',
                    fill: true, backgroundColor: gradient, tension: 0.4, pointRadius: 4
                }]
            },
            options: {
                responsive: true, maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: {
                    x: { ticks: { color: textColor }, grid: { display: false } },
                    y: { ticks: { color: textColor }, grid: { color: gridColor } }
                }
            }
        });

        // 3. Tool Distribution (Doughnut)
        if (distChart) distChart.destroy();
        const pCtx = document.getElementById('dist-chart').getContext('2d');
        const toolLabels = Object.keys(data.tool_usage);
        const toolValues = Object.values(data.tool_usage);
        const colors = ['#66fcf1', '#fbbf24', '#a78bfa', '#f87171', '#60a5fa'];

        distChart = new Chart(pCtx, {
            type: 'doughnut',
            data: {
                labels: toolLabels,
                datasets: [{
                    data: toolValues, backgroundColor: colors,
                    borderWidth: 0, weight: 0.5, cutout: '70%'
                }]
            },
            options: {
                responsive: true, maintainAspectRatio: false,
                plugins: { legend: { position: 'bottom', labels: { color: textColor, font: { size: 10 }, padding: 15 } } }
            }
        });

        // 4. Detailed Event Log
        document.getElementById('analytics-recent').innerHTML = data.recent.map(r => `
            <div class="analytics-recent-row">
                <span style="font-weight:600;">${r.username}</span>
                <span class="log-badge" style="color:${getBadgeColor(r.routing)};">${(r.routing || 'GEN').split('->')[0].replace('[', '').replace(']', '')}</span>
                <span style="color:var(--primary-neon);">${r.response_time}s</span>
                <span style="opacity:0.6; font-size:0.75rem;">${r.timestamp ? r.timestamp.slice(11, 16) : 'LIVE'} · ${r.chat_id}</span>
            </div>`).join('');

        // 5. System Engine Status (Active Tools + Key Agents)
        const systemList = document.getElementById('active-system-list');
        const coreAgents = ["Researcher", "Analyzer", "Synthesis", "Router", "Optimizer"];
        const combined = [...coreAgents, ...(data.active_tools || [])];

        systemList.innerHTML = combined.map(name => `
            <div class="engine-badge">
                <div class="status-dot"></div>
                <span>${name}</span>
            </div>`).join('');
    });

    function getBadgeColor(r) {
        const rt = (r || '').toUpperCase();
        if (rt.includes('SIMPLE')) return '#60a5fa';
        if (rt.includes('TOOL')) return '#fbbf24';
        if (rt.includes('CONTENT')) return '#a78bfa';
        return '#66fcf1';
    }

    // ══════════════════════════════════════════════════════════════
    // FEATURE 6: Memory Panel
    // ══════════════════════════════════════════════════════════════
    document.getElementById('btn-memory')?.addEventListener('click', async () => {
        openModal('memory-modal');
        loadMemory();
    });

    async function loadMemory() {
        const res = await fetch('/user_memory');
        const data = await res.json();
        const list = document.getElementById('memory-list');
        if (!data.memory.length) {
            list.innerHTML = `
                <div class="neural-empty-state slide-in">
                    <div class="neural-icon-container">
                        <i class="fa-solid fa-brain"></i>
                    </div>
                    <div class="neural-empty-title">Neural Core Standby</div>
                    <div class="neural-empty-desc">No patterns stored in current sequence. Initialize new memories to establish context.</div>
                </div>`;
            return;
        }
        list.innerHTML = data.memory.map((m, idx) => `
            <div class="memory-item" style="animation-delay: ${idx * 0.08}s">
                <div class="memory-icon"><i class="fa-solid fa-microchip"></i></div>
                <div class="memory-content-wrapper">
                    <div class="memory-item-key">${m.memory_key}</div>
                    <div class="memory-item-val">${m.memory_value}</div>
                </div>
                <div class="memory-actions">
                    <button class="memory-delete-btn" data-key="${m.memory_key}" title="Forget Pattern">
                        <i class="fa-solid fa-trash-can"></i>
                    </button>
                </div>
            </div>`).join('');
        list.querySelectorAll('.memory-delete-btn').forEach(btn => {
            btn.addEventListener('click', async () => {
                const fd = new FormData(); fd.append('key', btn.dataset.key);
                await fetch('/delete_memory', { method: 'POST', body: fd });
                loadMemory();
            });
        });
    }

    document.getElementById('btn-add-memory')?.addEventListener('click', async () => {
        const key = document.getElementById('mem-key').value.trim();
        const val = document.getElementById('mem-val').value.trim();
        if (!key || !val) return;
        const fd = new FormData(); fd.append('key', key); fd.append('value', val);
        await fetch('/user_memory', { method: 'POST', body: fd });
        document.getElementById('mem-key').value = '';
        document.getElementById('mem-val').value = '';
        loadMemory();
    });

    document.getElementById('btn-clear-memory')?.addEventListener('click', async () => {
        if (!confirm("⚠️ Format Neural Core? This will wipe all cognitive patterns permanently.")) return;
        const res = await fetch('/clear_all_memory', { method: 'POST' });
        const data = await res.json();
        if (data.success) {
            showToast("Neural Core Formatted.", "warn");
            loadMemory();
        }
    });

    // ══════════════════════════════════════════════════════════════
    // FEATURE 7: Pinned Messages
    // ══════════════════════════════════════════════════════════════
    document.getElementById('btn-pinned')?.addEventListener('click', async () => {
        openModal('pinned-modal');
        const res = await fetch('/pinned_messages');
        const data = await res.json();
        const list = document.getElementById('pinned-list');
        if (!data.pinned.length) {
            list.innerHTML = '<p style="color:var(--text-main);font-size:0.85rem;text-align:center;padding:16px;">No pinned messages yet. Pin any message using the 📌 button.</p>';
            return;
        }
        list.innerHTML = data.pinned.map(p => `
            <div class="pinned-item" data-msg-id="${p.id}" data-chat-id="${p.chat_id}">
                <div class="pinned-item-meta"><i class="fa-solid fa-thumbtack"></i> ${p.chat_id} &nbsp;·&nbsp; ${p.timestamp || ''}</div>
                <div class="pinned-item-msg"><strong>You:</strong> ${p.message.substring(0, 120)}${p.message.length > 120 ? '...' : ''}</div>
                <div class="pinned-item-resp">${p.response.substring(0, 200)}${p.response.length > 200 ? '...' : ''}</div>
                <div style="font-size:0.7rem; color:var(--primary-neon); margin-top:8px; text-align:right;"><i class="fa-solid fa-arrow-right-to-bracket"></i> Go to message</div>
            </div>`).join('');
    });

    // Pinned item click to navigate
    document.getElementById('pinned-list')?.addEventListener('click', e => {
        const item = e.target.closest('.pinned-item');
        if (!item) return;
        const msgId = item.dataset.msgId;
        const chatId = item.dataset.chatId;

        if (chatId === currentChatId) {
            closeModal('pinned-modal');
            const target = document.querySelector(`[data-msg-id="${msgId}"]`);
            if (target) {
                target.scrollIntoView({ behavior: 'smooth', block: 'center' });
                target.classList.add('highlight-active');
                setTimeout(() => target.classList.remove('highlight-active'), 3000);
            } else {
                showToast('Message not found in current view.', 'warn');
            }
        } else {
            // Different workspace - redirect
            window.location.href = `/chat?chat_id=${encodeURIComponent(chatId)}&scroll_to=${msgId}`;
        }
    });

    // ══════════════════════════════════════════════════════════════
    // FEATURE 10: Profile
    // ══════════════════════════════════════════════════════════════
    document.getElementById('btn-profile')?.addEventListener('click', async () => {
        openModal('profile-modal');
        const res = await fetch('/profile');
        const data = await res.json();
        document.getElementById('profile-stats').innerHTML = `
            <div class="profile-stat-card"><div class="ps-val">${data.total_messages}</div><div class="ps-label">Queries</div></div>
            <div class="profile-stat-card"><div class="ps-val">${data.total_chats}</div><div class="ps-label">Workspaces</div></div>
            <div class="profile-stat-card"><div class="ps-val">${data.avg_response_time}s</div><div class="ps-label">Avg Time</div></div>
            <div class="profile-stat-card"><div class="ps-val">${data.files_uploaded}</div><div class="ps-label">Files</div></div>
            <div class="profile-stat-card"><div class="ps-val">${data.pinned_messages}</div><div class="ps-label">Pinned</div></div>
            <div class="profile-stat-card"><div class="ps-val" style="font-size:1rem">${data.member_since ? data.member_since.substring(0, 10) : 'N/A'}</div><div class="ps-label">Member Since</div></div>`;
        const profileLang = document.getElementById('profile-lang');
        if (profileLang) profileLang.value = data.language || 'en';
    });

    document.getElementById('btn-change-password')?.addEventListener('click', async () => {
        const fd = new FormData();
        fd.append('action', 'change_password');
        fd.append('old_password', document.getElementById('old-password').value);
        fd.append('new_password', document.getElementById('new-password').value);
        const res = await fetch('/profile', { method: 'POST', body: fd });
        const data = await res.json();
        const msg = document.getElementById('profile-msg');
        msg.style.color = data.success ? 'var(--primary-neon)' : 'var(--accent-red)';
        msg.textContent = data.message;
        if (data.success) { document.getElementById('old-password').value = ''; document.getElementById('new-password').value = ''; }
    });

    document.getElementById('btn-save-language')?.addEventListener('click', async () => {
        const lang = document.getElementById('profile-lang').value;
        const fd = new FormData(); fd.append('action', 'change_language'); fd.append('language', lang);
        await fetch('/profile', { method: 'POST', body: fd });
        if (langInput) langInput.value = lang;
        const sel = document.getElementById('lang-select');
        if (sel) sel.value = lang;
        document.getElementById('profile-msg').textContent = 'Language saved!';
        document.getElementById('profile-msg').style.color = 'var(--primary-neon)';
    });

    // ══════════════════════════════════════════════════════════════
    // Pipeline Badge + Trace helpers
    // ══════════════════════════════════════════════════════════════
    function getBadgeClass(routing) {
        const r = (routing || '').toUpperCase();
        if (r.includes('SIMPLE')) return 'badge-simple';
        if (r.includes('TOOL')) return 'badge-tool';
        if (r.includes('CONTENT')) return 'badge-content';
        if (r.includes('MEDICAL')) return 'badge-medical';
        if (r.includes('DECISION')) return 'badge-decision';
        if (r.includes('DEBUG')) return 'badge-debug';
        if (r.includes('SHOPPING')) return 'badge-shopping';
        return 'badge-general';
    }

    function getPipelineSteps(routing) {
        const r = (routing || '').toUpperCase();
        if (r.includes('SIMPLE')) return ['🧠 Fast LLM', '✅ Direct Answer'];
        if (r.includes('TOOL')) return ['🔍 Research Agent', '🛠️ Tool Execution', '✅ Output'];
        if (r.includes('CONTENT')) return ['✍️ Generate Content', '🔍 Evaluate Quality', '⚡ Optimize', '✅ Final'];
        if (r.includes('MEDICAL')) return ['🏥 Initial Check', '🩺 Specialist Review', '🔗 Merge', '✅ Medical Guidance'];
        if (r.includes('DECISION')) return ['🔍 Research', '📊 Analyze', '⚖️ Risk Eval', '📋 Compare', '🧠 Decision Engine', '✅ Recommendation'];
        if (r.includes('DEBUG')) return ['🐛 Detect Error', '🔍 Find Cause', '🔧 Generate Fix', '✅ Solution'];
        if (r.includes('SHOPPING')) return ['🛒 Search Items', '💰 Get Prices', '⭐ Check Reviews', '🔗 Merge', '✅ Best Pick'];
        if (r.includes('PARALLEL')) return ['🔍 Research', '⚡ Parallel Processing', '🔗 Merge Results', '📝 Summarize', '✅ Final'];
        return ['🔍 Research', '📊 Analyze', '📝 Summarize', '✅ Final'];
    }

    function addPipelineBadge(routing, elapsed) {
        const badge = document.createElement('div');
        badge.className = `pipeline-badge ${getBadgeClass(routing)} slide-in`;
        badge.innerHTML = `<i class="fa-solid fa-route"></i> ${routing}` +
            (elapsed ? `<span class="response-timer">⏱ ${elapsed}s</span>` : '');
        chatFlow.appendChild(badge);
    }

    function buildDynamicTrace(routing) {
        const trace = document.createElement('div');
        trace.className = 'agent-trace slide-in';
        const steps = getPipelineSteps(routing);
        trace.innerHTML = `
            <div class="trace-header">Executing: ${(routing || 'Agent Pipeline').split('->')[0]}</div>
            <ul class="trace-list">
                ${steps.map((s, i) => `<li class="step dyn-step-${i}">${s}</li>`).join('')}
            </ul>`;
        chatFlow.appendChild(trace);
        return trace;
    }

    function animateTrace(trace, onComplete) {
        const steps = [...trace.querySelectorAll('.step')];
        let i = 0;
        function next() {
            if (i > 0) steps[i - 1].classList.replace('active', 'done');
            if (i < steps.length) { steps[i].classList.add('active'); i++; setTimeout(next, 200); }
            else if (onComplete) onComplete();
        }
        next();
    }

    function injectToolsInTrace(traceBlock, tools) {
        const list = traceBlock.querySelector('.trace-list');
        if (!list) return;
        const unique = [...new Map(tools.map(t => [t.tool, t])).values()];
        const li = document.createElement('li');
        li.className = 'step step-tool-inline slide-in done';
        li.innerHTML = `🛠️ Tools: ${unique.map(t => `<span class="tool-inline-name"><i class="fa-solid fa-wrench"></i> ${t.tool}</span>`).join(' | ')}`;
        list.appendChild(li);
    }

    // ══════════════════════════════════════════════════════════════
    // FEATURE 3: Copy Response + FEATURE 9: TTS
    // ══════════════════════════════════════════════════════════════
    let ttsUtterance = null;

    function attachAiActions(aiMsgEl) {
        if (!aiMsgEl) return;
        const actionsDiv = aiMsgEl.querySelector('.ai-msg-actions');
        if (!actionsDiv) return;

        const copyBtn = actionsDiv.querySelector('.copy-response-btn');
        const ttsBtn = actionsDiv.querySelector('.tts-btn');
        const content = aiMsgEl.querySelector('.message-content');

        copyBtn?.addEventListener('click', () => {
            const text = content ? content.innerText : '';
            navigator.clipboard.writeText(text);
            copyBtn.innerHTML = '<i class="fa-solid fa-check"></i>';
            setTimeout(() => { copyBtn.innerHTML = '<i class="fa-regular fa-copy"></i>'; }, 2000);
        });

        ttsBtn?.addEventListener('click', () => {
            const ttsEnabled = document.getElementById('toggle-tts')?.checked !== false;
            if (!ttsEnabled) return;
            if (window.speechSynthesis.speaking) {
                window.speechSynthesis.cancel();
                document.querySelectorAll('.tts-btn').forEach(b => b.classList.remove('speaking'));
                return;
            }
            const text = content ? content.innerText : '';
            ttsUtterance = new SpeechSynthesisUtterance(text);
            ttsUtterance.rate = 0.95;
            ttsUtterance.onstart = () => ttsBtn.classList.add('speaking');
            ttsUtterance.onend = () => ttsBtn.classList.remove('speaking');
            window.speechSynthesis.speak(ttsUtterance);
        });
    }

    function addAiResponse(markdownText) {
        const div = document.createElement('div');
        div.className = 'message ai-message slide-in';
        const html = typeof marked !== 'undefined' ? marked.parse(markdownText) : markdownText;
        div.innerHTML = `
            <div class="avatar ai-avatar"><i class="fa-solid fa-robot"></i></div>
            <div class="msg-col">
                <div class="ai-msg-actions">
                    <span class="ai-name"><i class="fa-solid fa-microchip"></i> ORCHESTAI</span>
                    <div class="ai-btn-group">
                        <button class="ai-action-btn copy-response-btn" title="Copy"><i class="fa-regular fa-copy"></i></button>
                        <button class="ai-action-btn tts-btn" title="Read aloud"><i class="fa-solid fa-volume-high"></i></button>
                    </div>
                </div>
                <div class="message-content glass-pill">${html}</div>
            </div>`;
        chatFlow.appendChild(div);
        attachAiActions(div);
    }

    // ══════════════════════════════════════════════════════════════
    // FEATURE 7: Pin Message (click handler on chat flow)
    // ══════════════════════════════════════════════════════════════
    chatFlow.addEventListener('click', async e => {
        if (!e.target.classList.contains('pin-btn')) return;
        const msgRow = e.target.closest('.user-message');
        const msgId = msgRow?.getAttribute('data-msg-id');
        if (!msgId) {
            showToast('⏳ Message is still being saved. Please wait a moment and try again.', 'warn');
            return;
        }
        const isPinned = String(e.target.dataset.pinned) === '1';
        const newState = isPinned ? 0 : 1;
        const fd = new FormData(); fd.append('msg_id', msgId); fd.append('state', newState);
        const res = await fetch('/pin_message', { method: 'POST', body: fd });
        const data = await res.json();
        if (data.success) {
            e.target.dataset.pinned = String(newState);
            e.target.title = newState ? 'Unpin' : 'Pin';
            e.target.classList.toggle('pinned-active', !!newState);
            showToast(newState ? '📌 Message pinned!' : '📌 Message unpinned.', 'info');
        } else {
            showToast('❌ Failed to pin message.', 'error');
        }
    });

    // ══════════════════════════════════════════════════════════════
    // MAIN SUBMIT
    // ══════════════════════════════════════════════════════════════
    chatForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const msg = userInput.value.trim();
        const lang = langInput?.value || 'en';
        if (!msg) return;

        // Build final prompt with language instruction
        let finalMsg = msg;
        if (lang !== 'en') {
            const langNames = { hi: 'Hindi', mr: 'Marathi', es: 'Spanish', fr: 'French', de: 'German', ja: 'Japanese', ar: 'Arabic' };
            finalMsg = `${msg}\n\n[INSTRUCTION: Please respond in ${langNames[lang] || lang}]`;
        }

        const activeItem = document.querySelector(`.chat-item[data-chat-id="${currentChatId}"]`);
        if (activeItem) chatHistoryList.prepend(activeItem);

        addUserMessage(msg);
        userInput.value = '';
        scrollToBottom();

        // Loading trace
        const loadingTrace = document.createElement('div');
        loadingTrace.className = 'agent-trace slide-in';
        loadingTrace.innerHTML = `
            <div class="trace-header">Routing to agent pipeline...</div>
            <ul class="trace-list">
                <li class="step active"><i class="fa-solid fa-route"></i> Supervisor analyzing <span class="dot pulse" style="display:inline-block;width:6px;height:6px;border-radius:50%;background:var(--primary-neon);margin-left:6px;"></span></li>
            </ul>`;
        chatFlow.appendChild(loadingTrace);
        scrollToBottom();

        try {
            const fd = new FormData();
            fd.append('chat_id', currentChatId);
            fd.append('message', finalMsg);
            if (pdfUpload?.files.length) fd.append('pdf', pdfUpload.files[0]);

            const response = await fetch('/send_message', { method: 'POST', body: fd });
            const data = await response.json();

            const lastUser = chatFlow.querySelector('.user-message:last-of-type');
            if (lastUser && data.id) lastUser.setAttribute('data-msg-id', data.id);

            loadingTrace.remove();

            // Feature 2: Response timer + Feature badge
            addPipelineBadge(data.routing || 'Agent Pipeline', data.response_time);

            const realTrace = buildDynamicTrace(data.routing || '');
            if (data.tools_used?.length) injectToolsInTrace(realTrace, data.tools_used);
            scrollToBottom();

            animateTrace(realTrace, () => {
                addAiResponse(data.answer || '(No response)');
                if (data.email?.trim()) addEmailCard(data.email);
                scrollToBottom();
            });

            if (pdfUpload) { pdfUpload.value = ""; fileIndicator.style.display = 'none'; }

            // Auto-rename
            const isGeneric = /^(chat|workspace)\s*\d*$/i.test(currentChatId.trim());
            if (data.suggested_name && isGeneric) {
                const fd2 = new FormData(); fd2.append('old_id', currentChatId); fd2.append('new_id', data.suggested_name);
                fetch('/rename_workspace', { method: 'POST', body: fd2 }).then(r => r.json()).then(res => {
                    if (!res.success) return;
                    const newId = data.suggested_name;
                    document.querySelectorAll(`.chat-item[data-chat-id="${currentChatId}"]`).forEach(item => {
                        item.setAttribute('data-chat-id', newId);
                        item.querySelector('span').innerText = newId;
                        chatHistoryList.prepend(item);
                        const link = item.closest('a');
                        if (link) { const u = new URL(link.href, location.origin); u.searchParams.set('chat_id', newId); link.href = u.pathname + u.search; }
                    });
                    currentChatId = newId;
                    if (chatIdInput) chatIdInput.value = newId;
                });
            }

        } catch (err) {
            console.error(err);
            loadingTrace.remove();
            addAiResponse('Connection error. Please check the server and try again.');
            scrollToBottom();
        }
    });

    // ── Message Edit ──────────────────────────────────────────────────────
    chatFlow.addEventListener('click', e => {
        if (!e.target.classList.contains('edit-btn')) return;
        const msgRow = e.target.closest('.user-message');
        const msgId = msgRow.getAttribute('data-msg-id');
        const origText = msgRow.querySelector('.msg-text').innerText;
        const glassPill = msgRow.querySelector('.glass-pill');
        const origHTML = glassPill.innerHTML;

        glassPill.innerHTML = `
            <textarea class="edit-input-area">${origText}</textarea>
            <div class="edit-actions">
                <button class="edit-cancel-btn">Cancel</button>
                <button class="edit-save-btn">Save & Regenerate</button>
            </div>`;
        const ta = glassPill.querySelector('textarea');
        ta.focus(); ta.setSelectionRange(ta.value.length, ta.value.length);
        glassPill.querySelector('.edit-cancel-btn').addEventListener('click', () => { glassPill.innerHTML = origHTML; });
        glassPill.querySelector('.edit-save-btn').addEventListener('click', () => {
            const newText = ta.value.trim();
            if (!newText || newText === origText) { glassPill.innerHTML = origHTML; return; }
            saveEdit(msgId, newText, msgRow, origHTML);
        });
    });

    async function saveEdit(msgId, newText, msgRow, fallbackHTML) {
        const glassPill = msgRow.querySelector('.glass-pill');
        glassPill.innerHTML = `<p><i class="fa-solid fa-spinner fa-spin"></i> Regenerating...</p>`;
        const fd = new FormData(); fd.append('msg_id', msgId); fd.append('message', newText);
        try {
            const res = await fetch('/edit_message', { method: 'POST', body: fd });
            const data = await res.json();
            if (data.success) {
                glassPill.innerHTML = `<div class="msg-text-container"><p class="msg-text">${newText}</p><div class="msg-actions"><i class="fa-solid fa-pen-to-square edit-btn" title="Edit"></i><i class="fa-solid fa-thumbtack pin-btn" title="Pin" data-pinned="0"></i></div></div>`;
                let aiRow = msgRow.nextElementSibling;
                while (aiRow && !aiRow.classList.contains('ai-message')) aiRow = aiRow.nextElementSibling;
                if (aiRow) {
                    aiRow.querySelector('.message-content').innerHTML = typeof marked !== 'undefined' ? marked.parse(data.new_response) : data.new_response;
                    aiRow.style.animation = 'none'; void aiRow.offsetWidth; aiRow.style.animation = 'flashText 1s ease';
                }
            } else { alert("Error updating message."); glassPill.innerHTML = fallbackHTML; }
        } catch (err) { console.error(err); alert("Connection error."); glassPill.innerHTML = fallbackHTML; }
    }

    // ── DOM helpers ───────────────────────────────────────────────────────
    function addUserMessage(text, id = null) {
        const div = document.createElement('div');
        div.className = 'message user-message slide-in';
        if (id) div.setAttribute('data-msg-id', id);
        div.innerHTML = `
            <div class="avatar user-avatar"><i class="fa-solid fa-user-astronaut"></i></div>
            <div class="message-content glass-pill">
                <div class="msg-text-container">
                    <p class="msg-text">${text}</p>
                    <div class="msg-actions">
                        <i class="fa-solid fa-pen-to-square edit-btn" title="Edit"></i>
                        <i class="fa-solid fa-thumbtack pin-btn" title="Pin" data-pinned="0"></i>
                    </div>
                </div>
            </div>`;
        chatFlow.appendChild(div);
    }

    function addEmailCard(emailText) {
        const template = document.getElementById('email-card-template');
        const clone = template.content.cloneNode(true);
        const card = clone.querySelector('.email-card');
        card.querySelector('.email-body').innerHTML = emailText.replace(/\n/g, '<br>');
        card.querySelector('.copy-btn').addEventListener('click', () => {
            navigator.clipboard.writeText(emailText);
        });
        chatFlow.appendChild(card);
    }

    // ── Toast Notification helper ─────────────────────────────────────────
    function showToast(msg, type = 'info') {
        const toast = document.createElement('div');
        const colors = { info: 'var(--primary-neon)', warn: '#fbbf24', error: 'var(--accent-red)' };
        toast.style.cssText = `
            position:fixed;bottom:90px;left:50%;transform:translateX(-50%) translateY(20px);
            background:var(--glass-bg);border:1px solid ${colors[type] || colors.info};
            color:var(--text-bright);padding:10px 20px;border-radius:12px;
            font-size:0.85rem;z-index:9999;pointer-events:none;
            box-shadow:0 4px 20px rgba(0,0,0,0.4);opacity:0;
            transition:all 0.3s ease;backdrop-filter:blur(12px);`;
        toast.textContent = msg;
        document.body.appendChild(toast);
        requestAnimationFrame(() => {
            toast.style.opacity = '1';
            toast.style.transform = 'translateX(-50%) translateY(0)';
        });
        setTimeout(() => {
            toast.style.opacity = '0';
            toast.style.transform = 'translateX(-50%) translateY(20px)';
            setTimeout(() => toast.remove(), 300);
        }, 2800);
    }

});