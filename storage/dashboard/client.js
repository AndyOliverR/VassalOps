const chatStream = document.getElementById('chatStream');
const inputField = document.getElementById('userInputField');
const runButton = document.getElementById('runButton');
const toggleSettingsBtn = document.getElementById('toggleSettingsBtn');
const closeSettingsBtn = document.getElementById('closeSettingsBtn');
const clearBgBtn = document.getElementById('clearBgBtn');
const settingsPanel = document.getElementById('settingsPanel');
const dutiesPanel = document.getElementById('dutiesPanel');
const toggleDutiesBtn = document.getElementById('toggleDutiesBtn');
const closeDutiesBtn = document.getElementById('closeDutiesBtn');
const refreshDutiesBtn = document.getElementById('refreshDutiesBtn');
const approvePlaylistBtn = document.getElementById('approvePlaylistBtn');
const skipPlaylistBtn = document.getElementById('skipPlaylistBtn');
const dutiesList = document.getElementById('dutiesList');
const dutiesStatus = document.getElementById('dutiesStatus');
const dutiesHint = document.getElementById('dutiesHint');
const runProgressTitle = document.getElementById('runProgressTitle');

let currentUsername = localStorage.getItem('vassal_user_name') || 'AnDY';
let currentUserAvatarBase64 = localStorage.getItem('vassal_user_avatar_b64') || '';
let currentWallpaperBase64 = localStorage.getItem('vassal_wallpaper_b64') || '';
let approvalInFlight = false;
let playlistInFlight = false;

document.getElementById('settingUsername').value = currentUsername;
if (currentWallpaperBase64) {
    document.body.style.backgroundImage = `url(${currentWallpaperBase64})`;
}

toggleSettingsBtn.addEventListener('click', () => {
    settingsPanel.classList.add('open');
    dutiesPanel.classList.remove('open');
});

toggleDutiesBtn.addEventListener('click', async () => {
    settingsPanel.classList.remove('open');
    dutiesPanel.classList.add('open');
    await refreshDutiesPanel();
});

closeDutiesBtn.addEventListener('click', () => dutiesPanel.classList.remove('open'));
refreshDutiesBtn.addEventListener('click', () => refreshDutiesPanel());

const teachDutyBtn = document.getElementById('teachDutyBtn');
const runLastDutyBtn = document.getElementById('runLastDutyBtn');
const teachOverlay = document.getElementById('teachOverlay');
const teachNameInput = document.getElementById('teachNameInput');
const teachNoteInput = document.getElementById('teachNoteInput');
const teachStartBtn = document.getElementById('teachStartBtn');
const teachCancelBtn = document.getElementById('teachCancelBtn');
const teachError = document.getElementById('teachError');

function openTeachDialog() {
    if (teachError) teachError.textContent = '';
    if (teachNameInput) teachNameInput.value = '';
    if (teachNoteInput) teachNoteInput.value = '';
    if (teachOverlay) {
        teachOverlay.classList.remove('hidden');
        teachOverlay.setAttribute('aria-hidden', 'false');
    }
    if (teachNameInput) teachNameInput.focus();
}

function closeTeachDialog() {
    if (teachOverlay) {
        teachOverlay.classList.add('hidden');
        teachOverlay.setAttribute('aria-hidden', 'true');
    }
}

if (teachDutyBtn) {
    teachDutyBtn.addEventListener('click', () => openTeachDialog());
}

if (teachCancelBtn) {
    teachCancelBtn.addEventListener('click', closeTeachDialog);
}

if (teachStartBtn) {
    teachStartBtn.addEventListener('click', async () => {
        const name = ((teachNameInput && teachNameInput.value) || '').trim();
        const note = ((teachNoteInput && teachNoteInput.value) || '').trim();
        if (!name) {
            if (teachError) teachError.textContent = 'Enter a task name (e.g. morning email).';
            return;
        }
        const cmd = note ? ('teach ' + name + ': ' + note) : ('teach ' + name);
        closeTeachDialog();
        inputField.value = cmd;
        await handleSend();
    });
}

if (runLastDutyBtn) {
    runLastDutyBtn.addEventListener('click', async () => {
        inputField.value = 'run last duty';
        await handleSend();
    });
}

const feedbackBtn = document.getElementById('feedbackBtn');
const sponsorBtn = document.getElementById('sponsorBtn');
const starRepoBtn = document.getElementById('starRepoBtn');
const feedbackOverlay = document.getElementById('feedbackOverlay');
const feedbackRating = document.getElementById('feedbackRating');
const feedbackBody = document.getElementById('feedbackBody');
const feedbackSubmitBtn = document.getElementById('feedbackSubmitBtn');
const feedbackCancelBtn = document.getElementById('feedbackCancelBtn');
const feedbackError = document.getElementById('feedbackError');

