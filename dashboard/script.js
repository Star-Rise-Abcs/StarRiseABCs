const API_URL = "https://starriseabcsapi.onrender.com";
let teacherData = null;
let currentSelectedClass = null;

async function handleLogin() {
    const u = document.getElementById('loginUser').value;
    const p = document.getElementById('loginPass').value;
    const res = await fetch(`${API_URL}/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username: u, password: p })
    });
    if (res.ok) {
        teacherData = await res.json();
        // SAVE the teacher's name to use when creating classes
        const fullName = `${teacherData.first_name} ${teacherData.last_name}`;
        localStorage.setItem('teacherDisplayName', fullName);

        document.getElementById('authScreen').classList.add('hidden');
        loadAllClasses();
    } else { alert("Invalid Login"); }
}

async function loadAllClasses() {
    const res = await fetch(`${API_URL}/get_all_classes`);
    const classes = await res.json();
    renderClassGrid(classes);
    console.log("Database Response:", classes); // <--- ADD THIS
}

function renderClassGrid(classes) {
    const grid = document.getElementById('classGrid');
    grid.innerHTML = classes.map(cls => `
        <div class="class-card">
            <button class="btn-delete-class" onclick="deleteClass('${cls.class_code}')">×</button>
            <h3 style="color: #1a1a1a; margin-top:15px;">${cls.class_code}</h3>
            
            <p style="color: #147c25; font-size: 11px; font-weight: bold; margin-bottom: 5px;">
                Added by: ${cls.creator_name || 'System'}
            </p>
            
            <p style="color: #666; font-size: 13px; margin-bottom: 10px;">
                ${cls.student_count || 0} Students Enrolled
            </p>
            
            <button class="btn-enter" onclick="enterClass('${cls.class_code}')">View Details</button>
        </div>
    `).join('');
}

async function createNewClass() {
    const codeInput = document.getElementById('newClassCode');
    const classCode = codeInput.value.trim().toUpperCase();

    if (!classCode) return alert("Please enter a valid Class Name!");
    if (!teacherData) return alert("Please log in first!");

    const res = await fetch(`${API_URL}/create_class`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            class_code: classCode,
            user_id: teacherData.id,
            creator_name: `${teacherData.first_name} ${teacherData.last_name}`
        })
    });

    if (res.ok) {
        codeInput.value = "";
        loadAllClasses();
    } else {
        // This grabs the "Class already exists!" message from the backend
        const errData = await res.json();
        alert(errData.detail || "Failed to create class.");
    }
}


async function deleteClass(classCode) {
    if (confirm(`Delete class ${classCode}?`)) {
        // Use backticks (`) not single quotes (') here:
        await fetch(`${API_URL}/delete_class/${classCode}`, { method: 'DELETE' });
        loadAllClasses();
    }
}

async function enterClass(classCode) {
    currentSelectedClass = classCode.toUpperCase();

    // 1. Hide Search Results and the Main Dashboard
    document.getElementById('search-class-results').classList.add('hidden');
    document.getElementById('search-class-results').innerHTML = "";
    document.getElementById('view-all-classes').classList.add('hidden');
    document.getElementById('globalSearch').value = "";

    // 2. Setup the "Official" Class View
    document.getElementById('view-progress').classList.remove('hidden');
    document.getElementById('btnBack').classList.remove('hidden');
    document.getElementById('classNavTabs').style.display = 'flex';
    document.getElementById('viewTitle').innerText = `Class: ${currentSelectedClass}`;

    // --- ADD THIS LINE HERE ---
    document.getElementById('enrollmentBox').classList.remove('hidden');
    // ----------------------------

    // 3. Fetch fresh, filtered data for just THIS class
    await fetchStudents(currentSelectedClass);
    await loadClassRewards(currentSelectedClass);

    switchTab('progress');
}

function backToDashboard() {
    currentSelectedClass = null;

    // Clear and Hide Search Results
    const searchDiv = document.getElementById('search-class-results');
    searchDiv.innerHTML = "";
    searchDiv.classList.add('hidden');
    document.getElementById("globalSearch").value = "";

    // Reset Visibility
    document.getElementById('view-all-classes').classList.remove('hidden');
    document.getElementById('view-progress').classList.add('hidden');
    document.getElementById('view-rewards').classList.add('hidden');
    document.getElementById('btnBack').classList.add('hidden');
    document.getElementById('classNavTabs').style.display = 'none';
    document.getElementById('viewTitle').innerText = "All Classes";
    document.getElementById('enrollmentBox').classList.add('hidden');

    loadAllClasses();
}

function switchTab(tab) {
    const isProg = tab === 'progress';
    document.getElementById('view-progress').classList.toggle('hidden', !isProg);
    document.getElementById('view-rewards').classList.toggle('hidden', isProg);
    document.getElementById('tabProg').classList.toggle('active', isProg);
    document.getElementById('tabRew').classList.toggle('active', !isProg);
}

