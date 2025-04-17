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
      const year = document.querySelector(".swiper-slide-active .timestamp span")?.innerText;

      if (color === "red" && year) {
        document.getElementById('injury-details').innerHTML = `<p>Loading injury story for ${label}...</p>`;
        try {
          const res = await fetch(`/api/injury-story?t=${year}`);
          const data = await res.json();
          if (data.story) {
            document.getElementById('injury-details').innerHTML = `
              <h3>${label} - Injury Story (${year})</h3>
              <p style="white-space: pre-wrap;">${data.story}</p>
            `;
          } else {
            document.getElementById('injury-details').innerText = `No story found for ${label}.`;
          }
        } catch (err) {
          console.error("Error loading story:", err);
          document.getElementById('injury-details').innerText = "Failed to load injury story.";
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

  // Populate timeline dynamically
  dates.forEach((date) => {
    const slide = document.createElement("div");
    slide.classList.add("swiper-slide");
    slide.innerHTML = `
      <div class="timestamp">
        <span>${date}</span>
      </div>
      <div class="status">
        <span>${date}</span>
      </div>
    `;
    timeline.appendChild(slide);
  });

  // Initialize Swiper without pagination
  const swiper = new Swiper('.swiper-container', {
    slidesPerView: 3,
    centeredSlides: true,
    spaceBetween: 30,
    grabCursor: true,
    on: {
      slideChange: () => {
        const activeSlide = document.querySelector(".swiper-slide-active .timestamp span");
        if (activeSlide) {
          const date = activeSlide.innerText;
          loadData(date);
        }
      }
    }
  });

  // Load initial data
  if (dates.length) {
    loadData(dates[0]);
    swiper.slideTo(0, 0); // Ensure first slide is active
  }
});