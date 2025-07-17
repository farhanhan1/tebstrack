// Animated category edit logic for settings.html
// This script enables edit-in-place with fade/slide animation, Save/Cancel buttons, and updates category name via AJAX.
document.addEventListener('DOMContentLoaded', function() {
  document.querySelectorAll('.edit-category-btn').forEach(function(btn) {
    btn.addEventListener('click', function() {
      var row = btn.closest('.category-row');
      var nameSpan = row.querySelector('.category-name');
      var editField = row.querySelector('.edit-category-field');
      var saveBtn = row.querySelector('.save-category-btn');
      var cancelBtn = row.querySelector('.cancel-category-btn');
      // Show edit field with animation
      editField.style.display = 'block';
      editField.style.opacity = 0;
      editField.style.transform = 'translateY(-10px)';
      setTimeout(function() {
        editField.style.transition = 'opacity 0.3s, transform 0.3s';
        editField.style.opacity = 1;
        editField.style.transform = 'translateY(0)';
      }, 10);
      nameSpan.style.display = 'none';
      btn.style.display = 'none';
      saveBtn.style.display = 'inline-block';
      cancelBtn.style.display = 'inline-block';
    });
  });
  document.querySelectorAll('.cancel-category-btn').forEach(function(btn) {
    btn.addEventListener('click', function() {
      var row = btn.closest('.category-row');
      var nameSpan = row.querySelector('.category-name');
      var editField = row.querySelector('.edit-category-field');
      var editBtn = row.querySelector('.edit-category-btn');
      var saveBtn = row.querySelector('.save-category-btn');
      // Hide edit field with animation
      editField.style.transition = 'opacity 0.3s, transform 0.3s';
      editField.style.opacity = 0;
      editField.style.transform = 'translateY(-10px)';
      setTimeout(function() {
        editField.style.display = 'none';
        nameSpan.style.display = 'inline-block';
        editBtn.style.display = 'inline-block';
        saveBtn.style.display = 'none';
        btn.style.display = 'none';
      }, 300);
    });
  });
  document.querySelectorAll('.save-category-btn').forEach(function(btn) {
    btn.addEventListener('click', function() {
      var row = btn.closest('.category-row');
      var nameSpan = row.querySelector('.category-name');
      var editField = row.querySelector('.edit-category-field');
      var editBtn = row.querySelector('.edit-category-btn');
      var cancelBtn = row.querySelector('.cancel-category-btn');
      var newName = editField.value.trim();
      var oldName = nameSpan.textContent.trim();
      if (!newName || newName === oldName) {
        // Just cancel
        cancelBtn.click();
        return;
      }
      // AJAX update
      fetch('/edit_category/' + encodeURIComponent(oldName), {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: 'new_category=' + encodeURIComponent(newName)
      })
      .then(function(r) { return r.text(); })
      .then(function() {
        // Update UI
        nameSpan.textContent = newName;
        editField.value = newName;
        cancelBtn.click();
      })
      .catch(function() {
        alert('Error updating category.');
        cancelBtn.click();
      });
    });
  });
});
