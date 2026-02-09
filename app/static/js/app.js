// State
let users = [];
let chores = [];
let activeUser = null;
let weatherCache = null;
let weatherCacheTimestamp = 0;

// Initialization
document.addEventListener('DOMContentLoaded', () => {
    fetchUsers();
    fetchChores();
    fetchWeather(true);
});

// -- API Interaction --

async function fetchUsers() {
    try {
        const res = await fetch('/api/users');
        users = await res.json();
        renderUserSelect();
        renderLeaderboard();
    } catch (err) {
        console.error('Failed to fetch users', err);
    }
}

async function fetchChores() {
    try {
        const res = await fetch('/api/chores');
        chores = await res.json();
        renderChores();
    } catch (err) {
        console.error('Failed to fetch chores', err);
    }
}

async function handleAddUser(e) {
    e.preventDefault();
    const username = document.getElementById('newUsername').value;

    try {
        const res = await fetch('/api/users', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username })
        });

        if (res.ok) {
            closeModal('userModal');
            document.getElementById('newUsername').value = '';
            fetchUsers();
        } else {
            showToast('Failed to create user', 'error');
        }
    } catch (err) {
        console.error(err);
    }
}

async function handleSaveChore(e) {
    e.preventDefault();
    const id = document.getElementById('choreId').value;
    const title = document.getElementById('choreTitle').value;
    const description = document.getElementById('choreDesc').value;
    const location = document.getElementById('choreLocation').value;
    const points = document.getElementById('chorePoints').value;
    const is_recurring = document.getElementById('choreRecurring').checked;

    const url = id ? `/api/chores/${id}` : '/api/chores';
    const method = id ? 'PUT' : 'POST';

    try {
        const res = await fetch(url, {
            method: method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ title, description, location, points, is_recurring })
        });

        if (res.ok) {
            closeModal('choreModal');
            fetchChores();
        } else {
            showToast('Failed to save chore', 'error');
        }
    } catch (err) {
        console.error(err);
    }
}

async function completeChore(choreId, points) {
    if (!activeUser) {
        showToast('Please select a user first!', 'error');
        document.getElementById('userSelect').focus();
        return;
    }

    // if (!confirm(`Mark this chore as done by ${activeUser.username} for ${points} points?`)) return;

    try {
        const res = await fetch(`/api/chores/${choreId}/complete`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ user_id: activeUser.id })
        });

        const data = await res.json();

        if (res.ok) {
            showToast(`Chore completed! ${activeUser.username} earned ${data.points_earned} points.`, 'success');
            // Refresh data
            await fetchUsers();
            await fetchChores();
        }
    } catch (err) {
        console.error(err);
    }
}

async function deleteChore(choreId) {
    if (!confirm('Are you sure you want to delete this chore?')) return;

    try {
        const res = await fetch(`/api/chores/${choreId}`, {
            method: 'DELETE'
        });

        if (res.ok) {
            fetchChores();
        }
    } catch (err) {
        console.error(err);
    }
}

// -- Rendering --

function renderUserSelect() {
    const select = document.getElementById('userSelect');
    const currentVal = select.value;

    select.innerHTML = '<option value="">Select a user...</option>' +
        users.map(u => `<option value="${u.id}">${u.username} (${u.total_points} pts)</option>`).join('');

    if (currentVal && users.find(u => u.id == currentVal)) {
        select.value = currentVal;
    } else if (users.length === 1) {
        // Auto-select if only one item available? No, explicit is better.
    }
    updateActiveUser();
}

function updateActiveUser() {
    const id = document.getElementById('userSelect').value;
    const statsDiv = document.getElementById('userStats');

    if (!id) {
        activeUser = null;
        statsDiv.textContent = 'Select yourself to start earning points';
        return;
    }

    activeUser = users.find(u => u.id == id);
    if (activeUser) {
        statsDiv.innerHTML = `Current Points: <strong style="color: var(--primary)">${activeUser.total_points}</strong>`;
    }
}

