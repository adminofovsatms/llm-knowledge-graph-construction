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
  
      console.log("Fetched Data:", data);  // DEBUG LINE
  
      const { nodes, edges } = data;
  
      cy.elements().remove();         // Clear previous data
      cy.add([...nodes, ...edges]);  // Add new data
      cy.layout({ name: 'preset' }).run();
    } catch (err) {
      console.error("Failed to load data:", err);
    }
  }    