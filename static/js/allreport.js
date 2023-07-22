$(document).ready(function () {

  $('#exempted_checkbox').change(function () {
    if ($(this).is(':checked')) {
      $('#exempted_category').removeAttr('hidden');
    } else {
      $('#exempted_category').attr('hidden', true);
    }
  });

  $('#edit_exempted_checkbox').change(function () {
    if ($(this).is(':checked')) {
      $('#edit_collection_exempted_category').removeAttr('hidden');
    } else {
      $('#edit_collection_exempted_category').attr('hidden', true);
    }
  });

  $('#collection_studentID').on('input', function () {
    var input = $(this).val();
    $(this).val(input.replace(/[^0-9]/g, '').substring(0, 8));
  });
  $('#edit_collection_studentID').on('input', function () {
    var input = $(this).val();
    $(this).val(input.replace(/[^0-9]/g, '').substring(0, 8));
  });



  $('#sort_filter').change(function () {
    refreshPage();
  });
  $('#student_filter').change(function () {
    if ($(this).val() === 'all' || $(this).val() == 'not_excempted') {
      refreshPage();
    }
    else {
      $('#excempted_filter_div').removeAttr('hidden');
    }
  });
  $('#excempted_filter').change(function () {
    refreshPage();
  });
  $('#course_filter').change(function () {
    refreshPage();
  });
  $('#year_filter').change(function () {
    refreshPage();
  });
  $('#void_filter').change(function () {
    refreshPage();
  });

  $('#semester_filter').change(function () {
    console.log(this.value);
    refreshPage();
  });

  $('#searchForm').submit(function (event) {
    event.preventDefault();
    refreshPage();
    return false;
  });

  function toggleClearButton() {
    const searchQuery = $('#search_query').val().trim();
    const clearButton = $('#clear_button');

    if (searchQuery.length > 0) {
      clearButton.show();
    } else {
      clearButton.hide();
    }
  }

  // Call the toggleClearButton function on page load to initialize the button's visibility
  toggleClearButton();

  // Add an input event handler to the search input
  $('#search_query').on('input', function () {
    // Call toggleClearButton whenever the input value changes
    toggleClearButton();

  });

  // Add a click event handler to the "Clear Search" button
  $('#clear_button').on('click', function () {
    // Clear the search input and hide the "Clear Search" button
    $('#search_query').val('');
    toggleClearButton();
    refreshPage();
  });
});



function refreshPage() {
  var sort_filter = document.getElementById("sort_filter").value;
  var student_filter = document.getElementById("student_filter").value;
  var excempted_filter = document.getElementById("excempted_filter").value;
  var course_filter = document.getElementById("course_filter").value;
  var year_filter = document.getElementById("year_filter").value;
  var void_filter = document.getElementById("void_filter").value;

  var search_query = document.getElementById("search_query").value;
  var page_number = document.getElementById("page_number").value;


  var semester_filter = document.getElementById("semester_filter").value;

  window.location.href = `/allreports?sort_filter=${sort_filter}&student_filter=${student_filter}&excempted_filter=${excempted_filter}&course_filter=${course_filter}&year_filter=${year_filter}&void_filter=${void_filter}&search_query=${search_query}&semester_filter=${semester_filter}&page_number=${page_number}`;
}

function previousPage() {
  var page_number = document.getElementById("page_number").value;
  var page = document.getElementById("page_number");

  page.value = Number(page_number)-1;
  refreshPage();
}

function nextPage() {
  var page_number = document.getElementById("page_number").value;
  var page = document.getElementById("page_number");

  page.value = Number(page_number)+1;
  refreshPage();
}
function setDeleteCollectionModal(id) {
  document.getElementById("delete_collection_id").value = id;
}

function setEditCollectionModal(ackID, studentID, firstname, middlename, lastname, course, year, category, semester_id) {
  document.getElementById("edit_collection_ackID").value = ackID;
  document.getElementById("edit_collection_studentID").value = studentID;
  document.getElementById("edit_collection_fname").value = firstname;
  document.getElementById("edit_collection_mname").value = middlename;
  document.getElementById("edit_collection_lname").value = lastname;
  document.getElementById("edit_collection_course").value = course;
  document.getElementById("edit_collection_year").value = year;
  document.getElementById("edit_semester").value = semester_id;

  if (category != "None") {
    document.getElementById("edit_collection_exempted_category").removeAttribute("hidden");
    document.getElementById("edit_exempted_checkbox").checked = true;
    document.getElementById("exempted_category".value = category);

  }
  else {
    document.getElementById("edit_exempted_checkbox").checked = false;
    document.getElementById("edit_collection_exempted_category").setAttribute("hidden", true);
  }
}

function setVoidTicketModal(ackID) {
  document.getElementById("void_ticket_input").value = ackID;
}