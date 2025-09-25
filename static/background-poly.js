// Fondo animado low-poly SVG con vértices animados
// Inspirado en https://codepen.io/Yakudoo/pen/PZzpVe

(function() {
    const width = window.innerWidth;
    const height = window.innerHeight;
    const svgNS = "http://www.w3.org/2000/svg";
    const polyW = 120, polyH = 120;
    const cols = Math.ceil(width / polyW) + 2;
    const rows = Math.ceil(height / polyH) + 2;
    const points = [];
    const polygons = [];
    let svg;

    function createSVG() {
        svg = document.createElementNS(svgNS, "svg");
        svg.setAttribute("width", width);
        svg.setAttribute("height", height);
        svg.style.position = "fixed";
        svg.style.left = 0;
        svg.style.top = 0;
        svg.style.width = "100vw";
        svg.style.height = "100vh";
        svg.style.zIndex = 0;
        svg.style.pointerEvents = "none";
        svg.style.transition = "background 1s";
        svg.style.background = "linear-gradient(180deg, #0e2a47 0%, #1e5a8a 100%)";
        document.body.prepend(svg);
    }

    function randomizePoint(x, y) {
        return {
            x: x + (Math.random() - 0.5) * 30,
            y: y + (Math.random() - 0.5) * 30,
            baseX: x,
            baseY: y,
            angle: Math.random() * Math.PI * 2,
            speed: 0.5 + Math.random() * 0.7,
            amplitude: 18 + Math.random() * 18
        };
    }

    function generatePoints() {
        for (let y = 0; y < rows; y++) {
            points[y] = [];
            for (let x = 0; x < cols; x++) {
                points[y][x] = randomizePoint(x * polyW, y * polyH);
            }
        }
    }

    function createPolygons() {
        for (let y = 0; y < rows - 1; y++) {
            for (let x = 0; x < cols - 1; x++) {
                // Triángulo 1
                let poly1 = document.createElementNS(svgNS, "polygon");
                svg.appendChild(poly1);
                polygons.push({
                    el: poly1,
                    indices: [
                        [y, x],
                        [y + 1, x],
                        [y, x + 1]
                    ],
                    color: getPolyColor(y, x)
                });
                // Triángulo 2
                let poly2 = document.createElementNS(svgNS, "polygon");
                svg.appendChild(poly2);
                polygons.push({
                    el: poly2,
                    indices: [
                        [y + 1, x],
                        [y + 1, x + 1],
                        [y, x + 1]
                    ],
                    color: getPolyColor(y, x, true)
                });
            }
        }
    }

    function getPolyColor(y, x, alt) {
        // Gradiente azul con variación
        let base = 40 + Math.floor(30 * Math.random());
        let c = base + y * 2 + (alt ? 10 : 0);
        return `rgb(${c},${c+40},${180 + x*2})`;
    }

    function animate() {
        for (let y = 0; y < rows; y++) {
            for (let x = 0; x < cols; x++) {
                let p = points[y][x];
                p.angle += 0.008 * p.speed;
                p.x = p.baseX + Math.cos(p.angle) * p.amplitude;
                p.y = p.baseY + Math.sin(p.angle) * p.amplitude * 0.7;
            }
        }
        polygons.forEach(poly => {
            let pts = poly.indices.map(([y, x]) => `${points[y][x].x},${points[y][x].y}`);
            poly.el.setAttribute("points", pts.join(" "));
            poly.el.setAttribute("fill", poly.color);
            poly.el.setAttribute("opacity", 0.7);
        });
        requestAnimationFrame(animate);
    }

    function onResize() {
        // Para simplicidad, recarga la página al redimensionar
        window.location.reload();
    }

    // Inicialización
    createSVG();
    generatePoints();
    createPolygons();
    animate();
    window.addEventListener('resize', onResize);
})();