async function openExternal(url) {
    if (window.pywebview && window.pywebview.api && window.pywebview.api.open_external_url) {
        return await window.pywebview.api.open_external_url(url);
    }
    window.open(url, '_blank');
    return 'opened';
}

async function communityLinks() {
    if (window.pywebview && window.pywebview.api && window.pywebview.api.get_community_links) {
        try {
            return await window.pywebview.api.get_community_links();
        } catch (e) { /* fall through */ }
    }
    return {
        repo: 'https://github.com/AndyOliverR/VassalOps',
        star: 'https://github.com/AndyOliverR/VassalOps',
        sponsors: 'https://github.com/sponsors/AndyOliverR',
        feedback_new_issue: 'https://github.com/AndyOliverR/VassalOps/issues/new?template=feedback.yml',
        version: ''
    };
}

if (sponsorBtn) {
    sponsorBtn.addEventListener('click', async () => {
        const links = await communityLinks();
        const result = await openExternal(links.sponsors);
        if (result && result !== 'opened') {
            appendMessage('VassalOps', result, false);
        } else {
            appendMessage('VassalOps', 'Opened GitHub Sponsors — thank you for considering a tip or sponsorship.', false);
        }
    });
}

if (starRepoBtn) {
    starRepoBtn.addEventListener('click', async () => {
        const links = await communityLinks();
        await openExternal(links.star);
        appendMessage('VassalOps', 'Opened the VassalOps repo. Click the ★ Star button on GitHub to add a star (apps cannot set stars for you).', false);
    });
}

if (feedbackBtn) {
    feedbackBtn.addEventListener('click', () => {
        if (feedbackError) feedbackError.textContent = '';
        if (feedbackBody) feedbackBody.value = '';
        if (feedbackRating) feedbackRating.value = '';
        if (feedbackOverlay) {
            feedbackOverlay.classList.remove('hidden');
            feedbackOverlay.setAttribute('aria-hidden', 'false');
        }
    });
}

if (feedbackCancelBtn) {
    feedbackCancelBtn.addEventListener('click', () => {
        if (feedbackOverlay) {
            feedbackOverlay.classList.add('hidden');
            feedbackOverlay.setAttribute('aria-hidden', 'true');
        }
    });
}

if (feedbackSubmitBtn) {
    feedbackSubmitBtn.addEventListener('click', async () => {
        const text = ((feedbackBody && feedbackBody.value) || '').trim();
        if (!text) {
            if (feedbackError) feedbackError.textContent = 'Please write a short suggestion first.';
            return;
        }
        const links = await communityLinks();
        const rating = (feedbackRating && feedbackRating.value) || '';
        const ratingLine = rating ? ('Experience rating (in-app): ' + rating + '/5\n') : '';
        const versionLine = links.version ? ('VassalOps version: ' + links.version + '\n') : '';
        const body =
            '### Feedback from VassalOps app\n\n' +
            ratingLine +
            versionLine +
            '\n' +
            text +
            '\n\n---\nNote: In-app ratings do not automatically add GitHub stars.';
        const title = '[Feedback]: ' + text.slice(0, 60).replace(/\n/g, ' ');
        const url =
            'https://github.com/AndyOliverR/VassalOps/issues/new?labels=feedback&title=' +
            encodeURIComponent(title) +
            '&body=' +
            encodeURIComponent(body);
        if (feedbackOverlay) {
            feedbackOverlay.classList.add('hidden');
            feedbackOverlay.setAttribute('aria-hidden', 'true');
        }
        await openExternal(url);
        appendMessage('VassalOps', 'Opened a GitHub feedback Issue draft. Submit it while logged into GitHub so we can fix it in a future push.', false);
    });
}

approvePlaylistBtn.addEventListener('click', async () => {
    if (playlistInFlight) return;
    playlistInFlight = true;
    approvePlaylistBtn.disabled = true;
    dutiesStatus.textContent = 'Running approved duties...';
    try {
        const selected = Array.from(dutiesList.querySelectorAll('input[type=checkbox]:checked')).map((el) => el.value);
        if (window.pywebview && window.pywebview.api) {
            const result = await window.pywebview.api.confirm_playlist(true, selected);
            dutiesStatus.textContent = result;
            appendMessage('VassalOps', result, false);
            startProgressPolling();
            await refreshDutiesPanel();
        } else {
            dutiesStatus.textContent = 'API unavailable outside pywebview.';
        }
    } finally {
        playlistInFlight = false;
        approvePlaylistBtn.disabled = false;
    }
});

