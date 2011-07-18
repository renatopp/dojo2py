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

//====

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
                send({
                    command    : 'REGISTRY',
                    name       : $("#user-name").val(),
                    email      : $("#user-email").val(),
                    email_hash : $("#user-email-hash").val(),
                    key        : $("#key").val()
                });
            }
            
            socket.onmessage = function(msg) {
                var data = receive(msg.data);

                if (data["command"] == "REGISTRY") {
                    cmd_regitry(data);
                } else if (data["command"] == "CONTENT") {
                    cmd_content(data);
                } else if (data["command"] == "PATCH") {
                    cmd_patch(data);
                } else if (data["command"] == "USERCONNECT") {
                    cmd_user_connect(data);
                } else if (data["command"] == "USERDISCONNECT") {
                    cmd_user_disconnect(data);
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

//====

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
    send({
        command  : 'PATCH',
        doc_name : doc_name,
        patches  : difflib.patch_toText(difflib.patch_make(diff))
    });
}

//====

var send = function(object) {
    msg = JSON.stringify(object);
    socket.send(msg);
}

var receive = function(msg) {
    object = JSON.parse(msg);
    return object;
}

//====

var cmd_regitry = function(data) {
    log("Registration OK");

    for (var i=0; i<pads.names.length; i++) {
        var name = pads.names[i];
        send({
            command  : 'OPENDOCUMENT',
            doc_name : pads.doc_name[name],
        });
    }

    for (var i=0; i<data['users'].length; i++) {
        add_user(data['users'][i]['email'], 
                 data['users'][i]['email_hash'], 
                 data['users'][i]['name']);
    }
}

var cmd_content = function(data) {
    log("Updating with server content");

    name = data['doc_name'];
    pads.editor[name].getSession().setValue(data['content']);
    pads.state[name] = data['content'];
}

var cmd_patch = function(data) {
    log("Applying changes");

    name = doc_names[data['doc_name']];
    var patches = difflib.patch_fromText(data['patches']);
    var text = pads.editor[name].getSession().getValue();
    var new_text = difflib.patch_apply(patches, text)[0];
    pads.editor[name].getSession().setValue(new_text);
    pads.state[name] = new_text;
}

var cmd_user_connect = function(data) {
    log("User "+data["name"]+" connected");

    add_user(data['email'], data['email_hash'], data['name']);
}

var cmd_user_disconnect = function(data) {
    log("User "+data["name"]+" disconnected");

    remove_user(data['email_hash']);
}

//====

var add_user = function(email, email_hash, name) {
    users_online.push(email_hash);
    
    // log("Users online: "+users_online);

    var gravatar = "http://www.gravatar.com/avatar/";
    var html = "<div id='user-"+email_hash+"' class='user'>"
    html += "<img src='"+gravatar+email_hash+"?s=25'>"
    html += "<span class='name'>"+name+"</span>"
    html += "</div>"

    $("#user-bar").append(html);
}

var remove_user = function(email_hash) {
    var i = users_online.indexOf(email_hash);
    users_online.splice(i, i+1);

    // log("Users online: "+users_online);
    
    $("#user-"+email_hash).remove();
}