async function fetchStudents(classCode) {
    const res = await fetch(`${API_URL}/get_class_report/${classCode}`);
    const students = await res.json();
    const rewardRes = await fetch(`${API_URL}/get_class_rewards/${classCode}`);
    const rewards = await rewardRes.json();
    renderStudentTable(students, rewards);
}

function renderStudentTable(students, rewards) {
    const studentList = document.getElementById('student-list');

    studentList.innerHTML = students.map(u => {
        // We only show the (CLASS_CODE) if we are in Search Mode 
        // (i.e., if currentSelectedClass is null)
        const showClass = !currentSelectedClass ?
            `<span style="color: #666; font-size: 0.85em; font-weight: normal;"> (${u.class_code})</span>` : "";

        return `
            <tr>
                <td style="font-weight: bold; color: #147c25;">
                    ${u.name}${showClass}
                </td>
                <td><span class="star-pill">${u.abc} / 26 Stars</span></td>
                <td><span class="star-pill">${u.quiz1} Stars</span></td>
                <td><span class="star-pill">${u.quiz2} Stars</span></td>
                <td><span class="star-pill">${u.quiz3} Stars</span></td>
            </tr>
        `;
    }).join('');
}
async function doSearch() {
    const query = document.getElementById("globalSearch").value.trim();
    if (!query) return backToDashboard();

    const res = await fetch(`${API_URL}/search_all_students?query=${encodeURIComponent(query)}`);
    const data = await res.json();

    // 1. You MUST define these variables inside the function
    const classResultsDiv = document.getElementById('search-class-results');
    const viewProgress = document.getElementById('view-progress');
    const viewAllClasses = document.getElementById('view-all-classes');

    // 2. Clear current views and show the "Back" button
    classResultsDiv.innerHTML = "";
    document.getElementById('student-list').innerHTML = "";
    viewAllClasses.classList.add('hidden');
    document.getElementById('classNavTabs').style.display = 'none';
    document.getElementById('btnBack').classList.remove('hidden');

    // 3. Handle No Results
    if (data.matched_classes.length === 0 && data.matched_students.length === 0) {
        document.getElementById('viewTitle').innerText = `No results found for "${query.toUpperCase()}"`;
        viewProgress.classList.add('hidden');
        classResultsDiv.classList.add('hidden');
        return;
    }

    document.getElementById('viewTitle').innerText = `Search Results: ${query.toUpperCase()}`;

    // 4. Render Class Cards (now using creator_name from the backend)
    if (data.matched_classes.length > 0) {
        classResultsDiv.classList.remove('hidden');
        const addSection = document.querySelector('.add-student-section');
        if (addSection) addSection.classList.add('hidden');

        renderStudentTable(data.matched_students, []);
        classResultsDiv.innerHTML = data.matched_classes.map(cls => `
            <div class="class-card">
                <button class="btn-delete-class" onclick="deleteClass('${cls.class_code}')">×</button>
                <h3 style="color: #1a1a1a; margin-top:15px;">CLASS: ${cls.class_code}</h3>
                
                <p style="color: #147c25; font-size: 11px; font-weight: bold; margin-bottom: 5px;">
                    Added by: ${cls.creator_name || 'System'}
                </p>

                <p style="color: #666; font-size: 13px; margin-bottom: 10px;">
                    ${cls.student_count || 0} Students Enrolled
                </p>

                <button class="btn-enter" onclick="enterClass('${cls.class_code}')">View Details</button>
            </div>
        `).join('');
    } else {
        classResultsDiv.classList.add('hidden');
    }

    // 5. Render Student Progress table
    if (data.matched_students.length > 0) {
        viewProgress.classList.remove('hidden');
        renderStudentTable(data.matched_students, []);
    } else {
        viewProgress.classList.add('hidden');
    }
}

async function loadClassRewards(classCode) {
    const res = await fetch(`${API_URL}/get_class_rewards/${classCode}`);
    const rewards = await res.json();
    const container = document.getElementById('reward-editor-list');
    container.innerHTML = "";
    ['abc', 'video', 'quiz1', 'quiz2', 'quiz3'].forEach(act => {
        const cur = rewards.find(r => r.icon_type === act) || { reward_name: "None", stars_required: 0 };
        container.innerHTML += `
            <div class="reward-edit-row">
                <label>${act.toUpperCase()}</label>
                <input type="text" id="name-${act}" value="${cur.reward_name}">
                <input type="number" id="stars-${act}" value="${cur.stars_required}" style="width: 80px;">
                <button class="btn-update" onclick="saveRewardEdit('${act}')">Update</button>
            </div>`;
    });
}

