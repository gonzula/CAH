window.onload = function () {
    setInterval(checkNotifications, 1000);
    getPoints();
    getStatus();
};

function checkNotifications() {
    var xmlhttp = new XMLHttpRequest();
    var url = "/server_notifications";

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
    var i;
    for (i = 0; i < notifications.length; i++) {
        var note = notifications[i];
        console.log(note);
        var name = note['name'];
        if (name == 'update_points') {
            getPoints();
        }
        if (name == 'update_status') {
            getStatus();
        }
        if (name == 'get_winner') {
            getWinner();
        }
    }
}

function getWinner() {
    var xmlhttp = new XMLHttpRequest();
    var url = "/get_winner";

    xmlhttp.onreadystatechange = function() {
        if (this.readyState == 4 && this.status == 200) {
            var status = JSON.parse(this.responseText);
            parseStatus(status);
        }
    };
    xmlhttp.open("GET", url, true);
    xmlhttp.send();
    setTimeout(getStatus, 10 * 1000);
}

function getStatus() {
    var xmlhttp = new XMLHttpRequest();
    var url = "/get_status";

    xmlhttp.onreadystatechange = function() {
        if (this.readyState == 4 && this.status == 200) {
            var status = JSON.parse(this.responseText);
            parseStatus(status);
        }
    };
    xmlhttp.open("GET", url, true);
    xmlhttp.send();
}

function parseStatus(status) {
    console.log(status);
    var h1 = document.getElementById('h1');
    var h2 = document.getElementById('h2');
    var h3 = document.getElementById('h3');

    if (status['h1']) {
        h1.textContent = status['h1'];
    }
    if (status['h2']) {
        h2.textContent = status['h2'];
    }
    if (status['h3']) {
        h3.textContent = status['h3'];
    }
}

function getPoints() {
    var xmlhttp = new XMLHttpRequest();
    var url = "/all_points";

    xmlhttp.onreadystatechange = function() {
        if (this.readyState == 4 && this.status == 200) {
            table = document.getElementById('points_table');

            while (table.lastChild) {
                table.removeChild(table.lastChild);
            }

            var tr = document.createElement('tr');

            var points = JSON.parse(this.responseText);
            console.log(points);
            var i;
            for (i = 0; i < points.length; i++) {
                player = points[i];
                var td = document.createElement('td');
                var a = document.createElement('a');
                if (player['played']) {
                    td.setAttribute('class', 'played');
                }
                a.setAttribute('href', 'javascript:void(0);');
                a.setAttribute('onclick', 'removePlayer("' + player['token'] + '");');
                var text = (
                    'Jogador: <b>' + player['name'] + '</b><br>' +
                    'Pontos: <b>' + player['points'] + '</b>');
                a.innerHTML = text;
                td.appendChild(a);
                tr.appendChild(td);
            }
            table.appendChild(tr);
        }
    };
    xmlhttp.open("GET", url, true);
    xmlhttp.send();
}

function removePlayer(token) {
    var xmlhttp = new XMLHttpRequest();
    var url = "/remove_player?token=" + token;
    xmlhttp.open("POST", url, true);
    xmlhttp.send();
}
