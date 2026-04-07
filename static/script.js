document.addEventListener('DOMContentLoaded', () => {
    // ---- PARSE HISTORICAL MARKDOWN ---- //
    document.querySelectorAll('.message-content[data-markdown]').forEach(el => {
        let mdText = el.getAttribute('data-markdown');
        el.innerHTML = typeof marked !== 'undefined' ? marked.parse(mdText) : mdText;
        el.removeAttribute('data-markdown');
    });

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
    const chatIdInput = document.getElementById('chat_id');
    let currentChatId = chatIdInput ? chatIdInput.value : "Chat 1";

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
        newItem.setAttribute('data-chat-id', newId);
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

    // ---- CLEAR CHAT ---- //
    const btnClear = document.getElementById('btn-clear');
    if (btnClear) {
        btnClear.addEventListener('click', () => {
            if (confirm(`Are you sure you want to clear all history in ${currentChatId}?`)) {
                const formData = new FormData();
                formData.append('chat_id', currentChatId);
                
                fetch('/clear_chat', {
                    method: 'POST',
                    body: formData
                })
                .then(r => r.json())
                .then(res => {
                    if (res.success) {
                        window.location.reload();
                    } else {
                        alert("Error clearing workspace.");
                    }
                })
                .catch(err => {
                    console.error(err);
                    alert("Error clearing workspace.");
                });
            }
        });
    }

    // ---- PDF ATTACHMENT HANDLING ---- //
    const pdfUpload = document.getElementById('pdf-upload');
    const fileIndicator = document.getElementById('file-indicator');
    const fileNameText = document.getElementById('file-name');
    const btnRemoveFile = document.getElementById('remove-file-btn');

    if (pdfUpload) {
        pdfUpload.addEventListener('change', () => {
            if (pdfUpload.files && pdfUpload.files[0]) {
                const file = pdfUpload.files[0];
                const iconClass = getFileIcon(file.name);
                fileIndicator.innerHTML = `
                    <i class="fa-solid ${iconClass}"></i> <span id="file-name">${file.name}</span>
                    <i class="fa-solid fa-xmark remove-file" id="remove-file-btn"></i>
                `;
                fileIndicator.style.display = 'flex';
                
                // Re-bind remove button since innerHTML was reset
                document.getElementById('remove-file-btn').addEventListener('click', () => {
                    pdfUpload.value = "";
                    fileIndicator.style.display = 'none';
                });
                scrollToBottom();
            } else {
                fileIndicator.style.display = 'none';
            }
        });
    }

    function getFileIcon(filename) {
        const ext = filename.split('.').pop().toLowerCase();
        if (ext === 'pdf') return 'fa-file-pdf';
        if (ext === 'docx' || ext === 'doc') return 'fa-file-word';
        if (ext === 'xlsx' || ext === 'xls') return 'fa-file-excel';
        if (ext === 'pptx') return 'fa-file-powerpoint';
        if (ext === 'csv') return 'fa-file-csv';
        return 'fa-file-lines';
    }

    // Previous remove listener is now handled inside the change listener

    // ---- MAIN AI SUBMISSION LOOP ---- //
    chatForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const msg = userInput.value.trim();
        if (!msg) return;

        // Move current chat to top of sidebar
        const currentItem = document.querySelector(`.chat-item[data-chat-id="${currentChatId}"]`);
        if (currentItem) {
            chatHistoryList.prepend(currentItem);
        }

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

            setTimeout(() => { finishStep(steps[0]); activateStep(steps[1]); }, 200);

            // Fetch to backend
            const response = await fetch('/send_message', {
                method: 'POST',
                body: formData
            });
            const data = await response.json();
            
            // Set the ID of the message we just sent
            const lastUserMsg = document.querySelector('.user-message:last-of-type');
            if (lastUserMsg && data.id) {
                lastUserMsg.setAttribute('data-msg-id', data.id);
            }

            // --- AUTO-RENAME LOGIC --- //
            const currentName = currentChatId.toLowerCase();
            const isGeneric = currentName.startsWith('chat') || currentName.startsWith('workspace') || !isNaN(currentName) || currentName === 'chat 1';

            if (data.suggested_name && isGeneric) {
                const oldId = currentChatId;
                const newId = data.suggested_name;
                
                const renameForm = new FormData();
                renameForm.append('old_id', oldId);
                renameForm.append('new_id', newId);
                
                fetch('/rename_workspace', { method: 'POST', body: renameForm })
                    .then(r => r.json())
                    .then(res => {
                        if (res.success) {
                            // Update sidebar visually
                            const sidebarItems = document.querySelectorAll('.chat-item');
                            sidebarItems.forEach(item => {
                                const itemId = item.getAttribute('data-chat-id');
                                if (itemId === oldId) {
                                    item.setAttribute('data-chat-id', newId);
                                    item.querySelector('span').innerText = newId;
                                    
                                    // Ensure it stays at the top after rename
                                    chatHistoryList.prepend(item);

                                    // Update parent link
                                    const parentA = item.closest('a');
                                    if (parentA) {
                                        const url = new URL(parentA.href, window.location.origin);
                                        url.searchParams.set('chat_id', newId);
                                        parentA.href = url.pathname + url.search;
                                    }
                                }
                            });
                            
                            // Update current state
                            currentChatId = newId;
                            const chatIdInput = document.getElementById('chat_id');
                            if (chatIdInput) chatIdInput.value = newId;
                            
                            // Update header text if it contains the ID
                            const headerH3 = document.querySelector('.chat-header h3');
                            // (Optional: if the header displays the chat name, update it here)
                        }
                    });
            }

            // Clear PDF after successful send
            pdfUpload.value = "";
            fileIndicator.style.display = 'none';

            setTimeout(() => {
                finishStep(steps[1]);
                // Inject tools inline inside trace, under Research step
                if (data.tools_used && data.tools_used.length > 0) {
                    injectToolsInTrace(traceBlock, data.tools_used);
                }
                
                // --- SMART TRACE DISPLAY ---
                // If it was COMPLEX, show the full pipeline with faster timing
                if (data.routing && data.routing.includes('COMPLEX')) {
                    activateStep(steps[2]);
                    setTimeout(() => { finishStep(steps[2]); activateStep(steps[3]); }, 100);
                    setTimeout(() => {
                        finishStep(steps[3]);
                        addAiResponse(data.answer); 
                        if (data.email && data.email.trim() !== "") addEmailCard(data.email);
                        scrollToBottom();
                    }, 300);
                } else {
                    // Just RESEARCH - skip analysis/synthesis
                    steps[2].style.display = 'none';
                    steps[3].style.display = 'none';
                    addAiResponse(data.answer);
                    scrollToBottom();
                }
            }, 100);

        } catch (error) {
            console.error(error);
            // ... error handling ...
        }
    });

    // ---- MESSAGE EDITING LOGIC ---- //
    chatFlow.addEventListener('click', (e) => {
        if (e.target.classList.contains('edit-btn')) {
            const msgRow = e.target.closest('.user-message');
            const msgId = msgRow.getAttribute('data-msg-id');
            const msgTextEl = msgRow.querySelector('.msg-text');
            const originalText = msgTextEl.innerText;

            // Enter Edit Mode
            const glassPill = msgRow.querySelector('.glass-pill');
            const originalHTML = glassPill.innerHTML;

            glassPill.innerHTML = `
                <textarea class="edit-input-area">${originalText}</textarea>
                <div class="edit-actions">
                    <button class="edit-cancel-btn">Cancel</button>
                    <button class="edit-save-btn">Save</button>
                </div>
            `;
            
            const textarea = glassPill.querySelector('textarea');
            textarea.focus();
            textarea.setSelectionRange(textarea.value.length, textarea.value.length);

            // Cancel Button
            glassPill.querySelector('.edit-cancel-btn').addEventListener('click', () => {
                glassPill.innerHTML = originalHTML;
            });

            // Save Button
            glassPill.querySelector('.edit-save-btn').addEventListener('click', () => {
                const newText = textarea.value.trim();
                if (!newText || newText === originalText) {
                    glassPill.innerHTML = originalHTML;
                    return;
                }
                saveEdit(msgId, newText, msgRow, originalHTML);
            });
        }
    });

    async function saveEdit(msgId, newText, msgRow, fallbackHTML) {
        const glassPill = msgRow.querySelector('.glass-pill');
        glassPill.innerHTML = `<p><i class="fa-solid fa-spinner fa-spin"></i> Regenerating response...</p>`;

        const formData = new FormData();
        formData.append('msg_id', msgId);
        formData.append('message', newText);

        try {
            const response = await fetch('/edit_message', { method: 'POST', body: formData });
            const data = await response.json();

            if (data.success) {
                // Update User Message Text
                msgRow.querySelector('.glass-pill').innerHTML = `
                    <div class="msg-text-container">
                        <p class="msg-text">${newText}</p>
                        <i class="fa-solid fa-pen-to-square edit-btn" title="Edit message"></i>
                    </div>
                `;

                // Update the AI response and Tools (the siblings after this user-message)
                let traceRow = null;
                let aiRow = msgRow.nextElementSibling;
                
                // Scan siblings for trace and AI message
                while (aiRow && !aiRow.classList.contains('ai-message')) {
                    if (aiRow.classList.contains('agent-trace')) traceRow = aiRow;
                    aiRow = aiRow.nextElementSibling;
                }

                if (aiRow) {
                    const aiContent = aiRow.querySelector('.message-content');
                    const parsedHTML = typeof marked !== 'undefined' ? marked.parse(data.new_response) : data.new_response;
                    aiContent.innerHTML = parsedHTML;
                    
                    // Update Tools if trace exists and new tools were used
                    if (traceRow && data.tools_used && data.tools_used.length > 0) {
                        // Remove old tool list if exists
                        const oldToolLine = traceRow.querySelector('.step-tool-inline');
                        if (oldToolLine) oldToolLine.remove();
                        injectToolsInTrace(traceRow, data.tools_used);
                    }
                    
                    // Show a quick flash to indicate update
                    aiRow.style.animation = 'none';
                    void aiRow.offsetWidth;
                    aiRow.style.animation = 'flashText 1s ease';
                }
            } else {
                alert("Error updating message.");
                glassPill.innerHTML = fallbackHTML;
            }
        } catch (err) {
            console.error(err);
            alert("Connection error.");
            glassPill.innerHTML = fallbackHTML;
        }
    }

    // ---- DOM HELPERS ---- //
    function addUserMessage(text, id = null) {
        const div = document.createElement('div');
        div.className = 'message user-message slide-in';
        if (id) div.setAttribute('data-msg-id', id);
        div.innerHTML = `
            <div class="avatar user-avatar"><i class="fa-solid fa-user-astronaut"></i></div>
            <div class="message-content glass-pill">
                <div class="msg-text-container">
                    <p class="msg-text">${text}</p>
                    <i class="fa-solid fa-pen-to-square edit-btn" title="Edit message"></i>
                </div>
            </div>
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
