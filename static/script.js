document.addEventListener('DOMContentLoaded', () => {
    // ---- THEME TOGGLER ---- //
    const themeToggle = document.getElementById('theme-toggle');
    if (themeToggle) {
        // Check local storage for preference
        if (localStorage.getItem('theme') === 'light') {
            document.body.classList.add('light-mode');
        }

        themeToggle.addEventListener('click', () => {
            document.body.classList.toggle('light-mode');
            const newTheme = document.body.classList.contains('light-mode') ? 'light' : 'dark';
            localStorage.setItem('theme', newTheme);
        });
    }

    // ---- DASHBOARD SPECIFIC LOGIC ---- //
    const chatForm = document.getElementById('chat-form');
    if (!chatForm) return; // If on login page, logic below isn't needed.

    const userInput = document.getElementById('user-msg');
    const chatFlow = document.getElementById('chat-flow');
    let currentChatId = "Chat 1";

    const scrollToBottom = () => { chatFlow.scrollTop = chatFlow.scrollHeight; };

    // ---- SETTINGS MODAL ---- //
    const btnSettings = document.getElementById('btn-settings');
    const modalSettings = document.getElementById('settings-modal');
    const btnCloseSettings = document.getElementById('close-settings');

    if (btnSettings) {
        btnSettings.addEventListener('click', () => { modalSettings.classList.add('show'); });
        btnCloseSettings.addEventListener('click', () => { modalSettings.classList.remove('show'); });
        modalSettings.addEventListener('click', (e) => {
            if (e.target === modalSettings) modalSettings.classList.remove('show');
        });
    }

    // ---- VOICE DICTATION (WEB SPEECH API) ---- //
    const voiceBtn = document.getElementById('voice-btn');
    if (voiceBtn) {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        if (SpeechRecognition) {
            const recognition = new SpeechRecognition();
            recognition.continuous = false;
            recognition.interimResults = false;

            recognition.onstart = () => {
                voiceBtn.innerHTML = '<i class="fa-solid fa-microphone-lines pulse" style="color:var(--accent-red)"></i>';
                userInput.placeholder = "Listening...";
            };

            recognition.onresult = (event) => {
                const transcript = event.results[0][0].transcript;
                userInput.value = transcript;
            };

            recognition.onend = () => {
                voiceBtn.innerHTML = '<i class="fa-solid fa-microphone"></i>';
                userInput.placeholder = "Command the orchestration agents...";
                // optionally auto-submit: if(userInput.value) chatForm.dispatchEvent(new Event('submit'));
            };

            voiceBtn.addEventListener('click', () => { recognition.start(); });
        } else {
            voiceBtn.style.display = 'none'; // Browser doesn't support it
        }
    }

    // ---- NEW WORKSPACE / CHAT HISTORY TABS ---- //
    const btnNewChat = document.getElementById('btn-new-chat');
    const chatHistoryList = document.getElementById('chat-history-list');

    btnNewChat.addEventListener('click', () => {
        const newId = `Chat ${Date.now().toString().slice(-4)}`;
        // Clear chat area logically
        document.querySelectorAll('.message:not(.slide-in)').forEach(el => el.remove());

        // Add To Sidebar
        const newItem = document.createElement('div');
        newItem.className = 'chat-item active';
        newItem.innerHTML = `
            <i class="fa-regular fa-message"></i>
            <span>Workspace ${newId}</span>
            <i class="fa-solid fa-trash delete-chat hover-red"></i>
        `;

        // Deactivate others
        document.querySelectorAll('.chat-item').forEach(el => el.classList.remove('active'));
        chatHistoryList.prepend(newItem);
        currentChatId = newId;

        // Make chat clear (except welcome message)
        chatFlow.innerHTML = `
            <div class="message ai-message slide-in">
                <div class="avatar ai-avatar"><i class="fa-solid fa-robot"></i></div>
                <div class="message-content glass-pill">
                    <p>New strictly classified workspace initialized. Agents standing by.</p>
                </div>
            </div>
        `;
    });

    // ---- EXPORT CHAT ---- //
    const btnExport = document.getElementById('btn-export');
    if (btnExport) {
        btnExport.addEventListener('click', () => {
            let exportText = "# AI Orchestration Execution Log\n\n";
            const messages = chatFlow.querySelectorAll('.glass-pill');

            messages.forEach(msgNode => {
                const isAI = msgNode.parentElement.classList.contains('ai-message');
                exportText += isAI ? "### OrchestAI:\n" : "### User Query:\n";
                exportText += msgNode.innerText + "\n\n";
            });

            // Create download
            const blob = new Blob([exportText], { type: 'text/markdown' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `OrchestAI_Log_${new Date().getTime()}.md`;
            a.click();
            URL.revokeObjectURL(url);
        });
    }

    // ---- MAIN AI SUBMISSION LOOP ---- //
    chatForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const msg = userInput.value.trim();
        if (!msg) return;

        addUserMessage(msg);
        userInput.value = '';
        scrollToBottom();

        const traceBlock = addAgentTrace();
        scrollToBottom();

        const steps = traceBlock.querySelectorAll('.step');
        activateStep(steps[0]);

        try {
            const formData = new FormData();
            formData.append('chat_id', currentChatId);
            formData.append('message', msg);

            const pdfInput = document.getElementById('pdf-upload');
            if (pdfInput.files.length > 0) formData.append('pdf', pdfInput.files[0]);

            setTimeout(() => { finishStep(steps[0]); activateStep(steps[1]); }, 800);

            // Fetch to backend
            const response = await fetch('/send_message', {
                method: 'POST',
                body: formData
            });
            const data = await response.json();

            setTimeout(() => {
                finishStep(steps[1]);
                // Inject tools inline inside trace, under Research step
                if (data.tools_used && data.tools_used.length > 0) {
                    injectToolsInTrace(traceBlock, data.tools_used);
                }
                if (data.email && data.email.trim() !== "") {
                    activateStep(steps[2]);
                    setTimeout(() => { finishStep(steps[2]); activateStep(steps[3]); }, 800);
                    setTimeout(() => {
                        finishStep(steps[3]);
                        addAiResponse(data.response);
                        addEmailCard(data.email);
                        scrollToBottom();
                    }, 1600);
                } else {
                    steps[2].style.display = 'none';
                    steps[3].style.display = 'none';
                    addAiResponse(data.response);
                    scrollToBottom();
                }
            }, 1600);

        } catch (error) {
            console.error(error);
            // Simulate fake success for frontend testing if backend fails
            setTimeout(() => {
                finishStep(steps[1]);
                steps[2].style.display = 'none';
                steps[3].style.display = 'none';

                // Demo markdown parsing
                const testMarkdown = `**I cannot reach your Python backend server.** Please verify \`app.py\` is running via:
                \n\`\`\`bash\npython app.py\n\`\`\`\n\nI received your query though: "${msg}"`;

                addAiResponse(testMarkdown);
                scrollToBottom();
            }, 1500);
        }
    });

    // ---- DOM HELPERS ---- //
    function addUserMessage(text) {
        const div = document.createElement('div');
        div.className = 'message user-message slide-in';
        div.innerHTML = `
            <div class="avatar user-avatar"><i class="fa-solid fa-user-astronaut"></i></div>
            <div class="message-content glass-pill"><p>${text}</p></div>
        `;
        chatFlow.appendChild(div);
    }

    function addAgentTrace() {
        const template = document.getElementById('agent-steps-template');
        const clone = template.content.cloneNode(true);
        const div = clone.querySelector('.agent-trace');
        chatFlow.appendChild(div);
        return div;
    }

    function activateStep(stepEl) {
        stepEl.classList.add('active');
        stepEl.innerHTML = stepEl.innerHTML.replace('...', '<span class="pulse dot inline-block" style="display:inline-block; margin-left:8px;"></span>');
    }

    function finishStep(stepEl) {
        stepEl.classList.remove('active');
        stepEl.classList.add('done');
        stepEl.innerHTML = stepEl.innerHTML.replace('<span class="pulse dot inline-block" style="display:inline-block; margin-left:8px;"></span>', ' ✅');
    }

    function addAiResponse(markdownText) {
        const div = document.createElement('div');
        div.className = 'message ai-message slide-in';
        // Parse markdown -> HTML securely
        const parsedHTML = typeof marked !== 'undefined' ? marked.parse(markdownText) : markdownText;

        div.innerHTML = `
            <div class="avatar ai-avatar"><i class="fa-solid fa-robot"></i></div>
            <div class="message-content glass-pill">
                ${parsedHTML}
            </div>
        `;
        chatFlow.appendChild(div);
    }

    // Injects a single summary line of unique tools used inside the trace block
    function injectToolsInTrace(traceBlock, tools) {
        const list = traceBlock.querySelector('.trace-list');
        const researchStep = list.querySelector('.step-research');

        // Deduplicate — only show each tool name once
        const uniqueTools = [...new Map(tools.map(t => [t.tool, t])).values()];

        const li = document.createElement('li');
        li.className = 'step step-tool-inline slide-in done';
        const toolNames = uniqueTools.map(t =>
            `<span class="tool-inline-name"><i class="fa-solid fa-wrench tool-icon-inline"></i> ${t.tool}</span>`
        ).join(' &nbsp;|&nbsp; ');
        li.innerHTML = `🛠️ Tools used: ${toolNames}`;

        // Insert once, right after the research step
        researchStep.insertAdjacentElement('afterend', li);
    }

    function addEmailCard(emailText) {
        const template = document.getElementById('email-card-template');
        const clone = template.content.cloneNode(true);
        const card = clone.querySelector('.email-card');
        card.querySelector('.email-body').innerHTML = emailText.replace(/\n/g, '<br>');

        const copyBtn = card.querySelector('.copy-btn');
        copyBtn.addEventListener('click', () => {
            navigator.clipboard.writeText(emailText);
            copyBtn.innerHTML = '<i class="solid fa-check"></i> Copied';
            setTimeout(() => { copyBtn.innerHTML = '<i class="fa-regular fa-copy"></i> Copy'; }, 2000);
        });
        chatFlow.appendChild(card);
    }
});
