window.onload = function () {
    setInterval(checkNotifications, 1000);
};

var receivedNotifications = [];

function voteOption(option) {
    console.log('selected option ' + option);
    optionTable = document.getElementById('option_table_' + option);

    selectedTables = document.getElementsByClassName('selected');
    var i;
    for (i = 0; i < selectedTables.length; i++) {
        row = selectedTables[i];
        row.removeAttribute('class');
    }


    var xmlhttp = new XMLHttpRequest();
    var url = "/select_vote?option=" + option;


    xmlhttp.onreadystatechange = function () {
        if (this.readyState == 4 && this.status == 200) {
            var result = JSON.parse(this.responseText);

            if (result == 'ok') {
                optionTable.setAttribute('class', 'selected');
            }
        }
    }

    xmlhttp.open("POST", url, true);
    xmlhttp.send();
}

function checkNotifications() {
    var xmlhttp = new XMLHttpRequest();
    var url = "/player_notifications";

    xmlhttp.onreadystatechange = function() {
        if (this.readyState == 4 && this.status == 200) {
            var notifications = JSON.parse(this.responseText);
            parseNotifications(notifications);
        }
    };
    xmlhttp.open("GET", url, true);
    xmlhttp.send();
}

function parseNotifications(notifications) {
    if (notifications.length > 0) {
        console.log(notifications);
    }
    var i;
    for (i = 0; i < notifications.length; i++) {
        var note = notifications[i];

        var token = note['token'];
        if (arrayContainsElement(receivedNotifications, token)) {
            continue;
        }
        receivedNotifications.push(token);

        var name = note['name'];
        if (name == 'go_to_play') {
            window.location.replace('/play');
        }

        var xmlhttp = new XMLHttpRequest();
        var url = "/received_notification?token=" + token;
        xmlhttp.open("POST", url, true);
        xmlhttp.send();
    }
}
