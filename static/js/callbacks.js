var socket = io.connect();
var settings = JSON.parse(document.getElementById('settings-data').getAttribute('data'));
let note_selected;
var disconnected = false;

var id_ts_up;
var id_ts_down;
var id_icon_beat;
var id_icon_eighth;
var id_icon_sixteenth;
var id_val_tempo;
var id_vol_measure;
var id_vol_beat;
var id_vol_eighth;
var id_val_swing;
var id_vol_sixteenth;
var id_disp_tempo;
var id_disp_ts_num;
var id_disp_ts_denom;
var id_disconnect;
var id_dlg_note_number;
var id_note_number;
var id_form;

function auto_refresh() {
    if (disconnected){
        local.reload();
    }
}

setTimeout(auto_refresh, 5000);

socket.on("connect", function() { 
    console.log("connected to server");
    id_form.style.display="block";
    id_disconnect.style.display="none";
});

socket.on("disconnect", function() {
    console.log("disconnected from server");
    id_form.style.display="none";
    id_disconnect.style.display="block";
});

function set_midi_note(event) {
    console.log("clicked icon button: " + event.target.id);
    
    note_selected = event.target.id;
    let value;
    switch (event.target.id) {
        case "ts_edit"  : 
            value = settings.measure.note;
            // should this be time signature dialog? Do both note and TS from a new dialog?
            break;
        case "icon-beat"     :
            value = settings.beat.note; 
            break;
        case "icon-eighth"   : 
            value = settings.eighths.note; 
            break;
        case "icon-sixteenth": 
            value = settings.sixteenths.note; 
            break;
        default:
            console.log("unknown click - id = " + event.target.id);
            id_dlg_note_number.style.display = "none";
            return;
    };

    id_note_number.value = value;
    id_dlg_note_number.style.display = "block"
}

function note_entry_close(){
    id_dlg_note_number.style.display = "none";

    let value = parseInt(id_note_number.value);
    switch (note_selected) {
        case 'id_disp_ts_num': 
        case 'id_disp_ts_denom': 
            settings.measure.note = value;
            break;
        case 'icon-beat':
            settings.beat.note = value;
            break;
        case 'icon-eighth': 
            settings.eighths.note = value; 
            break;
        case 'icon-sixteenth': 
            settings.sixteenths.note = value;
            break;
        default:
            id_dlg_note_number.style.display = "";
            return;
    };
    console.log(settings.measure);
    console.log(settings.beat);
    console.log(settings.eighths);
    console.log(settings.sixteenths);
    socket.emit("update_from_gui", settings);
    note_selected = null;
}

function send_updates()
{
    settings.tempo             = parseInt(id_val_tempo.value)
    settings.measure.volume    = parseInt(id_vol_measure.value);
    settings.beat.volume       = parseInt(id_vol_beat.value);
    settings.eighths.volume    = parseInt(id_vol_eighth.value);
    settings.swing             = parseInt(id_val_swing.value);
    settings.sixteenths.volume = parseInt(id_vol_sixteenth.value);
    socket.emit("update_from_gui", settings);
    console.log("Sent update_from_gui");
}

socket.on('update', function(data) {
    console.log("on_update: begin");
});


function swing_check()
{
    let compound = ["6/8","9/8","12/8"].includes(settings.time_signature);
    id_vol_sixteenth.disabled = (id_val_swing.value > 0) && !compound;
    id_val_swing.disabled = (id_vol_sixteenth.value > 0) && !compound;
}

function on_change(event)
{
    console.log("on_change: " + event.target.id);
    if (["swing_value", "eighth_volume", "sixteenth_volume"].includes(event.target.id))
    {
        swing_check();
    }
    send_updates();
}

function update_tempo_drag(event)
{
    id_disp_tempo.value = id_val_tempo.value;
    // don't send it here - that will happen in on_change
}

function meter_clicked(event)
{
    let button_id = event.target.id;
    let meters = settings.measure_options;
    let current_meter = settings.time_signature;
    let meter_idx = meters.indexOf(current_meter);

    let numerators = [2,3,4,5,6,7,8,9,10,11,12];
    let denominators = [2,4,8];

    if (button_id == "ts_up")
    {
        meter_idx += 1;
    } else if (button_id == "ts_down")
    {
        meter_idx -= 1;
    }
    meter_idx = Math.max(0, Math.min(meter_idx, meters.length - 1));
    settings.time_signature = meters[meter_idx];
    show_meter();
    swing_check();
    send_updates();
}

function show_meter() {
    const zero = 0xe080;
    let numerator = 4;
    let denominator = 4;
    try {
        [n, d]  = settings.time_signature.split('/');
        numerator = parseInt(n);
        denominator = parseInt(d);
    }
    catch {
        console.log("error parsing time signature" + settings.time_signature);
    }

    formatted = "";
    if (numerator > 9) {
        tens = numerator / 10;
        formatted += String.fromCharCode(zero + tens);
    }
    ones = numerator % 10;
    formatted += String.fromCharCode(zero + ones);
    numerator = formatted;

    denominator = String.fromCharCode(zero + parseInt(denominator));
    id_disp_ts_num.textContent = numerator;
    id_disp_ts_denom.textContent = denominator;
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
    // tried to make these const global but not all fields are ready when this loads
    id_ts_up = document.getElementById("ts_up");
    id_ts_down = document.getElementById("ts_down");
    id_icon_beat  = document.getElementById("icon-beat");
    id_icon_eighth = document.getElementById("icon-eighth");
    id_icon_sixteenth = document.getElementById("icon-sixteenth");
    id_val_tempo  = document.getElementById("tempo_slider");
    id_vol_measure  = document.getElementById("measure_volume");
    id_vol_beat = document.getElementById("beat_volume");
    id_vol_eighth = document.getElementById("eighth_volume");
    id_val_swing = document.getElementById("swing_value");
    id_vol_sixteenth = document.getElementById("sixteenth_volume");
    id_disp_tempo = document.getElementById("tempo_output");
    id_disp_ts_num = document.getElementById("disp_ts_num");
    id_disp_ts_denom = document.getElementById("disp_ts_denom");
    id_disconnect = document.getElementById("disconnect_warning");
    id_dlg_note_number = document.getElementById("note_entry_dialog");
    id_note_number = document.getElementById("note_number");
    id_form = document.getElementById("the_form");

    id_ts_up.addEventListener("click", meter_clicked);
    id_ts_down.addEventListener("click", meter_clicked);

    id_icon_beat.addEventListener("click", set_midi_note);
    id_icon_eighth.addEventListener("click", set_midi_note);
    id_icon_sixteenth.addEventListener("click", set_midi_note);
    id_disp_ts_num.addEventListener("click", set_midi_note);
    id_disp_ts_denom.addEventListener("click", set_midi_note);

    id_val_tempo.addEventListener("input", update_tempo_drag);
    id_val_tempo.addEventListener("change", on_change);

    id_vol_measure.addEventListener("change", on_change);
    id_vol_beat.addEventListener("change", on_change);
    id_vol_eighth.addEventListener("change", on_change);
    id_val_swing.addEventListener("change", on_change);
    id_vol_sixteenth.addEventListener("change", on_change);

    id_val_tempo.value = settings.tempo;
    id_disp_tempo.value = settings.tempo;
    id_vol_measure.value = settings.measure.volume;
    id_vol_beat.value = settings.beat.volume; 
    id_vol_eighth.value = settings.eighths.volume;
    id_val_swing.value = settings.swing;
    id_vol_sixteenth.value = settings.sixteenths.volume;

    show_meter();

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
    console.log("callback registration ok");
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
