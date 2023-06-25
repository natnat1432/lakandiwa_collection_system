$(document).ready(function() {
    // Target the checkbox by its ID
    $('#exempted_checkbox').change(function() {
      if ($(this).is(':checked')) {
        $('#exempted_category').removeAttr('hidden');
      } else {
        $('#exempted_category').attr('hidden', true);
      }
    });

      $('#collection_studentID').on('input', function() {
        var input = $(this).val();
        $(this).val(input.replace(/[^0-9]/g, '').substring(0, 8));
      });
  
      // $('#collection_ackID').on('input', function() {
      //   var input = $(this).val();
      //   $(this).val(input.replace(/[^0-9]/g, ''));
      // });
  
  });