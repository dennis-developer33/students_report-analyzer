// ===== Navigation & Page Switching =====
let currentPage = 'upload';

document.getElementById('uploadNav').addEventListener('click', () => showPage('upload'));
document.getElementById('dataNav').addEventListener('click', () => showPage('data'));
document.getElementById('analyticsNav').addEventListener('click', () => showPage('analytics'));

const mobileMenuBtn = document.getElementById('mobileMenuBtn');
const mobileMenu = document.getElementById('mobileMenu');
const closeMobileMenu = document.getElementById('closeMobileMenu');

mobileMenuBtn.addEventListener('click', () => mobileMenu.classList.add('open'));
closeMobileMenu.addEventListener('click', () => mobileMenu.classList.remove('open'));

document.querySelectorAll('.mobile-nav-link').forEach(link => {
    link.addEventListener('click', (e) => {
        const page = e.target.getAttribute('data-page');
        showPage(page);
        mobileMenu.classList.remove('open');
    });
});

function showPage(page) {
    document.querySelectorAll('.page-content').forEach(p => p.classList.add('hidden'));
    document.getElementById(page + 'Page').classList.remove('hidden');
    document.getElementById(page + 'Page').classList.add('fade-in');

    document.querySelectorAll('.nav-link').forEach(link => {
        link.classList.remove('text-blue-600', 'font-semibold');
        link.classList.add('text-gray-700');
    });

    const activeNav = document.getElementById(page + 'Nav');
    if (activeNav) {
        activeNav.classList.remove('text-gray-700');
        activeNav.classList.add('text-blue-600', 'font-semibold');
    }

    currentPage = page;

    if (page === 'analytics') initializeCharts();
}

// ===== File Upload =====
const dropZone = document.getElementById('dropZone');
const fileInput = document.getElementById('fileInput');
const statusBox = document.getElementById('status');

// Drag & drop
dropZone.addEventListener('dragover', (e) => {
    e.preventDefault();
    dropZone.classList.add('drag-over');
});

dropZone.addEventListener('dragleave', () => dropZone.classList.remove('drag-over'));

dropZone.addEventListener('drop', (e) => {
    e.preventDefault();
    dropZone.classList.remove('drag-over');
    const files = e.dataTransfer.files;
    if (files.length > 0) uploadFile(files[0]);
});

// File selection
fileInput.addEventListener('change', (e) => {
    if (e.target.files.length > 0) uploadFile(e.target.files[0]);
});

// Upload logic
function uploadFile(file) {
    if (!file.name.endsWith('.csv')) {
        showStatus('❌ Please upload a CSV file.', 'error');
        return;
    }

    const formData = new FormData();
    formData.append('file', file);

    showStatus('⏳ Uploading file...', 'info');

    fetch('/upload', { method: 'POST', body: formData })
        .then(response => response.json())
        .then(data => {
            showStatus('✅ File uploaded successfully!', 'success');
            setTimeout(() => {
                showPage('data');
                loadData();
            }, 800);
        })
        .catch(err => {
            console.error(err);
            showStatus('❌ Error uploading file.', 'error');
        });
}

// Helper: update status box
function showStatus(message, type) {
    statusBox.textContent = message;
    statusBox.classList.remove('hidden', 'bg-green-100', 'text-green-800', 'bg-red-100', 'text-red-800', 'bg-blue-100', 'text-blue-800');

    if (type === 'success') {
        statusBox.classList.add('bg-green-100', 'text-green-800');
    } else if (type === 'error') {
        statusBox.classList.add('bg-red-100', 'text-red-800');
    } else {
        statusBox.classList.add('bg-blue-100', 'text-blue-800');
    }
}

// ===== Data Table =====
function loadData(filters = {}) {
    let url = '/filter_data';
    if (Object.keys(filters).length > 0) {
        const params = new URLSearchParams(filters);
        url += '?' + params.toString();
    }

    fetch(url)
        .then(res => res.json())
        .then(data => populateTable(data.data))
        .catch(err => console.error(err));
}