skipPlaylistBtn.addEventListener('click', async () => {
    if (window.pywebview && window.pywebview.api) {
        const result = await window.pywebview.api.confirm_playlist(false, []);
        dutiesStatus.textContent = result;
        appendMessage('VassalOps', result, false);
    } else {
        dutiesStatus.textContent = 'Skipped (no duties run).';
    }
    dutiesPanel.classList.remove('open');
});

async function refreshDutiesPanel() {
    dutiesList.textContent = '';
    if (!(window.pywebview && window.pywebview.api)) {
        dutiesHint.textContent = 'Open VassalOps via bootstrap to use Daily Duties.';
        return;
    }
    try {
        const briefing = await window.pywebview.api.get_today_playlist();
        if (!briefing || !briefing.items || briefing.items.length === 0) {
            dutiesHint.textContent = 'No playlist yet. Chat: teach morning email — then build my workday';
            return;
        }
        dutiesHint.textContent = 'Your workday for ' + briefing.date + ' (' + briefing.time + '). Check items, then Approve today\'s run — desktop steps wait for Approve.';
        briefing.items.forEach((item) => {
            const row = document.createElement('div');
            row.className = 'duty-row';
            const cb = document.createElement('input');
            cb.type = 'checkbox';
            cb.value = item.duty_id;
            cb.checked = !!item.exists;
            cb.disabled = !item.exists;
            const label = document.createElement('label');
            const title = document.createElement('div');
            title.textContent = item.name || item.duty_id;
            const meta = document.createElement('div');
            meta.className = 'duty-meta';
            meta.textContent = (item.after || '') + ' · ' + (item.step_count || 0) + ' steps · ' + (item.exists ? 'ready' : 'missing') + ' · last ' + (item.last_run || 'never');
            label.appendChild(title);
            label.appendChild(meta);
            row.appendChild(cb);
            row.appendChild(label);
            dutiesList.appendChild(row);
        });
    } catch (e) {
        dutiesStatus.textContent = 'Could not load playlist.';
    }
}

closeSettingsBtn.addEventListener('click', () => {
    currentUsername = document.getElementById('settingUsername').value.trim() || 'AnDY';
    localStorage.setItem('vassal_user_name', currentUsername);

    const avatarInput = document.getElementById('settingUserAvatar');
    const wallpaperInput = document.getElementById('settingBgWallpaper');

    if (avatarInput.files && avatarInput.files[0]) {
        const reader = new FileReader();
        reader.onload = function(e) {
            currentUserAvatarBase64 = e.target.result;
            localStorage.setItem('vassal_user_avatar_b64', e.target.result);
        };
        reader.readAsDataURL(avatarInput.files[0]);
    }

    if (wallpaperInput.files && wallpaperInput.files[0]) {
        const reader = new FileReader();
        reader.onload = function(e) {
            currentWallpaperBase64 = e.target.result;
            localStorage.setItem('vassal_wallpaper_b64', e.target.result);
            document.body.style.backgroundImage = `url(${e.target.result})`;
        };
        reader.readAsDataURL(wallpaperInput.files[0]);
    }
    settingsPanel.classList.remove('open');
});

clearBgBtn.addEventListener('click', () => {
    currentWallpaperBase64 = '';
    localStorage.removeItem('vassal_wallpaper_b64');
    document.body.style.backgroundImage = 'none';
});

function makeIcon(name) {
    const el = document.createElement('span');
    el.className = 'ui-icon ui-icon-' + name;
    el.setAttribute('aria-hidden', 'true');
    return el;
}

function setButtonIconLabel(btn, iconName, label) {
    btn.textContent = '';
    btn.appendChild(makeIcon(iconName));
    btn.appendChild(document.createTextNode(label));
}

function appendMessage(sender, text, isUser) {
    const container = document.createElement('div');
    container.className = 'msg-container';

    const header = document.createElement('div');
    header.className = 'header-row ' + (isUser ? 'user-color' : 'agent-color');

    if (isUser && currentUserAvatarBase64) {
        const avatarImg = document.createElement('img');
        avatarImg.src = currentUserAvatarBase64;
        avatarImg.className = 'avatar-frame';
        header.appendChild(avatarImg);
    } else if (!isUser) {
        const avatarImg = document.createElement('img');
        avatarImg.src = 'vassal_icon.png';
        avatarImg.className = 'avatar-frame';
        header.appendChild(avatarImg);
    }

    header.appendChild(document.createTextNode(' ' + sender));

    const textRow = document.createElement('div');
    textRow.className = 'text-row';
    textRow.textContent = text;

    container.appendChild(header);
    container.appendChild(textRow);
    chatStream.appendChild(container);
    chatStream.scrollTop = chatStream.scrollHeight;
}

