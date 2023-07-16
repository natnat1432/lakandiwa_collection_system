
function setEditSubsidyModal(member_id, subsidy_id, start_date, end_date,subsidy_value, role){
    select = document.getElementById('edit_member_id'); 
    document.getElementById('edit_subsidy_id').value = subsidy_id;
    document.getElementById('edit_start_date').value = start_date;
    document.getElementById('edit_end_date').value = end_date;
    document.getElementById('edit_subsidy_value').value = subsidy_value;

    select_role = document.getElementById('edit_role');

    for(i=0;i<select.options.length; i++)
    {
        var option = select.options[i];

        if(option.value === member_id)
        {
            option.selected = true;
            break;
        }
    }

    for(j=0;j<select_role.options.length;j++)
    {
        var edit_option = select_role.options[j];

        if(edit_option.value == role)
        {
            edit_option.selected = true;
            break;
        }
    }
    
    }

    
function convertTime(date_value) {
    let hour = parseInt(date_value.substring(10, 13));
    let ind = "";
    if ((hour - 12) < 0) {
        ind = "AM";
    } else {
        ind = "PM";
    }

    let f_hour = hour % 12;
    let w_hour = "";

    if (f_hour < 10) {
        w_hour = "0" + f_hour.toString();
    } else {
        w_hour = f_hour.toString();
    }
    if(f_hour == 0)
    {
        w_hour = "12"
    }

    return w_hour + date_value.substring(13, 16) + ind;
}

function setDeleteSubsidyModal(id, firstname, lastname, start_date, end_date) {
    document.getElementById('delete_name').innerHTML = lastname + ", " + firstname;
    document.getElementById('date_range').innerHTML = start_date.substring(0, 10) + " from " + convertTime(start_date) + " to " + convertTime(end_date);
    document.getElementById('delete_id').value = id;
}

function deleteSubsidy(){
    let id = document.getElementById('delete_id').value;
    location.href="/deletesubsidy/"+id;
}

function setSignModal(subsidy_id)
{
    document.getElementById("subsidy_id_input").value = subsidy_id;
}

function signSubsidy()
{
    var subsidy_id  = document.getElementById("subsidy_id_input").value;

    window.location.href = `/signsubsidy/${subsidy_id}`;
}