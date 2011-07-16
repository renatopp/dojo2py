var editor = null;
var timer = $.timer();
var socket = null;

var last_state = "";
var difflib = new diff_match_patch();


var init = function() {
    init_editor();
    init_timer();
    init_sockets();
}

var init_editor = function() {
    editor = ace.edit("dojoeditor");
    var PythonMode = require("ace/mode/python").Mode;
    editor.getSession().setMode(new PythonMode());
    editor.setTheme("ace/theme/monokai");
    // editor.getSession().setValue('trambone juquinha');
    // last_state = 'trambone juquinha';
}

var init_timer = function() {
    timer.set({
        action : update,
        time : 1000
    }).play();
}

var init_sockets = function() {
    if (!("WebSocket" in window)){
        log("Browser doesn't support WebSockets", "error");
        timer.stop();
    } else {
        try {
            socket = new WebSocket("ws://127.0.0.1:8080")

            socket.onopen = function() {
                log('Connection made');
                socket.send("CMD CONTENT");
            }
            
            socket.onmessage = function(msg) {
                var data = msg.data;

                if (data.slice(0, 11) == "CMD CONTENT") {
                    log("Updating with server content");

                    var new_text = data.slice(12);
                    editor.getSession().setValue(new_text);
                    last_state = new_text;
                } else if (data.slice(0, 9) == "CMD PATCH") {
                    log("Applying changes");

                    var patches_text = data.slice(10);
                    var patches = difflib.patch_fromText(patches_text);
                    var text = editor.getSession().getValue();
                    var new_text = difflib.patch_apply(patches, text)[0];
                    editor.getSession().setValue(new_text);
                    last_state = new_text;
                }
            }
            
            socket.onclose = function() {
                log("Connection closed");
            }
        } catch(exception) {
            log("Error when connecting to server", "error");
        }
    }
}

var update = function() {
    var text = editor.getSession().getValue();
    var diff = difflib.diff_main(last_state, text);

    if (diff.length > 1 || (diff.length == 1 && diff[0][0] != 0)) {
        last_state = text;
        sync(diff);
    }
}

var sync = function(diff) {
    log("Sending changes");
    socket.send("CMD PATCH:"+difflib.patch_make(diff));
    // socket.send(JSON.stringify(diff));
}