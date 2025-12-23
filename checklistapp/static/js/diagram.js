    const arrows = JSON.parse(document.getElementById('arrows-data').textContent);

    window.addEventListener('load', function() {
        const jp = window.jsPlumb || window.jsPlumbBrowserUI;
        
        if (!jp) return;

        jp.ready(() => {
            const container = document.getElementById("diagram-container");
            
            const instance = jp.newInstance({
                container: container,
                connector: { type: "Flowchart", options: { cornerRadius: 5 } },
                paintStyle: { stroke: "#2196F3", strokeWidth: 3 },
                endpoint: { type: "Dot", options: { radius: 5 } }
            });

            // 1. Initialiser TOUTES les box présentes dans le DOM
            // On ne boucle pas sur une variable JS, mais sur les éléments HTML générés par Django
            const boxElements = container.querySelectorAll(".diagram-box");
            
            boxElements.forEach(el => {
                // En v6, manage() est essentiel pour que jsPlumb "voit" l'élément
                instance.manage(el);
                // Activer le drag and drop
                instance.setDraggable(el, true);
            });

            // 2. Créer les connexions basées sur ton tableau 'arrows'
            arrows.forEach(arrow => {
                const sourceEl = document.getElementById(arrow.source);
                const targetEl = document.getElementById(arrow.target);

                if (sourceEl && targetEl) {
                    instance.connect({
                        source: sourceEl,
                        target: targetEl,
                        anchors: ["Right", "Left"],
                        overlays: [
                            { type: "Arrow", options: { location: 1, width: 12, length: 12 } },
                            { type: "Label", options: { label: arrow.label, cssClass: "jtk-overlay" } }
                        ]
                    });
                }
            });
        });
    });