function renderLeaderboard() {
    const container = document.getElementById('leaderboardList');
    if (!users.length) {
        container.innerHTML = '<div style="color: var(--text-muted)">No users yet</div>';
        return;
    }

    // Sort by points desc
    const sorted = [...users].sort((a, b) => b.total_points - a.total_points);

    container.innerHTML = sorted.map((u, index) => {
        const rankOrImage = u.profile_picture
            ? `<img src="${u.profile_picture}" alt="${u.username}" style="width: 50px; height: 50px; border-radius: 50%; object-fit: cover; margin-bottom: 0.5rem; border: 2px solid var(--surface);">`
            : `<div style="font-size: 0.8rem; color: var(--text-muted); margin-bottom: 0.5rem;">#${index + 1}</div>`;

        return `
        <div onclick="window.location.href='/user/${u.id}'" style="background: var(--background); padding: 1rem; border-radius: var(--radius); border: 1px solid var(--border); min-width: 150px; text-align: center; cursor: pointer; transition: transform 0.2s; display: flex; flex-direction: column; align-items: center;" onmouseenter="this.style.transform='translateY(-4px)'" onmouseleave="this.style.transform='translateY(0)'">
            ${rankOrImage}
            <div style="font-weight: bold; font-size: 1.1rem; margin-bottom: 0.25rem;">${u.username}</div>
            <div class="badge">${u.total_points} pts</div>
        </div>
    `;
    }).join('');
}

function renderChores() {
    const recurringContainer = document.getElementById('recurringChoreList');
    const oneOffContainer = document.getElementById('oneOffChoreList');

    const recurring = chores.filter(c => c.is_recurring).sort((a, b) => b.points - a.points);
    const oneOff = chores.filter(c => !c.is_recurring).sort((a, b) => b.points - a.points);

    const renderCard = (c) => {
        let avatarsHtml = '';
        if (c.schedules && c.schedules.length > 0) {
            avatarsHtml = `<div class="scheduled-avatars">
                ${c.schedules.map(s => `
                    <div class="avatar-wrapper">
                        <img src="${s.user_avatar || 'https://api.dicebear.com/9.x/avataaars/svg?seed=' + s.user_name}" alt="${s.user_name}" class="scheduled-avatar">
                        <div class="avatar-tooltip">
                            ${s.user_name}<br>
                            ${new Date(s.scheduled_at.endsWith('Z') ? s.scheduled_at : s.scheduled_at + 'Z').toLocaleString([], { month: 'numeric', day: 'numeric', hour: 'numeric', minute: '2-digit' })}
                        </div>
                    </div>
                `).join('')}
            </div>`;
        }

        return `
        <div class="card fade-in" style="display: flex; flex-direction: column; justify-content: space-between;">
            <div class="chore-card-content">
                ${avatarsHtml}
                <div class="flex-between" style="margin-bottom: 0.5rem; align-items: flex-start;">
                    <h3 style="font-size: 1.25rem;">${c.title}</h3>
                    <div class="badge">${c.points} pts</div>
                </div>
                <p style="color: var(--text-muted); margin-bottom: 1rem; font-size: 0.9rem;">
                    ${c.description || 'No description'}
                </p>
                ${c.is_recurring ? `
                    <div style="font-size: 0.8rem; color: var(--secondary); margin-bottom: 1rem;">
                        <span style="display:inline-block; transform: rotate(45deg); margin-right:4px;">↻</span> Recurring
                        ${c.last_completed_at ? `<span style="color: var(--text-muted);"> • Last done: ${new Date(c.last_completed_at).toLocaleDateString()}</span>` : ''}
                        <span style="color: var(--text-muted); padding-left: 5px; border-left: 1px solid var(--border); margin-left: 5px;"> ${c.location || 'Inside'}</span>
                    </div>`
                : `
                    <div style="font-size: 0.8rem; color: var(--text-muted); margin-bottom: 1rem;">
                        Location: ${c.location || 'Inside'}
                    </div>
            `}
            </div>
            
            <div class="flex-between" style="border-top: 1px solid var(--border); padding-top: 1rem; margin-top: 1rem;">
                <div style="display: flex; gap: 0.5rem; flex-wrap: wrap;">
                    <button class="btn" onclick="openChoreModal(${c.id})" style="padding: 0.4rem 0.8rem; font-size: 0.8rem; background: var(--surface); border: 1px solid var(--border); color: var(--text);">
                        Edit
                    </button>
                    <button class="btn btn-danger" onclick="deleteChore(${c.id})" style="padding: 0.4rem 0.8rem; font-size: 0.8rem;">
                        Delete
                    </button>
                    <button class="btn btn-warning" onclick="openCalendarModal(${c.id})" style="padding: 0.4rem 0.8rem; font-size: 0.8rem;">
                        Calendar
                    </button>
                </div>
                <button class="btn btn-primary" onclick="completeChore(${c.id}, ${c.points})">
                    Complete
                </button>
            </div>
        </div>
    `;
    };

    if (!recurring.length) {
        recurringContainer.innerHTML = '<div style="grid-column: 1/-1; text-align: center; color: var(--text-muted); padding: 2rem;">No recurring tasks found.</div>';
    } else {
        recurringContainer.innerHTML = recurring.map(renderCard).join('');
    }

    if (!oneOff.length) {
        oneOffContainer.innerHTML = '<div style="grid-column: 1/-1; text-align: center; color: var(--text-muted); padding: 2rem;">No one-time tasks found.</div>';
    } else {
        oneOffContainer.innerHTML = oneOff.map(renderCard).join('');
    }
}