function tryParsePendingApproval(response) {
    if (typeof response !== 'string') {
        return null;
    }
    const trimmed = response.trim();
    if (!trimmed.startsWith('{')) {
        return null;
    }
    try {
        const parsed = JSON.parse(trimmed);
        if (parsed && parsed.status === 'pending_approval') {
            return parsed;
        }
    } catch (e) {
        return null;
    }
    return null;
}

function appendApprovalBlock(plan) {
    const container = document.createElement('div');
    container.className = 'msg-container approval-block';

    const header = document.createElement('div');
    header.className = 'header-row agent-color';
    const avatarImg = document.createElement('img');
    avatarImg.src = 'vassal_icon.png';
    avatarImg.className = 'avatar-frame';
    header.appendChild(avatarImg);
    header.appendChild(document.createTextNode(' VassalOps'));

    const textRow = document.createElement('div');
    textRow.className = 'text-row';

    const intro = document.createElement('div');
    intro.textContent = plan.message || 'Review the proposed steps, then Approve or Reject.';
    textRow.appendChild(intro);

    if (plan.risk && plan.risk.has_desktop) {
        const riskNote = document.createElement('div');
        riskNote.className = 'risk-desktop';
        riskNote.appendChild(makeIcon('desktop'));
        riskNote.appendChild(document.createTextNode(
            'Desktop (' + (plan.risk.desktop_count || 0) + ' write) · read (' + (plan.risk.read_count || 0) + '). Desktop tools run only after Approve.'
        ));
        textRow.appendChild(riskNote);
    } else if (plan.risk && (plan.risk.read_count || 0) > 0) {
        const riskNote = document.createElement('div');
        riskNote.className = 'risk-desktop';
        riskNote.appendChild(makeIcon('eye'));
        riskNote.appendChild(document.createTextNode(
            'Read (' + (plan.risk.read_count || 0) + '). No desktop writes in this plan.'
        ));
        textRow.appendChild(riskNote);
    }

    const list = document.createElement('ul');
    list.className = 'approval-step-list';
    const readable = Array.isArray(plan.readable_steps) ? plan.readable_steps : null;
    const steps = Array.isArray(plan.proposed_actions) ? plan.proposed_actions : [];
    if (readable && readable.length) {
        readable.forEach((line, idx) => {
            const li = document.createElement('li');
            const risk = steps[idx] && steps[idx].risk ? String(steps[idx].risk) : '';
            li.textContent = (risk ? '[' + risk + '] ' : '') + line;
            list.appendChild(li);
        });
    } else if (steps.length === 0) {
        const empty = document.createElement('li');
        empty.textContent = '(no steps proposed)';
        list.appendChild(empty);
    } else {
        steps.forEach((step, idx) => {
            const li = document.createElement('li');
            const actionType = step && step.type != null ? String(step.type) : 'unknown';
            const payload = step && step.payload != null ? String(step.payload) : '';
            li.textContent = (idx + 1) + '. ' + actionType + ' -> ' + payload;
            list.appendChild(li);
        });
    }
    textRow.appendChild(list);

    const actions = document.createElement('div');
    actions.className = 'approval-actions';

    const approveBtn = document.createElement('button');
    approveBtn.type = 'button';
    approveBtn.className = 'approve-btn';
    setButtonIconLabel(approveBtn, 'check', 'Approve');

    const rejectBtn = document.createElement('button');
    rejectBtn.type = 'button';
    rejectBtn.className = 'reject-btn';
    setButtonIconLabel(rejectBtn, 'xmark', 'Reject');

    const disableButtons = () => {
        approveBtn.disabled = true;
        rejectBtn.disabled = true;
    };

    approveBtn.addEventListener('click', async () => {
        if (approvalInFlight) return;
        approvalInFlight = true;
        disableButtons();
        try {
            if (window.pywebview && window.pywebview.api) {
                const result = await window.pywebview.api.confirm_plan(true);
                appendMessage('VassalOps', result, false);
                startProgressPolling();
                await refreshDutiesPanel();
            }
        } finally {
            approvalInFlight = false;
        }
    });

    rejectBtn.addEventListener('click', async () => {
        if (approvalInFlight) return;
        approvalInFlight = true;
        disableButtons();
        try {
            if (window.pywebview && window.pywebview.api) {
                const result = await window.pywebview.api.confirm_plan(false);
                appendMessage('VassalOps', result, false);
            }
        } finally {
            approvalInFlight = false;
        }
    });

    actions.appendChild(approveBtn);
    actions.appendChild(rejectBtn);
    textRow.appendChild(actions);

    container.appendChild(header);
    container.appendChild(textRow);
    chatStream.appendChild(container);
    chatStream.scrollTop = chatStream.scrollHeight;
}

