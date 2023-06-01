$(document).ready(function() {
    $('#login-userID').on('input', function() {
      var input = $(this).val();
      $(this).val(input.replace(/[^0-9]/g, '').substring(0, 8));
    });
  });