async function saveRewardEdit(act) {
    const name = document.getElementById(`name-${act}`).value;
    const stars = document.getElementById(`stars-${act}`).value;
    await fetch(`${API_URL}/update_specific_reward`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ class_code: currentSelectedClass, reward_name: name, stars_required: parseInt(stars), icon_type: act })
    });
    document.getElementById('last-update').innerText = new Date().toLocaleTimeString();
}

function toggleAuth(isRegistering) {
    document.getElementById('login-view').classList.toggle('hidden', isRegistering);
    document.getElementById('register-view').classList.toggle('hidden', !isRegistering);
}

async function handleRegister() {
    const payload = {
        first_name: document.getElementById('regFirst').value.trim(),
        last_name: document.getElementById('regLast').value.trim(),
        username: document.getElementById('regUser').value.trim(),
        password: document.getElementById('regPass').value.trim(),
        access_code: document.getElementById('teacherSecret').value.trim()
    };

    if (!payload.first_name || !payload.username || !payload.password) {
        return alert("Please fill in all fields.");
    }

    const res = await fetch(`${API_URL}/register_teacher`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
    });

    if (res.ok) {
        alert("Registration successful! You can now log in.");
        toggleAuth(false); // Switch back to login
    } else {
        const err = await res.json();
        alert(err.detail || "Registration failed");
    }
}

let allStudentsMaster = [];
async function searchMasterStudents() {
    const query = document.getElementById('masterStudentSearch').value.trim().toLowerCase();
    const resultsDiv = document.getElementById('masterStudentResults');

    // 1. Hide if query is too short
    if (query.length < 2) {
        resultsDiv.classList.add('hidden');
        resultsDiv.innerHTML = "";
        return;
    }

    // 2. Load the master list from DB if we haven't yet
    if (allStudentsMaster.length === 0) {
        const res = await fetch(`${API_URL}/get_unassigned_students`);
        allStudentsMaster = await res.json();
    }

    // 3. FILTER: The Logic Fix is here
    const filtered = allStudentsMaster.filter(s => {
        const firstName = (s.first_name || "").toLowerCase();
        const lastName = (s.last_name || "").toLowerCase();
        const username = (s.username || "").toLowerCase();

        // Create the combined full name
        const fullName = `${firstName} ${lastName}`;

        // Match against first, last, username, OR the combined full name
        return firstName.includes(query) ||
            lastName.includes(query) ||
            username.includes(query) ||
            fullName.includes(query);
    });

    if (filtered.length === 0) {
        resultsDiv.innerHTML = `<div style="padding:10px; color:#999; font-size:12px;">No matching students found...</div>`;
    } else {
        resultsDiv.innerHTML = filtered.map(s => {
            const isSameClass = s.class_code === currentSelectedClass;
            const currentClassLabel = s.class_code ? s.class_code : "No Class Assigned";

            // Logic for the button vs "Already in" text
            const actionUI = isSameClass
                ? `<span style="color: #147c25; font-size: 11px; font-weight: bold; background: #e8f5e9; padding: 2px 6px; border-radius: 4px;">Enrolled Here</span>`
                : `<button onclick="enrollStudent('${s.id}', '${s.first_name} ${s.last_name}', '${s.class_code || ''}')" 
                           style="padding:5px 12px; background:#147c25; color:white; border:none; border-radius:4px; cursor:pointer; font-size:11px;">
                        + Add
                   </button>`;

            return `
                <div style="padding:12px; border-bottom:1px solid #eee; display:flex; justify-content:space-between; align-items:center; font-size:13px;">
                    <div>
                        <strong style="color: #333;">${s.first_name} ${s.last_name}</strong> <br>
                        <span style="color: #666; font-size: 11px;">User: <strong>${s.username}</strong> | Class: ${currentClassLabel}</span>
                    </div>
                    <div>${actionUI}</div>
                </div>
            `;
        }).join('');
    }

    resultsDiv.classList.remove('hidden');
}

async function enrollStudent(studentId, studentName, oldClassCode) {
    // 1. If they have a class and it's NOT the current one, ask for confirmation
    if (oldClassCode && oldClassCode !== "NONE" && oldClassCode !== "") {
        const confirmMove = confirm(`${studentName} is currently in class [${oldClassCode}]. Do you want to move them to [${currentSelectedClass}]?`);
        if (!confirmMove) return;
    }

    const res = await fetch(`${API_URL}/assign_student_to_class`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            student_id: studentId,
            class_code: currentSelectedClass
        })
    });

    if (res.ok) {
        document.getElementById('masterStudentSearch').value = "";
        document.getElementById('masterStudentResults').classList.add('hidden');

        // Clear cache so the next search sees the updated class_code
        allStudentsMaster = [];

        await fetchStudents(currentSelectedClass);
        loadAllClasses();

        alert(`${studentName} is now enrolled in ${currentSelectedClass}!`);
    } else {
        alert("Failed to update student enrollment.");
    }
}
