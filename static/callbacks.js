let socket = io();
let settings = {};

function myLoad(event)
{
    if (window.localStorage) {
        var t0 = Number(window.localStorage['myUnloadEventFlag']);
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
        window.localStorage['myUnloadEventFlag']=new Date().getTime();
    }

    // notify the server that we want to disconnect the user in a few seconds (I used 5 seconds)
    askServerToDisconnectUserInAFewSeconds(); // synchronous AJAX call
}


function set_meter_icon(meter)
{
  let icon = "/static/" + meter + ".svg";
  document.getElementById("measure_length_display").src = icon;
}

function send_updates()
{
  settings["tempo"     ] = parseInt(document.getElementById("tempo_output").value);
  settings["beats"     ] = parseInt(document.getElementById("measure_length").value);
  settings["measure"   ] = parseInt(document.getElementById("measure_volume").value);
  settings["beat"      ] = parseInt(document.getElementById("beat_volume").value);
  settings["eighths"   ] = parseInt(document.getElementById("eighth_volume").value);
  settings["swing"     ] = parseInt(document.getElementById("swing_value").value);
  settings["sixteenths"] = parseInt(document.getElementById("sixteenth_volume").value);
  socket.emit("push_params", settings);
}

function update_tempo_drag()
{
  let tempo_val = document.getElementById("tempo_slider").value.padEnd(3);
  document.getElementById("tempo_output").value = document.getElementById("tempo_slider").value;
  send_updates();
}

function meter_clicked(button_id)
{
  socket.emit('log', 'clicked meter button: %s' % (event.target));
  let meters = document.getElementById("measure_options").value.split(",").map(Number);
  let current_meter = parseInt(document.getElementById("measure_length").value);
  let meter_idx = meters.indexOf(current_meter);

  if (button_id == "meter_up" && (meter_idx < meters.length - 1))
  {
    meter_idx += 1;
  } else if (button_id == "meter_down" && meter_idx > 0)
  {
      meter_idx -= 1;
  }
  document.getElementById("measure_length").value = meters[meter_idx];
  set_meter_icon(meters[meter_idx]);
  send_updates();
}

function popup_menu(){
    document.getElementById("config.dropbtn").classList.toggle("show");
}

// Close the dropdown menu if the user clicks outside of it
window.onclick = function(event) {
  if (!event.target.matches('.dropbtn')) {
    socket.emit('log', 'click outside: %s' % (event.target));
    var dropdowns = document.getElementsByClassName("dropdown-content");
    var i;
    for (i = 0; i < dropdowns.length; i++) {
      var openDropdown = dropdowns[i];
      if (openDropdown.classList.contains('show')) {
        openDropdown.classList.remove('show');
      }
    }
  }
}
