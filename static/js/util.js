function convertTime(date){
    hour = parseInt(date.substring(10,13));
    ind = ""
    if(hour%12 > 0)
    {
        ind = "PM"
    }
    else{
        ind = "AM"
    }

    f_hour = hour%12
    w_hour = ""
    if(f_hour < 10)
    {
        w_hour = "0" + String.valueOf(f_hour)
    }
    else{
        w_hour = String.valueOf(f_hour)
    }

    return w_hour + " " + ind;
}

// Export the function
export { convertTime };