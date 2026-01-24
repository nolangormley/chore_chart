// State
let users = [];
let chores = [];
let activeUser = null;

// Initialization
document.addEventListener('DOMContentLoaded', () => {
    fetchUsers();
    fetchChores();
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
            alert('Failed to create user');
        }
    } catch (err) {
        console.error(err);
    }
}

async function handleAddChore(e) {
    e.preventDefault();
    const title = document.getElementById('choreTitle').value;
    const description = document.getElementById('choreDesc').value;
    const points = document.getElementById('chorePoints').value;
    const is_recurring = document.getElementById('choreRecurring').checked;
    
    try {
        const res = await fetch('/api/chores', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ title, description, points, is_recurring })
        });
        
        if (res.ok) {
            closeModal('choreModal');
            // reset form
            document.getElementById('choreTitle').value = '';
            document.getElementById('choreDesc').value = '';
            document.getElementById('choreRecurring').checked = false;
            fetchChores();
        } else {
            alert('Failed to create chore');
        }
    } catch (err) {
        console.error(err);
    }
}

async function completeChore(choreId, points) {
    if (!activeUser) {
        alert('Please select a user first!');
        document.getElementById('userSelect').focus();
        return;
    }
    
    if (!confirm(`Mark this chore as done by ${activeUser.username} for ${points} points?`)) return;
    
    try {
        const res = await fetch(`/api/chores/${choreId}/complete`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ user_id: activeUser.id })
        });
        
        if (res.ok) {
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
    
    container.innerHTML = sorted.map((u, index) => `
        <div style="background: var(--background); padding: 1rem; border-radius: var(--radius); border: 1px solid var(--border); min-width: 150px; text-align: center;">
            <div style="font-size: 0.8rem; color: var(--text-muted); margin-bottom: 0.5rem;">#${index + 1}</div>
            <div style="font-weight: bold; font-size: 1.1rem; margin-bottom: 0.25rem;">${u.username}</div>
            <div class="badge">${u.total_points} pts</div>
        </div>
    `).join('');
}

function renderChores() {
    const container = document.getElementById('choreList');
    
    if (!chores.length) {
        container.innerHTML = '<div style="grid-column: 1/-1; text-align: center; color: var(--text-muted); padding: 3rem; background: var(--surface); border-radius: var(--radius); border: 1px dashed var(--border);">No active chores. Create one to get started!</div>';
        return;
    }
    
    container.innerHTML = chores.map(c => `
        <div class="card fade-in" style="display: flex; flex-direction: column; justify-content: space-between;">
            <div>
                <div class="flex-between" style="margin-bottom: 0.5rem; align-items: flex-start;">
                    <h3 style="font-size: 1.25rem;">${c.title}</h3>
                    <div class="badge">${c.points} pts</div>
                </div>
                <p style="color: var(--text-muted); margin-bottom: 1rem; font-size: 0.9rem;">
                    ${c.description || 'No description'}
                </p>
                ${c.is_recurring ? '<div style="font-size: 0.8rem; color: var(--secondary); margin-bottom: 1rem;"><span style="display:inline-block; transform: rotate(45deg); margin-right:4px;">↻</span> Recurring</div>' : ''}
            </div>
            
            <div class="flex-between" style="border-top: 1px solid var(--border); padding-top: 1rem; margin-top: 1rem;">
                <button class="btn btn-danger" onclick="deleteChore(${c.id})" style="padding: 0.4rem 0.8rem; font-size: 0.8rem;">
                    Delete
                </button>
                <button class="btn btn-primary" onclick="completeChore(${c.id}, ${c.points})">
                    Complete
                </button>
            </div>
        </div>
    `).join('');
}


// -- UI Helpers --
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
window.onclick = function(event) {
    if (event.target.classList.contains('modal')) {
        event.target.classList.remove('active');
    }
}
