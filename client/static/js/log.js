var log = function(mensagem, classe) {
    // Classes: normal, error, warning 
    classe = classe || 'normal'
    $('#log').append('<p class="log-'+classe+'"> &gt; '+mensagem+"</p>");
    
    var objDiv = document.getElementById("log");
    objDiv.scrollTop = objDiv.scrollHeight;
}
