var timer = $.timer();
var socket = null;
var difflib = new diff_match_patch();

var editor = null;
var last_state = "";

var pads = {
    names: [],
    editor: {},
    state: {},
    doc_name: {},
};

var doc_names = {};


var init = function() {
    init_editor("maineditor", "testeditor");
    init_timer();
    init_sockets();
}

var init_editor = function() {
    var PythonMode = require("ace/mode/python").Mode;

    for (var i=0; i<arguments.length; i++) {
        var name = arguments[i];
        pads.editor[name] = ace.edit(name);
        pads.state[name] = "";
        pads.doc_name[name] = $('#'+name).attr("alt");
        pads.names.push(name);
        doc_names[pads.doc_name[name]] = name;

        pads.editor[name].getSession().setMode(new PythonMode());
        pads.editor[name].setTheme("ace/theme/monokai");
    }
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
                for (var i=0; i<pads.names.length; i++) {
                    var name = pads.names[i];
                    socket.send("CMD OPENDOCUMENT:"+pads.doc_name[name]);
                }
            }
            
            socket.onmessage = function(msg) {
                var data = split_command(msg.data);
                var command = data[0];
                var doc_name = data[1];
                var args = data[2];
                var name = doc_names[doc_name];

                if (command == "CMD CONTENT") {
                    log("Updating with server content");
                    pads.editor[name].getSession().setValue(args);
                    pads.state[name] = args;
                } else if (command == "CMD PATCH") {
                    log("Applying changes");

                    var patches = difflib.patch_fromText(args);
                    var text = pads.editor[name].getSession().getValue();
                    var new_text = difflib.patch_apply(patches, text)[0];
                    pads.editor[name].getSession().setValue(new_text);
                    pads.state[name] = new_text;
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
    for (var i=0; i<pads.names.length; i++) {
        var name = pads.names[i];

        var text = pads.editor[name].getSession().getValue();
        var diff = difflib.diff_main(pads.state[name], text);

        if (diff.length > 1 || (diff.length == 1 && diff[0][0] != 0)) {
            pads.state[name] = text;
            sync(name, diff);
        }
    }
}

var sync = function(editor_name, diff) {
    log("Sending changes of "+editor_name);
    var doc_name = pads.doc_name[editor_name];
    socket.send("CMD PATCH:"+doc_name+":"+difflib.patch_make(diff));
}

var split_command = function(msg) {
    var i = msg.indexOf(":");
    if (i != -1) {
        var command = msg.slice(0, i);
        var j = msg.indexOf(":", i+1);
        if (j != -1) {
            var doc_name = msg.slice(i+1, j);
            var args = msg.slice(j+1);
            return new Array(command, doc_name, args);
        } else {
            var doc_name = msg.slice(i+1);
            return new Array(command, doc_name);
        }
    }

    log("Invalid command from server", "error")
}