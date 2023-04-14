var socket = io();
var settings = {};

function set_midi_note(event) {
  socket.emit("log", "clicked icon button: " + event.target.id);
}

function set_meter_icon(meter)
{
  let icon = "/static/img" + meter + ".svg";
  document.getElementById("measure_length_display").src = icon;
  //send_updates();
}

function send_updates()
{
  socket.emit("log: send_updates: " + settings);
  settings.tempo             = parseInt(document.getElementById("tempo_output").value);
  settings.num_beats         = parseInt(document.getElementById("measure_length").value);
  settings.measure.volume    = parseInt(document.getElementById("measure_volume").value);
  settings.beat.volume       = parseInt(document.getElementById("beat_volume").value);
  settings.eighths.volume    = parseInt(document.getElementById("eighth_volume").value);
  settings.swing             = parseInt(document.getElementById("swing_value").value);
  settings.sixteenths.volume = parseInt(document.getElementById("sixteenth_volume").value);
  socket.emit("push_params", settings);
}

socket.on('update', function(data) {
    //socket.emit("log", "update parameters: " + data);
    settings = data;
});

function on_change(event)
{
    socket.emit("log", "on_change")
    //send_updates();
}

function update_tempo_drag(event)
{
  socket.emit("log", "update_tempo_drag")
  let tempo_val = document.getElementById("tempo_slider").value.padEnd(3);
  document.getElementById("tempo_output").value = document.getElementById("tempo_slider").value;
}

function meter_clicked(event)
{
    socket.emit("log", "meter_clicked: " + settings);
    let meters = settings['measure_options'];
    let current_meter = settings.num_beats;
    let meter_idx = meters.indexOf(current_meter);

    if (button_id == "meter_up" && (meter_idx < meters.length - 1))
    {
        meter_idx += 1;
    } else if (button_id == "meter_down" && meter_idx > 0)
    {
        meter_idx -= 1;
    }
    document.getElementById("measure_length").value = parseInt(meters[meter_idx]);
    set_meter_icon(meters[meter_idx]);
}

function popup_menu(){
    document.getElementById("config-dropbtn").classList.toggle("show");
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


function register_icon_callbacks() {
    var icons = ["icon-measure", "icon-beat", "icon-eighth", "icon-sixteenth"];
    for (var i = 0; i < icons.length; i++)
    {
        id = icons[i];
        icon = document.getElementById(id);
        if (icon) {
            icon.addEventListener("click", set_midi_note);
        }
    }
}

function register_slider_callbacks() {
    var sliders = ["tempo_slider", "measure_volume", "beat_volume", "eight_volume", "swing_value", "sixteenth_volume"];
    for (var i = 0; i < sliders.length; i++)
    {
        id = sliders[i];
        slider = document.getElementById(id);
        if (slider) {
            slider.addEventListener("change", on_change);
        }
    }
}

function register_meter_callbacks() {
    var buttons = ["meter_up", "meter_down"];
    for (var i = 0; i < buttons.length; i++)
    {
        id = buttons[i];
        button = document.getElementById(id);
        if (button) {
            button.addEventListener("click", meter_clicked);
        }
    }
}

window.addEventListener("load", myLoad);
tempo_slider = document.getElementById("tempo_slider");
if (tempo_slider) {
    tempo_slider.addEventListener("input", update_tempo_drag);
}

register_icon_callbacks();
register_slider_callbacks();
register_meter_callbacks();

