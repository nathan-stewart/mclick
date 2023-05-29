var socket = io.connect();
var settings = JSON.parse(document.getElementById('settings-data').getAttribute('data'));
let note_selected;
var disconnected = false;
var paused = false;

function auto_refresh() {
    if (disconnected){
        local.reload();
    }
}

setTimeout(auto_refresh, 5000);

socket.on("connect", function() { 
    console.log("connected to server");
    document.getElementById("id_form").style.display="block";
    document.getElementById("disconnect_warning").style.display="none";
});

socket.on("disconnect", function() {
    console.log("disconnected from server");
    document.getElementById("id_form").style.display="none";
    document.getElementById("disconnect_warning").style.display="block";
});

function set_midi_note(event) {
    console.log("clicked icon button: " + event.target.id);
    
    note_selected = event.target.id;
    let value = -1;
    switch (event.target.id) {
        case "disp_ts_num"  :
        case "disp_ts_denom": 
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
            return;
    };

    if (value > 0)
    {
        document.getElementById("note_number").value = value;
        document.getElementById("note_entry_dialog").style.display = "block"
    
    }
}

function note_entry_close(){
    document.getElementById("note_entry_dialog").style.display = "none";

    let value = parseInt(document.getElementById("note_number").value);
    switch (note_selected) {
        case 'disp_ts_num': 
        case 'disp_ts_denom': 
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


function swing_check()
{
    let id_val_swing = document.getElementById("swing_value");
    let id_vol_sixteenth = document.getElementById("sixteenth_volume");    
    let compound = ["6/8","9/8","12/8"].includes(settings.time_signature);

    id_vol_sixteenth.disabled = (id_val_swing.value > 0) && !compound;
    id_val_swing.disabled = (id_vol_sixteenth.value > 0) && !compound;

    let new_swing_icon = compound ? "/static/img/swing-sixteenths.svg" : "/static/img/swing-eighths.svg";
    document.getElementById("icon-swing").setAttribute("src", new_swing_icon);
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

function toggle_pushed(id, state)
{    
    let button_container = document.getElementById(id);
    let button = button_container.querySelector("input.transport_button");
    let svg = button.getAttribute("src");
    let base = svg.replace("-pushed", "");
    base = base.replace(".svg", "");
    button.setAttribute("src", state ? base + "-pushed.svg" : base + ".svg");
}

function on_transport(event)
{
    console.log(event.currentTarget.id);
    let id_play = document.getElementById("id_play");
    switch (event.currentTarget.id) {
        case "id_load": break;
            // pull up folder browser
        case "id_prev_song":break;
        case "id_begin_song": break;
        case "id_play":
            if (paused)
            {
                // was paused - start playing, next button will pause
                socket.emit("transport", "id_play");                
                console.log(id_play.getAttribute("src"));
                id_play.setAttribute("src", "/static/img/pause.svg");
                console.log(id_play.getAttribute("src"));
            }
            else
            {
                // was playing- stop playing, next button will play
                socket.emit("transport", "id_pause");
                console.log(id_play.getAttribute("src"));
                id_play.setAttribute("src", "/static/img/play.svg");
                console.log(id_play.getAttribute("src"));
            }
            paused = !paused;
            return;
            break;
        case "id_next_song": break;
        case "id_repeat":
            settings.repeat = !settings.repeat;
            toggle_pushed(event.currentTarget.id, settings.repeat);
            break;

        case "id_shuffle":
            settings.shuffle = !settings.shuffle;
            toggle_pushed(event.currentTarget.id, settings.shuffle);
            break;
    }
    socket.emit("transport", event.currentTarget.id);
}


function update_tempo_drag(event)
{
    document.getElementById("tempo_output").value = id_val_tempo.value;
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
    document.getElementById("disp_ts_num").textContent = numerator;
    document.getElementById("disp_ts_denom").textContent = denominator;
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

// Client-side JavaScript code
socket.on('open_file_dialog', function() {
    window.location.href = '/file-dialog';
});

function myLoad(event)
{
    // the up/down buttons not the display
    document.getElementById("ts_up").addEventListener("click", meter_clicked);
    document.getElementById("ts_down").addEventListener("click", meter_clicked);

    // The display not the up/down buttons!
    document.getElementById("ts_dbl_click_group").addEventListener("dblclick", set_midi_note);

    document.getElementById("icon-beat").addEventListener("dblclick", set_midi_note);
    document.getElementById("icon-eighth").addEventListener("dblclick", set_midi_note);
    document.getElementById("icon-sixteenth").addEventListener("dblclick", set_midi_note);

    let id_val_tempo  = document.getElementById("tempo_slider");
    id_val_tempo.addEventListener("input", update_tempo_drag);
    id_val_tempo.addEventListener("change", on_change);

    let id_vol_measure  = document.getElementById("measure_volume");
    id_vol_measure.addEventListener("change", on_change);
    id_vol_measure.value = settings.measure.volume;
    
    let id_vol_beat = document.getElementById("beat_volume");
    id_vol_beat.addEventListener("change", on_change);

    let id_vol_eighth = document.getElementById("eighth_volume");
    id_vol_eighth.addEventListener("change", on_change);
    id_vol_eighth.value = settings.eighths.volume;


    let id_val_swing = document.getElementById("swing_value");
    id_val_swing.addEventListener("change", on_change);
    id_val_swing.value = settings.swing;

    let id_vol_sixteenth = document.getElementById("sixteenth_volume");
    id_vol_sixteenth.addEventListener("change", on_change);
    id_vol_sixteenth.value = settings.sixteenths.volume;
    
    document.getElementById("id_load").addEventListener("click", on_transport);
    document.getElementById("id_prev_song").addEventListener("click", on_transport);
    document.getElementById("id_begin_song").addEventListener("click", on_transport);
    document.getElementById("id_play").addEventListener("click", on_transport);
    document.getElementById("id_next_song").addEventListener("click", on_transport);
    document.getElementById("id_repeat").addEventListener("click", on_transport);
    document.getElementById("id_shuffle").addEventListener("click", on_transport);

    id_val_tempo.value = settings.tempo;
    document.getElementById("tempo_output").value = settings.tempo;
    
    id_vol_beat.value = settings.beat.volume;     

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
