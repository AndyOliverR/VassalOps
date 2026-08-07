const chatStream = document.getElementById('chatStream');
const inputField = document.getElementById('userInputField');
const runButton = document.getElementById('runButton');
const toggleSettingsBtn = document.getElementById('toggleSettingsBtn');
const closeSettingsBtn = document.getElementById('closeSettingsBtn');
const clearBgBtn = document.getElementById('clearBgBtn');
const settingsPanel = document.getElementById('settingsPanel');

let currentUsername = localStorage.getItem('vassal_user_name') || 'AnDY';
let currentUserAvatarBase64 = localStorage.getItem('vassal_user_avatar_b64') || '';
let currentWallpaperBase64 = localStorage.getItem('vassal_wallpaper_b64') || '';
let approvalInFlight = false;

document.getElementById('settingUsername').value = currentUsername;
if (currentWallpaperBase64) {
    document.body.style.backgroundImage = `url(${currentWallpaperBase64})`;
}

toggleSettingsBtn.addEventListener('click', () => settingsPanel.classList.add('open'));

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

    const list = document.createElement('ul');
    list.className = 'approval-step-list';
    const steps = Array.isArray(plan.proposed_actions) ? plan.proposed_actions : [];
    if (steps.length === 0) {
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
    approveBtn.textContent = 'Approve';

    const rejectBtn = document.createElement('button');
    rejectBtn.type = 'button';
    rejectBtn.className = 'reject-btn';
    rejectBtn.textContent = 'Reject';

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
    } else {
        appendMessage('VassalOps', 'Hello AnDY! How May I help?', false);
    }
}

runButton.addEventListener('click', handleSend);
inputField.addEventListener('keypress', (e) => { if (e.key === 'Enter') handleSend(); });

window.addEventListener('load', () => {
    appendMessage('VassalOps', 'Hello! How May I help?', false);
});
