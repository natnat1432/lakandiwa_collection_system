function duplicateForm() {
    var originalForm = document.querySelector('.importForm');
    var duplicateForm = originalForm.cloneNode(true);
    
    // Clear the input values in the duplicated form
    var inputFields = duplicateForm.querySelectorAll('input, select');
    inputFields.forEach(function(field) {
      field.value = '';
    });
    
    var deleteButton = document.createElement('button');
    deleteButton.className = 'btn btn-danger';
    deleteButton.textContent = 'Delete';
    deleteButton.addEventListener('click', function() {
      deleteForm(this);
    });
    
    duplicateForm.appendChild(deleteButton);
    
    originalForm.parentNode.appendChild(duplicateForm);
  }
  
  function deleteForm(button) {
    var form = button.parentNode;
    form.parentNode.removeChild(form);
  }