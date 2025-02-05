// Edit your ics sources here
var username = document.getElementById('calendar').getAttribute('data-username');
var ics_sources = [
    {url: window.location.origin + '/ical/' + username, title: 'custom calendar', event_properties: {color: 'DeepPurple'}}
];

function data_req(url, callback) {
    var req = new XMLHttpRequest();
    req.addEventListener('load', callback);
    req.open('GET', url);
    req.send();
}

function load_ical_events() {
    $('#calendar').fullCalendar('removeEvents');

    var sources_to_load_cnt = ics_sources.length;

    ics_sources.forEach(function(ics, cpt) {
        data_req(ics.url, function() {
            if (this.status === 404) {
                return;
            }
            var events = fc_events(this.response, ics.event_properties);
            $('#calendar').fullCalendar('addEventSource', events);
            sources_to_load_cnt -= 1;
            if (sources_to_load_cnt === 0) {
                add_recur_events();
            }
        });
    });
}

function add_recur_events() {
    $('#calendar').fullCalendar('addEventSource', expand_recur_events);
}

$(document).ready(function() {
    $('#calendar').fullCalendar({
        header: {
            left: 'prev, next today',
            center: 'title',
            right: 'month, agendaWeek, agendaDay'
        },
        defaultView: 'agendaWeek',
        firstDay: '1',
        minTime: "08:00:00",
        maxTime: "19:00:00",
        slotDuration: '00:30:00',
        height: 'auto',
        hiddenDays: [0],
        locale: 'de',
        lang: 'de',
        views: {
            listWeek: { buttonText: 'list week' },
            listMonth: { buttonText: 'list month' }
        },
        navLinks: true,
        editable: false,
        eventLimit: true, // allow "more" link when too many events
        eventRender: function(event, element, view) {
            if (view.name == "listMonth" || view.name == "listWeek") {
                element.find('.fc-list-item-title').append('<div style="margin-top:5px;"></div><span style="font-size: 0.9em">' + (event.description || 'no description') + '</span>' + ((event.loc) ? ('<span style="margin-top:5px;display:     block"><b>Venue: </b>' + event.loc + '</span>') : ' ') + '</div>');
            } else if (view.name == "agendaWeek" || view.name == "agendaDay") {
                if (event.end == null) { event.end = event.start; }
                element.qtip({
                    content: {
                        text: '<small>' + ((event.start.format("d") != event.end.format("d")) ? (event.start.format("MMM Do") +
                            (((event.end.subtract(1, "seconds")).format("d") == event.start.format("d")) ? ' ' : ' - ' +
                                (event.end.subtract(1, "seconds")).format("MMM Do"))) :
                            (event.start == event.end ? event.start.format("MMM Do") : event.start.format("HH:mm") +
                                ' - ' + event.end.format("HH:mm"))) + '</small><br/>' +
                            '<b>' + event.title + '</b>' +
                            ((event.description) ? ('<br/>' + event.description) : ' ') +
                            ((event.loc) ? ('<br/><b>Raum: </b>' + event.loc) : ' ')
                    },
                    style: {
                        classes: 'qtip-bootstrap qtip-rounded qtip-shadown qtip-light',
                    },
                    position: {
                        my: 'center left',
                        at: 'center right',
                    }
                });
            } else {
                if (event.end == null) { event.end = event.start; }
                element.qtip({
                    content: {
                        text: '<small>' + ((event.start.format("d") != event.end.format("d")) ? (event.start.format("MMM Do") +
                            (((event.end.subtract(1, "seconds")).format("d") == event.start.format("d")) ? ' ' : ' - ' +
                                (event.end.subtract(1, "seconds")).format("MMM Do"))) :
                            (event.start == event.end ? event.start.format("MMM Do") : event.start.format("HH:mm") +
                                ' - ' + event.end.format("HH:mm"))) + '</small><br/>' +
                            '<b>' + event.title + '</b>' +
                            ((event.description) ? ('<br/>' + event.description) : ' ') +
                            ((event.loc) ? ('<br/><b>Venue: </b>' + event.loc) : ' ')
                    },
                    style: {
                        classes: 'qtip-bootstrap qtip-rounded qtip-shadown qtip-light',
                    },
                    position: {
                        my: 'top left',
                        at: 'bottom center',
                    }
                });
            }
        }
    });

    load_ical_events();
});