function populateTable(data) {
    const tbody = document.getElementById('dataTableBody');
    tbody.innerHTML = '';

    data.forEach(row => {
        const tr = document.createElement('tr');
        tr.classList.add('hover:bg-gray-50');
        tr.innerHTML = `
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">${row.Username_TRNO}</td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">${row.Student_FullName}</td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">${row.Student_Class}</td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-blue-600 hover:text-blue-800">
                <a href="${row.Website_Address}" class="truncate max-w-xs block" target="_blank">${row.Website_Address}</a>
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">${row.Visits_to_Website}</td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">${row.Last_Visit_Time}</td>
            <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">${row.Total_Visits}</td>
        `;
        tbody.appendChild(tr);
    });
}

// ===== Filters & Export =====
document.getElementById('applyFilters').addEventListener('click', () => {
    const filters = {
        username: document.getElementById('searchInput').value,
        student_class: document.getElementById('classFilter').value,
        date: document.getElementById('dateFilter').value
    };
    loadData(filters);
});

document.getElementById('clearFilters').addEventListener('click', () => {
    document.getElementById('searchInput').value = '';
    document.getElementById('classFilter').value = '';
    document.getElementById('dateFilter').value = '';
    loadData();
});

document.getElementById('exportCSV').addEventListener('click', () => {
    window.location.href = '/export/csv';
});

document.getElementById('exportPDF').addEventListener('click', () => {
    window.location.href = '/export/pdf';
});

// ===== Analytics Charts =====
let topWebsitesChart, activeStudentsChart, visitsTimeChart;

function initializeCharts() {
    fetch('/analytics_data')
        .then(res => res.json())
        .then(data => {
            // Top Websites
            const ctx1 = document.getElementById('topWebsitesChart').getContext('2d');
            if (topWebsitesChart) topWebsitesChart.destroy();
            topWebsitesChart = new Chart(ctx1, {
                type: 'bar',
                data: { labels: data.top_websites.labels, datasets: [{ label: 'Visits', data: data.top_websites.data, backgroundColor: 'rgba(59,130,246,0.8)' }] },
                options: { responsive: true, maintainAspectRatio: false }
            });

            // Active Students
            const ctx2 = document.getElementById('activeStudentsChart').getContext('2d');
            if (activeStudentsChart) activeStudentsChart.destroy();
            activeStudentsChart = new Chart(ctx2, {
                type: 'bar',
                data: { labels: data.active_students.labels, datasets: [{ label: 'Visits', data: data.active_students.data, backgroundColor: 'rgba(16,185,129,0.8)' }] },
                options: { indexAxis: 'y', responsive: true, maintainAspectRatio: false }
            });

            // Visits Over Time
            const ctx3 = document.getElementById('visitsTimeChart').getContext('2d');
            if (visitsTimeChart) visitsTimeChart.destroy();
            visitsTimeChart = new Chart(ctx3, {
                type: 'line',
                data: { labels: data.visits_over_time.labels, datasets: [{ label: 'Visits', data: data.visits_over_time.data, borderColor: 'rgba(139,92,246,1)', backgroundColor: 'rgba(139,92,246,0.1)', fill: true, tension: 0.4 }] },
                options: { responsive: true, maintainAspectRatio: false }
            });

            // Update summary cards
            document.querySelectorAll('.grid div:nth-child(1) .text-3xl').forEach(el => el.textContent = data.summary.total_students);
            document.querySelectorAll('.grid div:nth-child(2) .text-3xl').forEach(el => el.textContent = data.summary.total_visits);
            document.querySelectorAll('.grid div:nth-child(3) .text-3xl').forEach(el => el.textContent = data.summary.unique_websites);
            document.querySelectorAll('.grid div:nth-child(4) .text-3xl').forEach(el => el.textContent = data.summary.avg_visits_per_student);
        });
}

document.getElementById('updateCharts').addEventListener('click', () => {
    const filters = {
        username: document.getElementById('analyticsUsernameFilter').value,
        student_class: document.getElementById('analyticsClassFilter').value
    };
    fetch('/analytics_data?' + new URLSearchParams(filters))
        .then(res => res.json())
        .then(data => initializeCharts());
});

// ===== Initialize =====
showPage('upload');
