
function setEditModal(id, firstname, lastname, position){
    document.getElementById('edit_id_number').value = id;
    document.getElementById('edit_firstname').value = firstname;
    document.getElementById('edit_lastname').value = lastname;
    
    select = document.getElementById('edit_position');

    for(i=0;i<select.options.length; i++)
    {
        var option = select.options[i];

        if(option.value === position)
        {
            option.selected = true;
            break;
        }
    }

}

function setDeleteModal(id, firstname, lastname){
    document.getElementById('delete_name').innerHTML = lastname + ", " + firstname;
    document.getElementById('delete_id').value = id;
}

function deleteMember(){
    id = document.getElementById('delete_id').value;

    location.href="/deletemember/"+id;
}

