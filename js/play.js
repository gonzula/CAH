window.onload = function () {
    getCards();
    getPoints();
    setInterval(checkNotifications, 1000);
};

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
        console.log(notifications);
        var note = notifications[i];
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
    }
}

var cardsSelected = 0;

function selectCard(cardId) {
    cardRow = document.getElementById('card_row_' + cardId);

    var pick = parseInt(document.getElementById('pick').innerHTML, 10);

    if (cardsSelected < pick) {
        var xmlhttp = new XMLHttpRequest();
        var url = "/select_card?index=" + cardId;
        xmlhttp.onreadystatechange = function () {
            if (this.readyState == 4 && this.status == 200) {
                var result = JSON.parse(this.responseText);

                if (result == 'ok') {
                    cardsSelected += 1;
                    cardRow.setAttribute('class', 'selected');
                }
            }
        }
        xmlhttp.open("POST", url, true);
        xmlhttp.send();
    }
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
