// Edit your ics sources here
var username = document.getElementById('calendar').getAttribute('data-username');
var ics_sources = [
    {url: 'https://yourical.de/ical/' + username, title: 'custom calendar', event_properties: {color: 'DeepPurple'}}
];


////////////////////////////////////////////////////////////////////////////
//
// Here be dragons!
//
////////////////////////////////////////////////////////////////////////////

function data_req (url, callback) {
    req = new XMLHttpRequest()
    req.addEventListener('load', callback)
    req.open('GET', url)
    req.send()
}

function add_recur_events() {
    if (sources_to_load_cnt < 1) {
        $('#calendar').fullCalendar('addEventSource', expand_recur_events)
    } else {
        setTimeout(add_recur_events, 30)
    }
}

function load_ics(ics, cpt){
    data_req(ics.url, function(){
        $('#calendar').fullCalendar('addEventSource', fc_events(this.response, ics.event_properties))
        sources_to_load_cnt -= 1;
    })
}

function load_events(){
      $('#calendar').fullCalendar('removeEvents');
      // display events
      $('#calendar').fullCalendar({
          header: {
              left: 'prev, next today',
              center: 'title',
              right: 'month, agendaWeek, agendaDay'
          },
          defaultView: 'agendaWeek',
          firstDay: '1',
          locale: 'de',
          lang: 'de',

          // customize the button names,
          // otherwise they'd all just say "list"
          views: {
            listWeek: { buttonText: 'list week' },
            listMonth: { buttonText: 'list month' }
          },
  	navLinks: true,
  	editable: false,
          eventLimit: true, // allow "more" link when too many events
          eventRender: function(event, element, view) {
  	  if(view.name == "listMonth" || view.name == "listWeek") {
              element.find('.fc-list-item-title').append('<div style="margin-top:5px;"></div><span style="font-size: 0.9em">'+(event.description || 'no description')+'</span>'+((event.loc) ? ('<span style="margin-top:5px;display:     block"><b>Venue: </b>'+event.loc+'</span>') : ' ')+'</div>');
  	  } else if(view.name == "agendaWeek" || view.name == "agendaDay") {
              if(event.end == null) { event.end=event.start; }
                element.qtip({
                    content: {
                      text: '<small>'+((event.start.format("d") != event.end.format("d")) ? (event.start.format("MMM Do")
                            +(((event.end.subtract(1,"seconds")).format("d") == event.start.format("d")) ? ' ' : ' - '
                            +(event.end.subtract(1,"seconds")).format("MMM Do"))) :
  			  (event.start == event.end ? event.start.format("MMM Do") : event.start.format("HH:mm")
                            +' - '+event.end.format("HH:mm")))+'</small><br/>'+
  	                   '<b>'+event.title+'</b>'+
  	                  ((event.description) ? ('<br/>'+event.description) : ' ')+
  	                  ((event.loc) ? ('<br/><b>Raum: </b>'+event.loc) : ' ')
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
              if(event.end == null) { event.end=event.start; }
              element.qtip({
                  content: {
                      text: '<small>'+((event.start.format("d") != event.end.format("d")) ? (event.start.format("MMM Do")
                            +(((event.end.subtract(1,"seconds")).format("d") == event.start.format("d")) ? ' ' : ' - '
                            +(event.end.subtract(1,"seconds")).format("MMM Do"))) :
  		          (event.start == event.end ? event.start.format("MMM Do") : event.start.format("HH:mm")
                            +' - '+event.end.format("HH:mm")))+'</small><br/>'+
  		          '<b>'+event.title+'</b>'+
  		          ((event.description) ? ('<br/>'+event.description) : ' ')+
  		          ((event.loc) ? ('<br/><b>Venue: </b>'+event.loc) : ' ')
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
      })
      sources_to_load_cnt = ics_sources.length
      var cpt = 0;
      for (ics of ics_sources) {
          cpt+=1;
          load_ics(ics, cpt)
      }
      add_recur_events()
}

$(document).ready(function() {
  load_events();
});