async function handleSend() {
    const text = inputField.value.trim();
    if (!text) return;
    appendMessage(currentUsername, text, true);
    inputField.value = '';

    if (window.pywebview && window.pywebview.api) {
        const response = await window.pywebview.api.submit_command(text);
        const pending = tryParsePendingApproval(response);
        if (pending) {
            appendApprovalBlock(pending);
        } else {
            appendMessage('VassalOps', response, false);
        }
        const lower = text.toLowerCase();
        if (lower.indexOf('teach ') === 0 || lower.indexOf('build my workday') >= 0 || lower.indexOf('run duty') >= 0 || lower.indexOf('run my workday') >= 0) {
            await refreshDutiesPanel();
        }
    } else {
        appendMessage('VassalOps', 'Hello AnDY! How May I help?', false);
    }
}

runButton.addEventListener('click', handleSend);
inputField.addEventListener('keypress', (e) => { if (e.key === 'Enter') handleSend(); });

/* Voice → chat (Web Speech API in WebView2). Desktop actions still need Approve. */
const micButton = document.getElementById('micButton');
let voiceRecognition = null;
let voiceListening = false;

function getSpeechRecognition() {
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    return SR ? new SR() : null;
}

if (micButton) {
    micButton.addEventListener('click', () => {
        if (!(window.SpeechRecognition || window.webkitSpeechRecognition)) {
            appendMessage('VassalOps', 'Voice input is not available in this WebView. Type in the chat box instead.', false);
            return;
        }
        if (voiceListening && voiceRecognition) {
            try { voiceRecognition.stop(); } catch (e) { /* ignore */ }
            return;
        }
        voiceRecognition = getSpeechRecognition();
        if (!voiceRecognition) return;
        voiceRecognition.lang = 'en-US';
        voiceRecognition.interimResults = true;
        voiceRecognition.continuous = false;
        voiceListening = true;
        micButton.classList.add('listening');
        micButton.title = 'Listening… tap to stop';
        voiceRecognition.onresult = (event) => {
            let interim = '';
            let finalText = '';
            for (let i = event.resultIndex; i < event.results.length; i++) {
                const piece = event.results[i][0].transcript;
                if (event.results[i].isFinal) finalText += piece;
                else interim += piece;
            }
            if (finalText) inputField.value = finalText.trim();
            else if (interim) inputField.value = interim.trim();
        };
        voiceRecognition.onerror = () => {
            voiceListening = false;
            micButton.classList.remove('listening');
            micButton.title = 'Voice input (speech to chat)';
        };
        voiceRecognition.onend = () => {
            voiceListening = false;
            micButton.classList.remove('listening');
            micButton.title = 'Voice input (speech to chat)';
            const text = (inputField.value || '').trim();
            if (text) handleSend();
        };
        try {
            voiceRecognition.start();
        } catch (e) {
            voiceListening = false;
            micButton.classList.remove('listening');
            appendMessage('VassalOps', 'Could not start microphone. Check Windows mic permission for VassalOps.', false);
        }
    });
}

const runProgressPanel = document.getElementById('runProgressPanel');
const runProgressIcon = document.getElementById('runProgressIcon');
const runProgressLabel = document.getElementById('runProgressLabel');
const runProgressFill = document.getElementById('runProgressFill');
const runProgressSummary = document.getElementById('runProgressSummary');
const runChecklist = document.getElementById('runChecklist');
const stuckBox = document.getElementById('stuckBox');
const stuckReason = document.getElementById('stuckReason');
const stuckHint = document.getElementById('stuckHint');
const stopRunBtn = document.getElementById('stopRunBtn');
const continueRunBtn = document.getElementById('continueRunBtn');
const confirmReplanBtn = document.getElementById('confirmReplanBtn');
const skipStuckBtn = document.getElementById('skipStuckBtn');
let progressTimer = null;
let lastProgressStatus = 'idle';
let reportedRunEnd = false;

function renderChecklist(items) {
    if (!runChecklist) return;
    runChecklist.innerHTML = '';
    (items || []).slice(0, 24).forEach((item) => {
        const li = document.createElement('li');
        const st = item.status || 'pending';
        li.className = st;
        li.textContent = (st === 'running' ? '→ ' : st === 'done' ? '✓ ' : st === 'failed' ? '✗ ' : '• ') + (item.label || '');
        runChecklist.appendChild(li);
    });
}

function startProgressPolling() {
    if (progressTimer) clearInterval(progressTimer);
    reportedRunEnd = false;
    runProgressPanel.classList.remove('hidden');
    progressTimer = setInterval(refreshRunProgress, 400);
    refreshRunProgress();
}

