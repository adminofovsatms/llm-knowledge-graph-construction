const cy = cytoscape({
  container: document.getElementById('cy'),
  elements: [],
  style: [
    {
      selector: 'node',
      style: {
        'label': 'data(label)',
        'background-color': 'data(color)',
        'width': 30,
        'height': 30,
        'text-valign': 'center',
        'color': '#000',
        'font-size': 8,
        'text-wrap': 'wrap',
        'text-halign': 'center'
      }
    },
    {
      selector: 'edge',
      style: {
        'width': 2,
        'line-color': '#888',
        'target-arrow-shape': 'triangle',
        'target-arrow-color': '#888'
      }
    }
  ],
  layout: {
    name: 'preset'
  }
});

function initTimeline(timeline) {
  const timelineComponents = {};
  timelineComponents['timelineWrapper'] = timeline.querySelector('.events-wrapper');
  timelineComponents['eventsWrapper'] = timelineComponents['timelineWrapper'].querySelector('.events');
  timelineComponents['fillingLine'] = timelineComponents['eventsWrapper'].querySelector('.filling-line');
  timelineComponents['timelineEvents'] = Array.from(timelineComponents['eventsWrapper'].querySelectorAll('a'));
  timelineComponents['timelineDates'] = parseDate(timelineComponents['timelineEvents']);
  timelineComponents['eventsMinLapse'] = 1;
  timelineComponents['timelineNavigation'] = timeline.querySelector('.cd-timeline-navigation');

  setDatePosition(timelineComponents);
  const timelineTotWidth = setTimelineWidth(timelineComponents);
  const wrapperWidth = parseFloat(window.getComputedStyle(timelineComponents['timelineWrapper']).width);

  // Hide navigation if all events fit
  const totalEventsWidth = timelineComponents['timelineEvents'].length * 30; // Node width is 30px
  const totalSpacing = (timelineComponents['timelineEvents'].length + 1) * 40; // Spacing between and around nodes
  if (totalEventsWidth + totalSpacing <= wrapperWidth) {
    timelineComponents['timelineNavigation'].style.display = 'none';
  } else {
    timelineComponents['timelineNavigation'].style.display = 'flex';
  }
  timeline.classList.add('loaded');

  timelineComponents['timelineNavigation'].querySelector('.next').addEventListener('click', (event) => {
    event.preventDefault();
    updateSlide(timelineComponents, timelineTotWidth, 'next');
  });
  timelineComponents['timelineNavigation'].querySelector('.prev').addEventListener('click', (event) => {
    event.preventDefault();
    updateSlide(timelineComponents, timelineTotWidth, 'prev');
  });
  timelineComponents['eventsWrapper'].addEventListener('click', (event) => {
    const target = event.target.closest('a');
    if (target && target.tagName === 'A') {
      event.preventDefault();
      timelineComponents['timelineEvents'].forEach(a => a.classList.remove('selected'));
      target.classList.add('selected');
      updateFilling(target, timelineComponents['fillingLine'], timelineTotWidth);
      const date = target.textContent;
      loadData(date);
    }
  });
}

function updateSlide(timelineComponents, timelineTotWidth, string) {
  const translateValue = getTranslateValue(timelineComponents['eventsWrapper']);
  const wrapperWidth = parseFloat(window.getComputedStyle(timelineComponents['timelineWrapper']).width);
  if (string === 'next') {
    translateTimeline(timelineComponents, translateValue - wrapperWidth + 40, wrapperWidth - timelineTotWidth);
  } else {
    translateTimeline(timelineComponents, translateValue + wrapperWidth - 40);
  }
}

function translateTimeline(timelineComponents, value, totWidth) {
  const eventsWrapper = timelineComponents['eventsWrapper'];
  value = (value > 0) ? 0 : value;
  value = (typeof totWidth !== 'undefined' && value < totWidth) ? totWidth : value;
  setTransformValue(eventsWrapper, 'translateX', value + 'px');
  const prev = timelineComponents['timelineNavigation'].querySelector('.prev');
  const next = timelineComponents['timelineNavigation'].querySelector('.next');
  if (value === 0) prev.classList.add('inactive');
  else prev.classList.remove('inactive');
  if (value === totWidth) next.classList.add('inactive');
  else next.classList.remove('inactive');
}

function updateFilling(selectedEvent, filling, totWidth) {
  const eventStyle = window.getComputedStyle(selectedEvent);
  const eventLeft = parseFloat(eventStyle.getPropertyValue("left"));
  const scaleValue = eventLeft / totWidth; // Scale to left edge of node
  setTransformValue(filling, 'scaleX', scaleValue);
}

function setDatePosition(timelineComponents) {
  const totalEvents = timelineComponents['timelineEvents'].length;
  const containerWidth = parseFloat(window.getComputedStyle(timelineComponents['timelineWrapper']).width);
  const nodeWidth = 30; // Fixed node width from CSS
  const totalNodesWidth = totalEvents * nodeWidth;
  const totalSpacing = containerWidth - totalNodesWidth;
  const spacing = totalSpacing / (totalEvents + 1); // Equal spacing before, between, and after

  for (let i = 0; i < totalEvents; i++) {
    const position = spacing * (i + 1) + nodeWidth * i;
    timelineComponents['timelineEvents'][i].style.left = position + 'px';
  }
}

