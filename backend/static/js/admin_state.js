// File: backend/static/js/admin_state.js

document.addEventListener('DOMContentLoaded', function() {
    const changelistForm = document.getElementById('changelist-form');
    if (!changelistForm) return;

    const KEY = 'djangoAdminSelectedIds';

    // 1. Sau khi trang tải lại, kiểm tra xem có ID nào được lưu không
    const selectedIds = sessionStorage.getItem(KEY);
    if (selectedIds) {
        const ids = selectedIds.split(',');
        ids.forEach(id => {
            const checkbox = changelistForm.querySelector(`input[name="_selected_action"][value="${id}"]`);
            if (checkbox) {
                checkbox.checked = true;
            }
        });
        // Xóa đi để không bị tick lại ở lần tải trang sau
        sessionStorage.removeItem(KEY);
    }

    // 2. Trước khi gửi form đi để thực hiện action
    changelistForm.addEventListener('submit', function() {
        const actionSelect = this.querySelector('select[name="action"]');
        // Chỉ lưu khi một action thực sự được chọn (không phải lọc hay tìm kiếm)
        if (actionSelect && actionSelect.value) {
            const selectedCheckboxes = this.querySelectorAll('input[name="_selected_action"]:checked');
            const idsToSave = Array.from(selectedCheckboxes).map(cb => cb.value);
            if (idsToSave.length > 0) {
                sessionStorage.setItem(KEY, idsToSave.join(','));
            }
        }
    });
});