async function refreshRunProgress() {
    if (!(window.pywebview && window.pywebview.api && window.pywebview.api.get_run_progress)) {
        return;
    }
    try {
        const p = await window.pywebview.api.get_run_progress();
        if (!p) return;
        const status = p.status || 'idle';
        lastProgressStatus = status;
        if (status === 'idle') {
            runProgressPanel.classList.add('hidden');
            return;
        }
        runProgressPanel.classList.remove('hidden');
        const cur = p.current || 0;
        const total = p.total || 0;
        const pct = total > 0 ? Math.min(100, Math.round((cur / total) * 100)) : (status === 'done' ? 100 : 8);
        runProgressFill.style.width = pct + '%';
        runProgressLabel.textContent = p.label || p.current_tool || '';
        if (runProgressSummary) {
            runProgressSummary.textContent = p.summary || '';
        }
        const needsYouEl = document.getElementById('needsYouBrief');
        if (needsYouEl) {
            const ny = (p.needs_you || '').trim();
            if (ny) {
                needsYouEl.textContent = 'Needs you: ' + ny;
                needsYouEl.classList.remove('hidden');
            } else {
                needsYouEl.textContent = '';
                needsYouEl.classList.add('hidden');
            }
        }
        renderChecklist(p.checklist || []);
        const hasReplan = !!(p.pending_replan && p.pending_replan.message);
        if (confirmReplanBtn) {
            if (hasReplan) confirmReplanBtn.classList.remove('hidden');
            else confirmReplanBtn.classList.add('hidden');
        }
        if (status === 'paused') {
            runProgressIcon.className = 'ui-icon ui-icon-alert';
            runProgressTitle.textContent = hasReplan ? 'Stage / replan — Approve to continue' : 'Paused — need you';
            stuckBox.classList.remove('hidden');
            stuckReason.textContent = p.stuck_reason || 'Automation is stuck.';
            let hint = p.stuck_hint || '';
            if (hasReplan && p.pending_replan.steps && p.pending_replan.steps.length) {
                hint += '\nSuggested: ' + p.pending_replan.steps.join('; ');
            }
            stuckHint.textContent = hint;
        } else {
            stuckBox.classList.add('hidden');
            if (status === 'running') {
                runProgressIcon.className = 'ui-icon ui-icon-play';
                runProgressTitle.textContent = 'Running… (' + cur + '/' + total + ')';
            }
            if (status === 'stopped') {
                runProgressIcon.className = 'ui-icon ui-icon-stop';
                runProgressTitle.textContent = 'Stopped';
            }
            if (status === 'done' || status === 'stopped') {
                if (status === 'done') {
                    runProgressIcon.className = p.ok ? 'ui-icon ui-icon-check' : 'ui-icon ui-icon-xmark';
                    runProgressTitle.textContent = p.ok ? 'Finished' : ('Failed' + (p.last_error ? ': ' + p.last_error : ''));
                }
                if (!reportedRunEnd) {
                    reportedRunEnd = true;
                    if (p.summary) {
                        appendMessage('VassalOps', p.summary, false);
                    }
                    if (status === 'done' && p.last_error && !p.ok) {
                        appendMessage('VassalOps', 'Run failed: ' + p.last_error, false);
                    }
                    if (status === 'stopped') {
                        appendMessage('VassalOps', 'Run stopped.', false);
                    }
                }
                clearInterval(progressTimer);
                progressTimer = null;
                setTimeout(() => runProgressPanel.classList.add('hidden'), 4000);
                refreshDutiesPanel();
            }
        }
    } catch (e) {
        /* ignore poll errors */
    }
}

stopRunBtn.addEventListener('click', async () => {
    if (window.pywebview && window.pywebview.api) {
        const msg = await window.pywebview.api.stop_run();
        appendMessage('VassalOps', msg, false);
    }
});
continueRunBtn.addEventListener('click', async () => {
    if (window.pywebview && window.pywebview.api) {
        await window.pywebview.api.continue_run();
    }
});
if (confirmReplanBtn) {
    confirmReplanBtn.addEventListener('click', async () => {
        if (window.pywebview && window.pywebview.api && window.pywebview.api.confirm_replan) {
            const msg = await window.pywebview.api.confirm_replan();
            appendMessage('VassalOps', msg, false);
        }
    });
}
skipStuckBtn.addEventListener('click', async () => {
    if (window.pywebview && window.pywebview.api) {
        await window.pywebview.api.skip_stuck_step();
    }
});

