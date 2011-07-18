var timer = $.timer();
var socket = null;
var difflib = new diff_match_patch();

var users_online = [];

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
    add_user($("#user-email").val(), $("#user-email-hash").val(), $("#user-name").val())
    // remove_user($("#user-email-hash").val());
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
            socket = new WebSocket("ws://"+$("#host").val());

            socket.onopen = function() {
                log('Connection made');
                socket.send("CMD REGISTRY:"+$("#user-email").val()+":"+$("#key").val())
            }
            
            socket.onmessage = function(msg) {
                var data = split_command(msg.data);
                var command = data[0];
                var doc_name = data[1];
                var args = data[2];
                var name = doc_names[doc_name];

                if (command == "CMD REGISTRY") {
                    log("Registration OK");
                    for (var i=0; i<pads.names.length; i++) {
                        var name = pads.names[i];
                        socket.send("CMD OPENDOCUMENT:"+pads.doc_name[name]);
                    }
                } else if (command == "CMD CONTENT") {
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
    } else {
        return new Array(msg);
    }

    log("Invalid command from server", "error")
}


//====

var add_user = function(email, email_hash, name) {
    users_online.push(email_hash);

    var gravatar = "http://www.gravatar.com/avatar/";
    var html = "<div id='user-"+email_hash+"' class='user'>"
    html += "<img src='"+gravatar+email_hash+"?s=25'>"
    html += "<span class='name'>"+name+"</span>"
    html += "</div>"

    $("#user-bar").append(html);
}

var remove_user = function(email_hash) {
    users_online.pop(email_hash);
    $("#user-"+email_hash).remove();
    // alert($("#user-renato.ppontes@gmail.com").append("lol"));
}