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
    
    let headerHTML = '';
    if (isUser) {
        const avatarImg = currentUserAvatarBase64 ? `<img src="${currentUserAvatarBase64}" class="avatar-frame"> ` : '';
        headerHTML = `<div class="header-row user-color">${avatarImg}${sender}</div>`;
    } else {
        headerHTML = `<div class="header-row agent-color"><img src="vassal_icon.png" class="avatar-frame"> ${sender}</div>`;
    }

    container.innerHTML = `${headerHTML}<div class="text-row">${text}</div>`;
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
        appendMessage("VassalOps", response, false);
    } else {
        appendMessage("VassalOps", "Hello AnDY! How May I help?", false);
    }
}

runButton.addEventListener('click', handleSend);
inputField.addEventListener('keypress', (e) => { if (e.key === 'Enter') handleSend(); });

window.addEventListener('load', () => {
    appendMessage("VassalOps", "Hello! How May I help?", false);
});