window.addEventListener('load', async () => {
    const overlay = document.getElementById('splashOverlay');
    const finishWelcome = () => {
        appendMessage('VassalOps', 'Hello! This is your PC workday runner.\n• Teach / Learn (top bar): name a task → Approve → do it on the PC → Escape. Next time: Run last or say again.\n• Mic or type in chat — desktop still needs Approve.\n• Demo: import demo pack → run duty demo notepad hello\nIt does not silently record your whole day — only Teach sessions you start.', false);
    };

    const afterSplash = async () => {
        const unlocked = await showAuthGate();
        if (unlocked) finishWelcome();
    };

    // Brand splash every launch — large sharp mark (Desktop .ico stays static)
    if (!overlay) {
        await afterSplash();
        return;
    }

    overlay.classList.remove('hidden');
    overlay.setAttribute('aria-hidden', 'false');
    const reduced = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    const ms = reduced ? 1200 : 5000;
    setTimeout(async () => {
        const stage = document.getElementById('splashStage');
        if (stage) stage.classList.add('fade-out');
        setTimeout(async () => {
            overlay.classList.add('hidden');
            overlay.setAttribute('aria-hidden', 'true');
            try {
                if (window.pywebview && window.pywebview.api && window.pywebview.api.mark_splash_seen) {
                    await window.pywebview.api.mark_splash_seen();
                }
            } catch (e) { /* optional flag */ }
            await afterSplash();
        }, 350);
    }, ms);
});

/* ---- Local PIN gate ---- */
let authUnlocked = false;

function setAuthError(msg) {
    const el = document.getElementById('authError');
    if (el) el.textContent = msg || '';
}

function showAuthPanel(name) {
    ['authSignupPanel', 'authUnlockPanel', 'authResetPanel'].forEach((id) => {
        const p = document.getElementById(id);
        if (p) p.classList.toggle('hidden', id !== name);
    });
    const title = document.getElementById('authTitle');
    if (title) {
        title.textContent = name === 'authSignupPanel' ? 'Create local account'
            : name === 'authResetPanel' ? 'Reset PIN'
            : 'Unlock VassalOps';
    }
}

function fillQuestionSelect(questions) {
    const sel = document.getElementById('authQuestionSelect');
    const custom = document.getElementById('authQuestionCustom');
    if (!sel) return;
    sel.innerHTML = '';
    (questions || []).forEach((q) => {
        const opt = document.createElement('option');
        opt.value = q;
        opt.textContent = q;
        sel.appendChild(opt);
    });
    const syncCustom = () => {
        const isCustom = sel.value === 'Custom…';
        if (custom) custom.classList.toggle('hidden', !isCustom);
    };
    sel.onchange = syncCustom;
    syncCustom();
}

function setMainUiEnabled(enabled) {
    authUnlocked = !!enabled;
    const authOverlay = document.getElementById('authOverlay');
    if (authOverlay) {
        authOverlay.classList.toggle('hidden', enabled);
        authOverlay.setAttribute('aria-hidden', enabled ? 'true' : 'false');
    }
    if (inputField) inputField.disabled = !enabled;
    if (runButton) runButton.disabled = !enabled;
    if (micButton) micButton.disabled = !enabled;
    if (teachDutyBtn) teachDutyBtn.disabled = !enabled;
    if (runLastDutyBtn) runLastDutyBtn.disabled = !enabled;
    if (feedbackBtn) feedbackBtn.disabled = !enabled;
    if (sponsorBtn) sponsorBtn.disabled = !enabled;
    if (starRepoBtn) starRepoBtn.disabled = !enabled;
}

async function showAuthGate() {
    if (!(window.pywebview && window.pywebview.api && window.pywebview.api.auth_status)) {
        setMainUiEnabled(true);
        return true;
    }
    let status;
    try {
        status = await window.pywebview.api.auth_status();
    } catch (e) {
        setMainUiEnabled(true);
        return true;
    }
    if (status && status.unlocked) {
        setMainUiEnabled(true);
        await runLaunchHandshake();
        return true;
    }
    fillQuestionSelect(status.default_questions || []);
    setMainUiEnabled(false);
    setAuthError('');
    if (status.has_profile) {
        showAuthPanel('authUnlockPanel');
        const masked = document.getElementById('authEmailMasked');
        if (masked) masked.textContent = status.email_masked ? ('Account: ' + status.email_masked) : '';
    } else {
        showAuthPanel('authSignupPanel');
    }
    return new Promise((resolve) => {
        window.__authGateResolve = resolve;
    });
}

function finishAuthGate(ok) {
    if (ok) setMainUiEnabled(true);
    if (typeof window.__authGateResolve === 'function') {
        window.__authGateResolve(!!ok);
        window.__authGateResolve = null;
    }
}

