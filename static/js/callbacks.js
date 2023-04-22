var socket = io();
var settings = JSON.parse(document.getElementById('settings-data').getAttribute('data'));
let note_selected;

function set_midi_note(event) {
    console.log("clicked icon button: " + event.target.id);
    dlg = document.getElementById("note_entry_dialog");
    
    note_selected = event.target.id;
    let value;
    switch (event.target.id) {
        case 'icon-measure'  : 
            value = settings.measure.note;
            break;
        case 'icon-beat'     :
            value = settings.beat.note; 
            break;
        case 'icon-eighth'   : 
            value = settings.eighths.note; 
            break;
        case 'icon-sixteenth': 
            value = settings.sixteenths.note; 
            break;
        default:
            dlg.style.display = "none";
            return;
    };

    document.getElementById("note_number").value = value;
    dlg.style.display = "block"
}

function note_entry_close(){
    dlg = document.getElementById("note_entry_dialog");
    dlg.style.display = "none";

    let value;
    switch (note_selected) {
        case 'icon-measure'  : 
            value = settings.measure.note; 
            break;
        case 'icon-beat'     :
            value = settings.beat.note; 
            break;
        case 'icon-eighth'   : 
            value = settings.eighths.note; 
            break;
        case 'icon-sixteenth': 
            value = settings.sixteenths.note; 
            break;
        default:
            dlg.style.display = "";
            return;
    };
    new_val = document.getElementById("note_number").value;
    note_selector_field = new_val;
    console.log(note_selected + " new value = " + note_selector_field);

    socket.emit("update_from_gui", settings);
    note_selected = null;
}

function send_updates()
{
    settings.tempo             = parseInt(document.getElementById("tempo_output").value);
    settings.measure.volume    = parseInt(document.getElementById("measure_volume").value);
    settings.beat.volume       = parseInt(document.getElementById("beat_volume").value);
    settings.eighths.volume    = parseInt(document.getElementById("eighth_volume").value);
    settings.swing             = parseInt(document.getElementById("swing_value").value);
    settings.sixteenths.volume = parseInt(document.getElementById("sixteenth_volume").value);
    socket.emit("update_from_gui", settings);
    console.log("Sent update_from_gui");
}

socket.on('update', function(data) {
    console.log("on_update: begin");
});

function on_change(event)
{
    console.log("on_change: " + event.target.id)
    send_updates();
}

function update_tempo_drag(event)
{
    drag_value = document.getElementById("tempo_slider").value;
    document.getElementById("tempo_output").value = drag_value;
    // don't send it here - that will happen in on_change
}

function meter_clicked(event)
{
    console.log(event.target.id + " clicked: old meter = " +
        document.getElementById("measure_length").src);
    let button_id = event.target.id;
    let meters = settings.measure_options;
    let current_meter = settings.num_beats;
    let meter_idx = meters.indexOf(current_meter);

    if (button_id == "meter_up" && (meter_idx < meters.length - 1))
    {
        meter_idx += 1;
    } else if (button_id == "meter_down" && meter_idx > 0)
    {
        meter_idx -= 1;
    }
    settings.num_beats = parseInt(meters[meter_idx]);
    document.getElementById("measure_length").src = "/static/img/" + settings.num_beats + ".svg";
    console.log(event.target.id + " clicked: New meter = " 
        + document.getElementById("measure_length").src);
}

function popup_menu(){
    console.log("popup_menu: begin");
    document.getElementById("config-dropbtn").classList.toggle("show");
    console.log("popup_menu: end");
}

// Close the dropdown menu if the user clicks outside of it
window.onclick = function(event) {
  if (!event.target.matches(".dropbtn")) {
    var dropdowns = document.getElementsByClassName("dropdown-content");
    var i;
    for (i = 0; i < dropdowns.length; i++) {
      var openDropdown = dropdowns[i];
      if (openDropdown.classList.contains("show")) {
        openDropdown.classList.remove("show");
      }
    }
  }
}

function myLoad(event)
{
    document.getElementById("meter_up").addEventListener("click", meter_clicked);
    document.getElementById("meter_down").addEventListener("click", meter_clicked);

    document.getElementById("icon-measure").addEventListener("click", set_midi_note);
    document.getElementById("icon-beat").addEventListener("click", set_midi_note);
    document.getElementById("icon-eighth").addEventListener("click", set_midi_note);
    document.getElementById("icon-sixteenth").addEventListener("click", set_midi_note);
    
    document.getElementById("tempo_slider").addEventListener("input", update_tempo_drag);

    document.getElementById("tempo_slider").addEventListener("change", on_change);
    document.getElementById("measure_volume").addEventListener("change", on_change);
    document.getElementById("beat_volume").addEventListener("change", on_change);
    document.getElementById("eighth_volume").addEventListener("change", on_change);
    document.getElementById("swing_value").addEventListener("change", on_change);
    document.getElementById("sixteenth_volume").addEventListener("change", on_change);
    
    // update sliders
    document.getElementById("tempo_slider").value = settings.tempo;
    document.getElementById("tempo_output").value = settings.tempo;
    document.getElementById("measure_volume").value = settings.measure.volume;
    document.getElementById("beat_volume").value = settings.beat.volume; 
    document.getElementById("eighth_volume").value = settings.eighths.volume;
    document.getElementById("swing_value").value = settings.swing;
    document.getElementById("sixteenth_volume").value = settings.sixteenths.volume;
    document.getElementById("measure_length").src = "/static/img/" + settings.num_beats + ".svg";


    if (window.localStorage) {
        var t0 = Number(window.localStorage["myUnloadEventFlag"]);
        if (isNaN(t0)) t0=0;
        var t1=new Date().getTime();
        var duration=t1-t0;
        if (duration<5*1000) {
            // less than 5 seconds since the previous Unload event => it's a browser reload (so cancel the disconnection request)
            askServerToCancelDisconnectionRequest(); // asynchronous AJAX call
        }
    }
}

function myUnload(event)
{
    if (window.localStorage) {
        // flag the page as being unloading
        window.localStorage["myUnloadEventFlag"]=new Date().getTime();
    }

    // notify the server that we want to disconnect the user in a few seconds (I used 5 seconds)
    askServerToDisconnectUserInAFewSeconds(); // synchronous AJAX call
}

window.addEventListener("load", myLoad);