function setTimelineWidth(timelineComponents) {
  const totalEvents = timelineComponents['timelineEvents'].length;
  const containerWidth = parseFloat(window.getComputedStyle(timelineComponents['timelineWrapper']).width);
  const totalWidth = containerWidth; // Match container width
  timelineComponents['eventsWrapper'].style.width = totalWidth + 'px';
  updateFilling(timelineComponents['timelineEvents'][0], timelineComponents['fillingLine'], totalWidth);
  return totalWidth;
}

function getTranslateValue(timeline) {
  const timelineStyle = window.getComputedStyle(timeline);
  const timelineTranslate = timelineStyle.getPropertyValue("-webkit-transform") ||
    timelineStyle.getPropertyValue("-moz-transform") ||
    timelineStyle.getPropertyValue("-ms-transform") ||
    timelineStyle.getPropertyValue("-o-transform") ||
    timelineStyle.getPropertyValue("transform");
  if (timelineTranslate.indexOf('(') >= 0) {
    const translate = timelineTranslate.split('(')[1].split(')')[0].split(',');
    return parseFloat(translate[4]);
  }
  return 0;
}

function setTransformValue(element, property, value) {
  element.style.transform = `${property}(${value})`;
  element.style.webkitTransform = `${property}(${value})`;
  element.style.mozTransform = `${property}(${value})`;
  element.style.msTransform = `${property}(${value})`;
  element.style.oTransform = `${property}(${value})`;
}

function parseDate(events) {
  const dateArrays = [];
  events.forEach(event => {
    const newDate = new Date(event.getAttribute('data-date'));
    dateArrays.push(newDate);
  });
  return dateArrays;
}

function daydiff(first, second) {
  return Math.round((second - first) / (1000 * 60 * 60 * 24));
}

function minLapse(dates) {
  const dateDistances = [];
  for (let i = 1; i < dates.length; i++) {
    const distance = daydiff(dates[i - 1], dates[i]);
    dateDistances.push(distance);
  }
  return Math.min.apply(null, dateDistances);
}

async function loadData(date) {
  try {
    const figureRes = await fetch(`/api/stick-figure?t=${date}`);
    const { nodes, edges } = await figureRes.json();
    cy.elements().remove();
    cy.add([...nodes, ...edges]);
    cy.layout({ name: 'preset' }).run();
    document.getElementById('injury-details').innerText = "Click a body part to see injury details.";
    cy.off('tap');
    cy.on('tap', 'node', async function (evt) {
      const node = evt.target;
      const label = node.data('label');
      const color = node.data('color');
      if (color === "red" && date) {
        const cacheKey = `injuryStory_${date}_${label}`;
        const cachedStory = sessionStorage.getItem(cacheKey);
        if (cachedStory) {
          console.log(`Cache hit for ${cacheKey}`);
          document.getElementById('injury-details').innerHTML = `
            <h3>${label} - Injury Story (${date})</h3>
            <p style="white-space: pre-wrap;">${cachedStory}</p>
          `;
        } else {
          console.log(`Cache miss for ${cacheKey}, fetching from API`);
          document.getElementById('injury-details').innerHTML = `<p>Loading injury story for ${label}...</p>`;
          try {
            const res = await fetch(`/api/injury-story?t=${date}`);
            const data = await res.json();
            if (data.story) {
              try {
                sessionStorage.setItem(cacheKey, data.story);
                console.log(`Stored story in sessionStorage for ${cacheKey}`);
              } catch (e) {
                console.error('Failed to store in sessionStorage:', e);
              }
              document.getElementById('injury-details').innerHTML = `
                <h3>${label} - Injury Story (${date})</h3>
                <p style="white-space: pre-wrap;">${data.story}</p>
              `;
            } else {
              document.getElementById('injury-details').innerText = `No story found for ${label}.`;
            }
          } catch (err) {
            console.error("Error loading story:", err);
            document.getElementById('injury-details').innerText = "Failed to load injury story.";
          }
        }
      } else {
        const injury = node.data('injury');
        document.getElementById('injury-details').innerHTML = `
          <h3>${label}</h3>
          <p>${injury || "No known injury for this body part."}</p>
        `;
      }
    });
  } catch (err) {
    console.error("Failed to load data:", err);
    document.getElementById('injury-details').innerText = "Error fetching stick figure data.";
  }
}

document.addEventListener('DOMContentLoaded', async () => {
  const res = await fetch("/api/timeline");
  const dates = await res.json();
  const timeline = document.getElementById("timeline");
  dates.forEach((date) => {
    const li = document.createElement("li");
    const a = document.createElement("a");
    a.href = "#0";
    a.setAttribute("data-date", `01/01/${date}`);
    a.textContent = date;
    li.appendChild(a);
    timeline.appendChild(li);
  });

  const timelineElement = document.querySelector('.cd-horizontal-timeline');
  initTimeline(timelineElement);
  if (dates.length) {
    loadData(dates[0]);
    timeline.querySelector('a').classList.add('selected');
  }
});