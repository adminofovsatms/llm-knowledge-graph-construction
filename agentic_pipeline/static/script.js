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
  
  async function loadData(timeline) {
    try {
      const response = await fetch(`http://127.0.0.1:5000/api/stick-figure?t=${timeline}`);
      const data = await response.json();
  
      const { nodes, edges } = data;
  
      cy.elements().remove();         
      cy.add([...nodes, ...edges]);  
      cy.layout({ name: 'preset' }).run();
  
      // Add node click handler
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