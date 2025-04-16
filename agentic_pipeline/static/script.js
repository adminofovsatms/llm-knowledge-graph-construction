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

async function loadData(date) {
  try {
    const response = await fetch(`/api/stick-figure?t=${date}`);
    const data = await response.json();

    const { nodes, edges } = data;
    cy.elements().remove();
    cy.add([...nodes, ...edges]);
    cy.layout({ name: 'preset' }).run();

    cy.off('tap');
    cy.on('tap', 'node', function(evt) {
      const node = evt.target;
      const label = node.data('label');
      const injury = node.data('injury');

      document.getElementById('injury-details').innerHTML = `
        <h3>${label}</h3>
        <p>${injury || "No injury information available."}</p>
      `;
    });
  } catch (err) {
    console.error("Failed to load data:", err);
  }
}

document.addEventListener('DOMContentLoaded', async () => {
  const res = await fetch("/api/timeline");
  const dates = await res.json();
  const dateList = document.getElementById("date-list");
  const fillingLine = document.querySelector(".cd-h-timeline__filling-line");
  const prevBtn = document.getElementById("prev-btn");
  const nextBtn = document.getElementById("next-btn");

  let activeIndex = 0;

  // Populate timeline dates
  dates.forEach((date, i) => {
    const li = document.createElement("li");
    const a = document.createElement("a");
    a.href = "#0";
    a.dataset.date = date;
    a.innerText = date;
    a.classList.add("cd-h-timeline__date");
    if (i === 0) a.classList.add("cd-h-timeline__date--selected");

    a.addEventListener("click", () => {
      document.querySelectorAll(".cd-h-timeline__date").forEach(el => el.classList.remove("cd-h-timeline__date--selected"));
      a.classList.add("cd-h-timeline__date--selected");
      activeIndex = i;
      loadData(date);
      updateFillingLine(i, dates.length);
      updateNavVisibility();
    });

    li.appendChild(a);
    dateList.appendChild(li);
  });

  function updateFillingLine(index, total) {
    const percent = (index / (total - 1)) * 100;
    fillingLine.style.width = `${percent}%`;
  }

  function updateNavVisibility() {
    prevBtn.style.display = activeIndex > 0 ? 'inline-block' : 'none';
    nextBtn.style.display = activeIndex < dates.length - 1 ? 'inline-block' : 'none';
  }

  if (dates.length) {
    loadData(dates[0]);
    updateFillingLine(0, dates.length);
    updateNavVisibility();
  }

  prevBtn.addEventListener("click", () => {
    if (activeIndex > 0) {
      activeIndex--;
      document.querySelectorAll(".cd-h-timeline__date")[activeIndex].click();
    }
  });

  nextBtn.addEventListener("click", () => {
    if (activeIndex < dates.length - 1) {
      activeIndex++;
      document.querySelectorAll(".cd-h-timeline__date")[activeIndex].click();
    }
  });
});