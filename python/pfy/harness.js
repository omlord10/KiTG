const fs = require('fs');
const graphPath = process.argv[2], outPath = process.argv[3];
const parsed = JSON.parse(fs.readFileSync(graphPath, 'utf-8'));

const RED = Object.create(GraphRedactor.prototype);
RED.scales = [1]; RED.scale = 1; RED.scaleIndex = 0;
RED.x0 = 0; RED.y0 = 0; RED.width = 1000; RED.height = 1000; RED.offset = 0;
RED.vertices = new VerticesCollection();
RED.edges = []; RED.texts = []; RED.undo = []; RED.activeObject = null;
RED.AddAction = function(){};

for (const v of parsed.vertices)
  RED.vertices.Add(new Vertex(v.x, v.y, v.name, v));

for (const e of parsed.edges) {
  const v1 = RED.vertices.Get(e.vertex1);
  const v2 = RED.vertices.Get(e.vertex2);
  const edge = new Edge(v1, v2, e.weight, e.isDirected, e.controlStep || 0, e);
  if (typeof edge.IsLoop === 'function' && edge.IsLoop() && e.angle != null) edge.angle = e.angle;
  RED.edges.push(edge);
}
for (const t of (parsed.texts || []))
  RED.texts.push(new Text(t.x, t.y, (t.value != null ? t.value : (t.text != null ? t.text : '')), t));

let captured = null;
RED.SaveObject = function(obj){ captured = obj; };
try { RED.SaveSVG(); }
catch (e) { console.error('SaveSVG error:', e.message); console.error(e.stack.split('\n').slice(0,5).join('\n')); process.exit(3); }

(async () => {
  let svg = (captured && typeof captured.text === 'function') ? await captured.text()
          : (typeof captured === 'string' ? captured : String(captured));
  fs.writeFileSync(outPath, svg, 'utf-8');
  console.error('OK svg bytes:', svg.length);
})();
