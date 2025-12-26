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
                endpoint: { type: "Dot", options: { radius: 5 } },
                dragOptions: {
                    cursor: "crosshair"
                },
                connectionOverlays: [
                    { type: "Arrow", options: { location: 1, width: 12, length: 12 } }
                ]
            });

            // // Event listener pour les nouvelles connexions créées par drag & drop
            // instance.bind("connection", function(info) {
            //     console.log("Nouvelle connexion créée:", info.sourceId, "->", info.targetId);

            //     console.info(info);

            //     // Permettre la suppression avec double-clic
            //     info.connection.bind("dblclick", function(conn) {
            //         if (confirm("Supprimer cette connexion ?")) {
            //             instance.deleteConnection(conn);
            //         }
            //     });
            // });

            instance.batch(() => {

                // 1. create boxes with 8 anchors
                const boxElements = container.querySelectorAll(".diagram-box");
                const anchors = [
                    "Top",
                    "TopRight",
                    "Right",
                    "BottomRight",
                    "Bottom",
                    "BottomLeft",
                    "Left",
                    "TopLeft"
                ];

                boxElements.forEach(el => {
                    instance.manage(el, el.id);
                    instance.setDraggable(el, true);

                    anchors.forEach(anchor => {
                        const source = anchor === "Right";

                        const ep = instance.addEndpoint(el, {
                            endpoint: { type: "Dot", options: { radius: 6 } },
                            anchor: anchor,
                            paintStyle: { fill: "#2196F3", stroke: "#1976D2", strokeWidth: 2 },
                            maxConnections: -1,
                            source: true,
                            target: true,
                            connector: { type: "Flowchart", options: { cornerRadius: 5 } },
                            connectorStyle: { stroke: "#2196F3", strokeWidth: 3 },
                            connectionsDetachable: true,
                            reattach: true,
                            connectorOverlays: [
                                { type: "Arrow", options: { location: 1, width: 12, length: 12 } }
                            ]
                        });

                        
                        // // Ajouter un gestionnaire de clic personnalisé sur l'endpoint
                        // ep.bind("click", function(endpoint, event) {
                        //     event.stopPropagation();

                        //     console.log("click");
                            
                        //     // Récupérer toutes les connexions de cet endpoint
                        //     const connections = endpoint.connections;

                        //     console.info(connections);
                            
                        //     if (connections.length === 0) {
                        //         // Aucune connexion, comportement par défaut (créer une nouvelle)
                        //         return;
                        //     }
                            
                        //     // Séparer les connexions entrantes (target) et sortantes (source)
                        //     const incomingConnections = connections.filter(conn => 
                        //         conn.targetId === el.id && conn.target === endpoint.element
                        //     );
                            
                        //     // Priorité 1 : Détacher une connexion entrante (random si plusieurs)
                        //     if (incomingConnections.length > 0) {
                        //         const randomIncoming = incomingConnections[Math.floor(Math.random() * incomingConnections.length)];
                                
                        //         // Détacher et permettre le réattachement
                        //         instance.setSourceEnabled(randomIncoming.source, false);
                        //         setTimeout(() => {
                        //             instance.deleteConnection(randomIncoming);
                        //             // Démarrer une nouvelle connexion depuis la source d'origine
                        //             // (Ceci simule le comportement de réattachement)
                        //         }, 10);
                                
                        //         return;
                        //     }
                            
                        //     // Sinon, laisser jsPlumb gérer la création de connexion
                        // });
                    });

                    // // Validation pour limiter à 1 sortie par endpoint
                    // instance.bind("beforeDrop", function(info) {
                    //     const sourceEndpoint = info.connection.endpoints[0];
                        
                    //     // Compter les connexions sortantes de cet endpoint spécifique
                    //     const outgoingFromThisEndpoint = sourceEndpoint.connections.filter(conn => 
                    //         conn.sourceId === info.sourceId && conn.endpoints[0] === sourceEndpoint
                    //     );
                        
                    //     if (outgoingFromThisEndpoint.length >= 1) {
                    //         alert("Cet endpoint ne peut avoir qu'une seule connexion sortante !");
                    //         return false;
                    //     }
                        
                    //     return true;
                    // });
                });

                // 2. create initial connections
                arrows.forEach(arrow => {
                    const sourceEl = document.getElementById(arrow.source);
                    const targetEl = document.getElementById(arrow.target);

                    if (sourceEl && targetEl) {
                        const conn = instance.connect({
                            source: sourceEl,
                            target: targetEl,
                            anchors: ["AutoDefault", "AutoDefault"], // jsPlumb will choose the best anchors
                            overlays: [
                                { type: "Arrow", options: { location: 1, width: 12, length: 12 } },
                                { type: "Label", options: { label: arrow.label, cssClass: "jtk-overlay" } }
                            ],
                            detachable: true, // Allow removing connections
                            reattach: true, // Allow reattaching after detaching
                            maxConnections: -1,
                            connector: { type: "Flowchart", options: { cornerRadius: 5 } }
                            // events: {
                            //     "click": (params) => {
                            //         console.log("Clic détecté via events object!", params.connection);
                            //     },
                            //     "dblclick": (params) => {
                            //         if (confirm("Supprimer ?")) {
                            //             instance.deleteConnection(params.connection);
                            //         }
                            //     }
                            // }
                        });

                        // Permettre la suppression avec double-clic pour les connexions initiales aussi
                        // if (conn) {
                        //     console.log(conn);
                        //     conn.bind("dblclick", (c) => {
                        //         if (c === conn && confirm("Supprimer cette connexion ?")) {
                        //             instance.deleteConnection(c);
                        //         }
                        //     });
                        // }
                    }
                });

            });

            instance.bind("connection", (info) => {
                const endpoint = info.sourceEndpoint;
                
                // Une fois connecté, cet endpoint ne peut plus être le point de départ 
                // d'une NOUVELLE connexion (évite le conflit au clic)
                instance.setSourceEnabled(endpoint.element, false);
                
                // Optionnel : On peut quand même le laisser être une cible
                // instance.setTargetEnabled(endpoint.element, true);
            });

            instance.bind("connection:detach", (info) => {
                // Quand on supprime le lien, on réautorise le drag depuis cet élément
                instance.setSourceEnabled(info.sourceEndpoint.element, true);
            });

            instance.bind("click", (connection, originalEvent) => {
                console.log("Connexion cliquée : ", connection.id);
            });

            instance.bind("beforeStartDetach", (params) => {
                console.log("beforeStartDetach", params);
                return true;

                const endpoint = params.endpoint;
                // const connection = info.connection;
                
                // // Vérifier si cette connexion a l'endpoint comme TARGET
                // const isTarget = connection.targetId === endpoint.element.id;
                
                // // Toujours autoriser le détachement des connexions entrantes
                // if (isTarget) {
                //     return true;
                // }
                
                // Pour les connexions sortantes, vérifier s'il y a des entrantes
                const incomingConnections = endpoint.connections.filter(conn => 
                    conn.targetId === endpoint.element.id
                );

                console.log(incomingConnections);
                
                // Si pas d'entrantes, autoriser le détachement de la sortante
                if (incomingConnections.length === 0) {
                    return true;
                }
                
                // Sinon, empêcher (priorité aux entrantes)
                alert("Détachez d'abord les connexions entrantes");
                return false;
            });

            instance.bind("beforeDetach", (params) => {
                console.log("beforeDetach", params);
                return true;
            });

            instance.bind("beforeDrag", (params) => {
                console.log("beforeDrag", params);
                
                // console.log(params.endpoint.connections);

                return true;
            });

            instance.bind("beforeDrop", function(info) {
                console.log("beforeDrop", info);

                const new_connection = info.connection;
                const existing_conn = info.dropEndpoint.connections.filter(conn => {
                    conn.id != new_connection.id
                });

                console.log(existing_conn);

                if (existing_conn.length == 0) {
                    console.log("tamere");
                    // instance.setEndpointEnabled(info.dropEndpoint, false);
                    // instance.setSource(info.dropEndpoint.element, false);
                    // info.dropEndpoint.enabled = false;
                }

                console.log(info.dropEndpoint.isSource);

                return true;


                // // Vérifier si une connexion existe déjà entre ces deux éléments
                // const existingConnections = instance.getConnections({
                //     source: info.sourceId,
                //     target: info.targetId
                // });
                
                // if (existingConnections.length > 0) {
                //     console.log("Connexion déjà existante, annulation");
                //     return false; // Annule la création de la nouvelle connexion
                // }
                
                // return true; // Autorise la connexion
            });

            // Fonction pour exporter l'état du diagramme en JSON
            window.exportDiagramState = function() {
                const boxes = [];
                const connections = [];

                // 1. Récupérer toutes les boxes avec leurs positions
                const boxElements = container.querySelectorAll(".diagram-box");
                boxElements.forEach(el => {
                    const rect = el.getBoundingClientRect();
                    const containerRect = container.getBoundingClientRect();

                    boxes.push({
                        id: el.id,
                        label: el.querySelector('h3')?.textContent || '',
                        description: el.querySelector('p')?.textContent || '',
                        x: el.offsetLeft,
                        y: el.offsetTop
                    });
                });

                // 2. Récupérer toutes les connexions
                const allConnections = instance.getConnections();
                allConnections.forEach(conn => {
                    const sourceId = conn.source.id;
                    const targetId = conn.target.id;

                    // Récupérer le label si présent
                    let label = '';
                    const labelOverlay = conn.getOverlay('label');
                    if (labelOverlay) {
                        label = labelOverlay.label || '';
                    }

                    connections.push({
                        source: sourceId,
                        target: targetId,
                        label: label
                    });
                });

                return {
                    boxes: boxes,
                    arrows: connections
                };
            };

            // Fonction pour sauvegarder en base de données
            window.saveDiagramToDB = function(projectId) {
                const diagramState = window.exportDiagramState();

                console.log("État du diagramme à sauvegarder:", diagramState);

                // Envoyer au serveur Django
                fetch(`/diagram/save/${projectId}/`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': getCsrfToken()
                    },
                    body: JSON.stringify(diagramState)
                })
                .then(response => response.json())
                .then(data => {
                    console.log("Sauvegarde réussie:", data);
                    alert("Diagramme sauvegardé avec succès!");
                })
                .catch(error => {
                    console.error("Erreur lors de la sauvegarde:", error);
                    alert("Erreur lors de la sauvegarde du diagramme");
                });
            };

            // Fonction helper pour récupérer le token CSRF
            function getCsrfToken() {
                const name = 'csrftoken';
                let cookieValue = null;
                if (document.cookie && document.cookie !== '') {
                    const cookies = document.cookie.split(';');
                    for (let i = 0; i < cookies.length; i++) {
                        const cookie = cookies[i].trim();
                        if (cookie.substring(0, name.length + 1) === (name + '=')) {
                            cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                            break;
                        }
                    }
                }
                return cookieValue;
            }

        });
    });