function openChoreModal(choreId = null) {
    const titleEl = document.getElementById('choreModalTitle');
    const idInput = document.getElementById('choreId');
    const titleInput = document.getElementById('choreTitle');
    const descInput = document.getElementById('choreDesc');
    const locationInput = document.getElementById('choreLocation');
    const pointsInput = document.getElementById('chorePoints');
    const recurringInput = document.getElementById('choreRecurring');

    if (choreId) {
        const chore = chores.find(c => c.id === choreId);
        if (!chore) return;

        titleEl.textContent = 'Edit Chore';
        idInput.value = choreId;
        titleInput.value = chore.title;
        descInput.value = chore.description || '';
        locationInput.value = chore.location || 'Inside';
        pointsInput.value = chore.points;
        recurringInput.checked = chore.is_recurring;
    } else {
        titleEl.textContent = 'Create New Chore';
        idInput.value = '';
        titleInput.value = '';
        descInput.value = '';
        locationInput.value = 'Inside';
        pointsInput.value = '10';
        recurringInput.checked = false;
    }

    openModal('choreModal');
}


function openCalendarModal(choreId) {
    if (!activeUser) {
        showToast("Please select a user first to send a calendar invite.", "error");
        // Focus the user select
        const userSelect = document.getElementById('userSelect');
        if (userSelect) {
            userSelect.focus();
            userSelect.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
        return;
    }

    // Identify chore
    const chore = chores.find(c => c.id === choreId);

    // Reset Weather
    const weatherDiv = document.getElementById('calendarWeather');
    if (weatherDiv) {
        weatherDiv.style.display = 'none';
        document.getElementById('weatherContent').textContent = '';
        document.getElementById('weatherRecommendation').textContent = '';
    }

    if (chore && chore.location === "Outside") {
        fetchWeather();
    }

    document.getElementById('calendarChoreId').value = choreId;

    // Set default date/time
    const now = new Date();
    document.getElementById('calendarDate').valueAsDate = now;
    // Set time to next hour
    now.setHours(now.getHours() + 1);
    now.setMinutes(0);
    const timeStr = now.toTimeString().substring(0, 5);
    document.getElementById('calendarTime').value = timeStr;

    openModal('calendarModal');
}

async function fetchWeather(background = false) {
    let content, recommendation, weatherDiv;

    if (!background) {
        weatherDiv = document.getElementById('calendarWeather');
        content = document.getElementById('weatherContent');
        recommendation = document.getElementById('weatherRecommendation');

        weatherDiv.style.display = 'block';

        // Check Cache (valid for 1 hour)
        if (weatherCache && (Date.now() - weatherCacheTimestamp < 3600000)) {
            populateWeatherUI(weatherCache);
            return;
        }

        content.textContent = 'Loading weather...';
        recommendation.textContent = '';
    }

    if (!navigator.geolocation) {
        if (!background && content) content.textContent = 'Geolocation is not supported by your browser.';
        return;
    }

    navigator.geolocation.getCurrentPosition(async (position) => {
        try {
            const lat = position.coords.latitude;
            const lon = position.coords.longitude;

            const pointsRes = await fetch(`https://api.weather.gov/points/${lat},${lon}`);
            if (!pointsRes.ok) throw new Error('Weather API Error');
            const pointsData = await pointsRes.json();
            const forecastUrl = pointsData.properties.forecastHourly;

            const forecastRes = await fetch(forecastUrl);
            if (!forecastRes.ok) throw new Error('Forecast API Error');
            const forecastData = await forecastRes.json();
            const periods = forecastData.properties.periods.slice(0, 48);

            // Update Cache
            weatherCache = periods;
            weatherCacheTimestamp = Date.now();

            if (!background) {
                if (!periods.length) {
                    content.textContent = 'No forecast data available.';
                    return;
                }
                populateWeatherUI(periods);
            } else {
                console.log('Weather cached successfully via background fetch.');
            }

        } catch (err) {
            console.error(err);
            if (!background && content) content.textContent = 'Unable to fetch weather forecast.';
        }
    }, (err) => {
        console.error(err);
        if (!background && content) content.textContent = 'Location access denied. Cannot fetch weather.';
    });
}

function populateWeatherUI(periods) {
    const content = document.getElementById('weatherContent');
    const recommendation = document.getElementById('weatherRecommendation');

    // Safety check just in case modal was closed or elements missing
    if (!content || !recommendation) return;

    const current = periods[0];
    content.innerHTML = `Current: <strong>${current.temperature}°${current.temperatureUnit}</strong>, ${current.shortForecast}`;

    const next12 = periods.slice(0, 12);
    const avgTemp = next12.reduce((acc, p) => acc + p.temperature, 0) / next12.length;

    let bestPeriod = null;
    let reason = "";

    if (avgTemp < 60) {
        const daytime = periods.filter(p => p.isDaytime);
        if (daytime.length) {
            bestPeriod = daytime.reduce((prev, curr) => curr.temperature > prev.temperature ? curr : prev);
            reason = "Warmest time";
        } else {
            bestPeriod = periods.reduce((prev, curr) => curr.temperature > prev.temperature ? curr : prev);
            reason = "Warmest time (night)";
        }
    } else {
        const daytime = periods.filter(p => p.isDaytime);
        if (daytime.length) {
            bestPeriod = daytime.reduce((prev, curr) => curr.temperature < prev.temperature ? curr : prev);
            reason = "Coolest daytime";
        } else {
            bestPeriod = periods.reduce((prev, curr) => curr.temperature < prev.temperature ? curr : prev);
            reason = "Coolest time";
        }
    }

    if (bestPeriod) {
        const bestDate = new Date(bestPeriod.startTime);
        const timeStr = bestDate.toLocaleString('en-US', { weekday: 'short', hour: 'numeric' });
        recommendation.innerHTML = `💡 Best time: <strong>${timeStr}</strong> - ${bestPeriod.temperature}°${bestPeriod.temperatureUnit} (${bestPeriod.shortForecast})<br><small>(${reason} based on ${avgTemp < 60 ? 'cold' : 'warm'} weather)</small>`;

        // Auto-set date and time inputs
        const year = bestDate.getFullYear();
        const month = String(bestDate.getMonth() + 1).padStart(2, '0');
        const day = String(bestDate.getDate()).padStart(2, '0');

        const hour = String(bestDate.getHours()).padStart(2, '0');
        const minute = String(bestDate.getMinutes()).padStart(2, '0');

        const dateInput = document.getElementById('calendarDate');
        const timeInput = document.getElementById('calendarTime');

        if (dateInput && timeInput) {
            dateInput.value = `${year}-${month}-${day}`;
            timeInput.value = `${hour}:${minute}`;
        }

        showToast(`Auto-selected ${timeStr} based on weather!`, 'success');
    }
}

async function handleSendInvite(e) {
    e.preventDefault();
    const choreId = document.getElementById('calendarChoreId').value;
    const dateVal = document.getElementById('calendarDate').value;
    const timeVal = document.getElementById('calendarTime').value;
    const recurrenceVal = document.getElementById('calendarRecurrence').value;

    if (!activeUser) return;

    // Combine date and time
    // We create a date object then get ISO string
    const dateTime = new Date(`${dateVal}T${timeVal}`);

    try {
        const res = await fetch(`/api/chores/${choreId}/invite`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                user_id: activeUser.id,
                datetime: dateTime.toISOString(),
                recurrence: recurrenceVal
            })
        });

        const data = await res.json();

        if (res.ok) {
            showToast(data.message, 'success');
            closeModal('calendarModal');
        } else {
            showToast(data.error || 'Unknown error', 'error');
        }
    } catch (err) {
        console.error(err);
        showToast('Failed to send invite', 'error');
    }
}


// -- UI Helpers --
function showToast(message, type = 'success') {
    const toaster = document.getElementById('toaster');
    toaster.innerText = message;
    toaster.className = ''; // reset
    toaster.classList.add('show', type);

    // Clear previous timeout if any (simple implementation doesn't track it, but okay for basic usage)
    setTimeout(() => {
        toaster.classList.remove('show');
    }, 3000);
}
function openModal(id) {
    document.getElementById(id).classList.add('active');
    // Focus first input
    const firstInput = document.getElementById(id).querySelector('input');
    if (firstInput) firstInput.focus();
}

function closeModal(id) {
    document.getElementById(id).classList.remove('active');
}

// Close modal on outside click
window.onclick = function (event) {
    if (event.target.classList.contains('modal')) {
        event.target.classList.remove('active');
    }
}
