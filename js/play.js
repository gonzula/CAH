window.onload = function () {
    getCards();
    getPoints();
    setInterval(checkNotifications, 1000);
};

var receivedNotifications = [];

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
    var i;
    for (i = 0; i < notifications.length; i++) {
        var note = notifications[i];
        var token = note['token'];
        if (arrayContainsElement(receivedNotifications, token)) {
            continue;
        }
        receivedNotifications.push(token);

        var name = note['name'];
        if (name == 'go_to_vote') {
            window.location.replace('/vote');
        }
        if (name == 'refresh') {
            location.reload(true)
        }
        if (name == 'logout') {
            document.cookie = 'token' + '=; expires=Thu, 01 Jan 1970 00:00:01 GMT;';
            location.reload(true)
        }
        if (name == 'update_info') {
            getPoints();
            getCards();
        }

        var xmlhttp = new XMLHttpRequest();
        var url = "/received_notification?token=" + token;
        xmlhttp.open("POST", url, true);
        xmlhttp.send();
    }
}

var isSending = 0;
var selectedCards = [];

function selectCard(cardId) {
    if (arrayContainsElement(selectedCards, cardId)) {
        return;
    }
    if (isSending) {
        return;
    }
    cardRow = document.getElementById('card_row_' + cardId);

    var pick = parseInt(document.getElementById('pick').innerHTML, 10);

    if (selectedCards.length < pick) {
        var xmlhttp = new XMLHttpRequest();
        var url = "/select_card?index=" + cardId;
        xmlhttp.onreadystatechange = function () {
            if (this.readyState == 4) {
                isSending = 0;
            }
            if (this.readyState == 4 && this.status == 200) {
                var result = JSON.parse(this.responseText);

                if (result == 'ok') {
                    selectedCards.push(cardId);
                    cardRow.setAttribute('class', 'selected');
                }
            }
        }
        xmlhttp.open("POST", url, true);
        xmlhttp.send();
        isSending = 1;
    }
}

function clearSelection() {
    if (isSending) {
        return;
    }

    var xmlhttp = new XMLHttpRequest();
    var url = "/clear_selection";
    xmlhttp.onreadystatechange = function () {
        if (this.readyState == 4) {
            isSending = 0;
        }
        if (this.readyState == 4 && this.status == 200) {
            var result = JSON.parse(this.responseText);

            if (result == 'ok') {
                selectedCards = [];
                selectedTables = document.getElementsByClassName('selected');
                var i;
                for (i = 0; selectedTables.length; ) {
                    row = selectedTables[i];
                    row.removeAttribute('class');
                }
            }
        }
    }
    xmlhttp.open("POST", url, true);
    xmlhttp.send();
    isSending = 1;
}


function changeCards() {
    if (isSending) {
        return;
    }

    var xmlhttp = new XMLHttpRequest();
    var url = "/change_cards";
    xmlhttp.onreadystatechange = function () {
        if (this.readyState == 4) {
            isSending = 0;
        }
    }
    xmlhttp.open("POST", url, true);
    xmlhttp.send();
    isSending = 1;
}

function getPoints() {
    var xmlhttp = new XMLHttpRequest();
    var url = "/my_points";

    xmlhttp.onreadystatechange = function() {
        if (this.readyState == 4 && this.status == 200) {
            var points = JSON.parse(this.responseText);
            var span = document.getElementById('points');
            span.innerHTML = points;
        }
    };
    xmlhttp.open("GET", url, true);
    xmlhttp.send();
}

function getCards() {
    var xmlhttp = new XMLHttpRequest();
    var url = "/my_cards";

    xmlhttp.onreadystatechange = function() {
        if (this.readyState == 4 && this.status == 200) {
            var cards = JSON.parse(this.responseText);
            populateCards(cards);
        }
    };
    xmlhttp.open("GET", url, true);
    xmlhttp.send();
}

function populateCards(cards) {
    table = document.getElementById('cards_table');

    while (table.lastChild) {
        table.removeChild(table.lastChild);
    }

    var i;
    for (i = 0; i < cards.length; i++) {
        row = document.createElement('tr');
        row.id = 'card_row_' + i;
        data = document.createElement('td');
        a = document.createElement('a');
        text = document.createTextNode(cards[i]);
        a.setAttribute('onclick', 'selectCard(' + i + ');');
        a.setAttribute('href', 'javascript:void(0);');
        a.appendChild(text);
        data.appendChild(a);
        row.appendChild(data);
        table.appendChild(row);
    }
};
