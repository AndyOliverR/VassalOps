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
        dutiesHint.textContent = 'Briefing for ' + briefing.date + ' (' + briefing.time + '). Check items, then Approve today\'s run.';
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

const runProgressPanel = document.getElementById('runProgressPanel');
const runProgressIcon = document.getElementById('runProgressIcon');
const runProgressLabel = document.getElementById('runProgressLabel');
const runProgressFill = document.getElementById('runProgressFill');
const stuckBox = document.getElementById('stuckBox');
const stuckReason = document.getElementById('stuckReason');
const stuckHint = document.getElementById('stuckHint');
const stopRunBtn = document.getElementById('stopRunBtn');
const continueRunBtn = document.getElementById('continueRunBtn');
const skipStuckBtn = document.getElementById('skipStuckBtn');
let progressTimer = null;
let lastProgressStatus = 'idle';
let reportedRunEnd = false;

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
        runProgressLabel.textContent = p.label || '';
        if (status === 'paused') {
            runProgressIcon.className = 'ui-icon ui-icon-alert';
            runProgressTitle.textContent = 'Paused — need you';
            stuckBox.classList.remove('hidden');
            stuckReason.textContent = p.stuck_reason || 'Automation is stuck.';
            stuckHint.textContent = p.stuck_hint || '';
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
skipStuckBtn.addEventListener('click', async () => {
    if (window.pywebview && window.pywebview.api) {
        await window.pywebview.api.skip_stuck_step();
    }
});

window.addEventListener('load', () => {
    appendMessage('VassalOps', 'Hello! Teach a duty with teach morning email, import demo pack for a 60s demo, or open Daily Duties.\nYour PC\'s workday — taught by you, approved by you, run locally.', false);
});