async function runLaunchHandshake() {
    if (!(window.pywebview && window.pywebview.api && window.pywebview.api.run_labrat_handshake)) return;
    try {
        const result = await window.pywebview.api.run_labrat_handshake('launch');
        if (result && result.message) {
            appendMessage('VassalOps', result.message, false);
        }
    } catch (e) { /* offline is fine */ }
}

async function proceedAfterAuth() {
    finishAuthGate(true);
    await runLaunchHandshake();
}

const authSignupBtn = document.getElementById('authSignupBtn');
if (authSignupBtn) {
    authSignupBtn.addEventListener('click', async () => {
        setAuthError('');
        const email = (document.getElementById('authEmail') || {}).value || '';
        const pin = (document.getElementById('authPinSignup') || {}).value || '';
        const pin2 = (document.getElementById('authPinSignup2') || {}).value || '';
        const sel = document.getElementById('authQuestionSelect');
        const custom = document.getElementById('authQuestionCustom');
        let question = sel ? sel.value : '';
        if (question === 'Custom…') question = (custom && custom.value) || '';
        const answer = (document.getElementById('authAnswer') || {}).value || '';
        if (pin !== pin2) {
            setAuthError('PIN confirmation does not match.');
            return;
        }
        try {
            const result = await window.pywebview.api.auth_signup(email, pin, question, answer);
            if (!result || !result.ok) {
                setAuthError((result && result.error) || 'Signup failed.');
                return;
            }
            const note = result.registered
                ? (result.registration || 'Registered.')
                : ('Registered locally (cloud ping skipped). ' + (result.registration || ''));
            appendMessage('VassalOps', note.trim(), false);
            await proceedAfterAuth(result);
        } catch (e) {
            setAuthError(String(e));
        }
    });
}

const authUnlockBtn = document.getElementById('authUnlockBtn');
if (authUnlockBtn) {
    authUnlockBtn.addEventListener('click', async () => {
        setAuthError('');
        const pin = (document.getElementById('authPinUnlock') || {}).value || '';
        try {
            const result = await window.pywebview.api.auth_unlock(pin);
            if (!result || !result.ok) {
                setAuthError((result && result.error) || 'Unlock failed.');
                return;
            }
            await proceedAfterAuth(result);
        } catch (e) {
            setAuthError(String(e));
        }
    });
}

const authForgotBtn = document.getElementById('authForgotBtn');
if (authForgotBtn) {
    authForgotBtn.addEventListener('click', async () => {
        setAuthError('');
        try {
            const status = await window.pywebview.api.auth_status();
            const qEl = document.getElementById('authResetQuestion');
            if (qEl) qEl.textContent = 'Question: ' + (status.question || '(not set)');
        } catch (e) { /* ignore */ }
        showAuthPanel('authResetPanel');
    });
}

const authResetBackBtn = document.getElementById('authResetBackBtn');
if (authResetBackBtn) {
    authResetBackBtn.addEventListener('click', () => {
        setAuthError('');
        showAuthPanel('authUnlockPanel');
    });
}

const authResetBtn = document.getElementById('authResetBtn');
if (authResetBtn) {
    authResetBtn.addEventListener('click', async () => {
        setAuthError('');
        const answer = (document.getElementById('authResetAnswer') || {}).value || '';
        const pin = (document.getElementById('authResetPin') || {}).value || '';
        const pin2 = (document.getElementById('authResetPin2') || {}).value || '';
        if (pin !== pin2) {
            setAuthError('PIN confirmation does not match.');
            return;
        }
        try {
            const result = await window.pywebview.api.auth_reset_pin(answer, pin);
            if (!result || !result.ok) {
                setAuthError((result && result.error) || 'Reset failed.');
                return;
            }
            appendMessage('VassalOps', result.message || 'PIN updated.', false);
            await proceedAfterAuth(result);
        } catch (e) {
            setAuthError(String(e));
        }
    });
}

const changePinBtn = document.getElementById('changePinBtn');
if (changePinBtn) {
    changePinBtn.addEventListener('click', async () => {
        if (!(window.pywebview && window.pywebview.api && window.pywebview.api.auth_change_pin)) return;
        const cur = (document.getElementById('settingCurrentPin') || {}).value || '';
        const neu = (document.getElementById('settingNewPin') || {}).value || '';
        try {
            const result = await window.pywebview.api.auth_change_pin(cur, neu);
            appendMessage('VassalOps', (result && result.ok) ? (result.message || 'PIN changed.') : ((result && result.error) || 'PIN change failed.'), false);
            if (result && result.ok) {
                const a = document.getElementById('settingCurrentPin');
                const b = document.getElementById('settingNewPin');
                if (a) a.value = '';
                if (b) b.value = '';
            }
        } catch (e) {
            appendMessage('VassalOps', String(e), false);
        }
    });
}
