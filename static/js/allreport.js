$(document).ready(function() {
 
    $('#exempted_checkbox').change(function() {
      if ($(this).is(':checked')) {
        $('#exempted_category').removeAttr('hidden');
      } else {
        $('#exempted_category').attr('hidden', true);
      }
    });

    $('#edit_exempted_checkbox').change(function() {
      if ($(this).is(':checked')) {
        $('#edit_collection_exempted_category').removeAttr('hidden');
      } else {
        $('#edit_collection_exempted_category').attr('hidden', true);
      }
    });

      $('#collection_studentID').on('input', function() {
        var input = $(this).val();
        $(this).val(input.replace(/[^0-9]/g, '').substring(0, 8));
      });
      $('#edit_collection_studentID').on('input', function() {
        var input = $(this).val();
        $(this).val(input.replace(/[^0-9]/g, '').substring(0, 8));
      });



      $('#sort_filter').change(function(){
        refreshPage();
      });
      $('#student_filter').change(function(){
        if($(this).val() === 'all' || $(this).val() == 'not_excempted')
        {
          refreshPage();
        }
        else{
          $('#excempted_filter_div').removeAttr('hidden');
        }
      });
      $('#excempted_filter').change(function(){
        refreshPage();
      });
      $('#course_filter').change(function(){
        refreshPage();
      });
      $('#year_filter').change(function(){
        refreshPage();
      });
      $('#void_filter').change(function(){
        refreshPage();
      });
  
  });


  function refreshPage(){
    var sort_filter = document.getElementById("sort_filter").value;
    var student_filter = document.getElementById("student_filter").value;
    var excempted_filter = document.getElementById("excempted_filter").value;
    var course_filter = document.getElementById("course_filter").value;
    var year_filter = document.getElementById("year_filter").value;
    var void_filter = document.getElementById("void_filter").value;

    var search_query = document.getElementById("search_query").value;

    var distinct_date = document.getElementById("distinct_date").value;
    var distinct_day = document.getElementById("distinct_day").value;

    window.location.href= `/allreports?sort_filter=${sort_filter}&student_filter=${student_filter}&excempted_filter=${excempted_filter}&course_filter=${course_filter}&year_filter=${year_filter}&void_filter=${void_filter}&search_query=${search_query}`;
  }

  function setDeleteCollectionModal(id)
  {
    document.getElementById("delete_collection_id").value = id;
  }

  function setEditCollectionModal(ackID,studentID,firstname,middlename,lastname,course,year,category)
  {
    document.getElementById("edit_collection_ackID").value = ackID;
    document.getElementById("edit_collection_studentID").value = studentID;
    document.getElementById("edit_collection_fname").value = firstname;
    document.getElementById("edit_collection_mname").value = middlename;
    document.getElementById("edit_collection_lname").value = lastname;
    document.getElementById("edit_collection_course").value = course;
    document.getElementById("edit_collection_year").value = year;
    
    if(category != "None")
    {
      document.getElementById("edit_collection_exempted_category").removeAttribute("hidden");
      document.getElementById("edit_exempted_checkbox").checked = true;
      document.getElementById("exempted_category".value = category);

    }
    else{
      document.getElementById("edit_exempted_checkbox").checked = false;
      document.getElementById("edit_collection_exempted_category").setAttribute("hidden", true);
    }
  }

  function setVoidTicketModal(ackID)
  {
    document.getElementById("void_ticket_input").value = ackID;
  }