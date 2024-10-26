// src="url_for('static', filename='ruta/del/archivo')"
console.log('Hola mundo!');

async function main(){
    await setDatos();
}

async function setDatos() {
    const url=window.location.href.replace('menu','');
    const res= await fetch(url+'playlists')
    const data= await res.json();
    const columnas=['name', 'description','public','collaborative','images','tracks'];
    data['items'].forEach(element => {

        const row=document.createElement('tr');
        columnas.forEach(col => {
            const td=document.createElement('td');
            if (col=='images'){
                const img=document.createElement('img');
                img.src=element[col][0]['url'];
                img.width=100;
                img.height=100;
                td.appendChild(img);
            }
            else if (col=='tracks'){
                const tracks=element[col]['total'];
                td.textContent=tracks;
            }else{
                td.textContent=element[col];
            }
            row.appendChild(td);

        });

        const td=document.createElement('td');
        const button=document.createElement('button');
        button.textContent='Analizar';
        button.onclick=async function(){
            analizarPlaylist(element['id'], element['tracks']['total']);
        }
        td.appendChild(button);
        row.appendChild(td);
        document.getElementById('bodyPlaylist').appendChild(row);


        document.getElementById('bodyPlaylist').appendChild(document.createElement('tr'));

    });
}
function numeroRandom(min, max) {
    return Math.floor(Math.random() * (max - min + 1)) + min;
}
async function analizarPlaylist(id, total){
    let grafo=[];
    let datosCanciones={};
    let listaNombres=[];    
    let lastSong=-1;
    const graph = new graphlib.Graph();

    alert('Analizando playlist '+id);
    for(i=0;i<total;i++){
        let tmp=[];
        for(j=0;j<total;j++){
            tmp.push(0);
        }
        grafo.push(tmp);
    }
    let cont=0;
    const url=window.location.href.replace('menu','');
    fetch(url+'analizarPlyalist?id='+encodeURIComponent(id)).then(response => {
        const reader = response.body.getReader();
        const decoder = new TextDecoder();

        function getPath(targetNode, shortestPaths) {
            let path = [];
            let currentNode = targetNode;
        
            while (currentNode) {
                path.unshift(currentNode);
                currentNode = shortestPaths[currentNode].predecessor;
            }
        
            return path;
        }
        function processStream({ done, value }) {
            
            if (done) {
                console.log('No more data');
                console.log(grafo)
                document.getElementById('bodyDatos').innerHTML='';
                document.getElementById('table_datos').style.display='none';
                document.getElementById('network').style.display='block';
                /*
                console.log("Nodos:", graph.nodes());
                console.log("Aristas:");
                graph.edges().forEach(edge => {
                    console.log(`${edge.v} --(${graph.edge(edge.v, edge.w)})--> ${edge.w}`);
                });*/
                // Crear vis.DataSet para nodos y aristas
                let nodes = new vis.DataSet(
                    graph.nodes().map(node => ({
                        id: node,
                        label: node,
                        color: '#C4DAD2'  // Color de los nodos por defecto
                    }))
                );
                
                let edges = new vis.DataSet(
                    graph.edges().map(edge => ({
                        from: edge.v,
                        to: edge.w,
                        label: String(graph.edge(edge.v, edge.w)),
                        color: { color: '#FFFFFF' }  // Color de las aristas por defecto
                    }))
                );


                // Función para resaltar el camino en Vis.js
                function highlightPath(pathNodes, duration = 5000) {
                    // Guardar los colores originales de nodos y aristas
                    const originalNodes = pathNodes.map(node => ({
                        id: node,
                        color: nodes.get(node).color || '#C4DAD2'
                    }));
                
                    const originalEdges = [];
                    for (let i = 0; i < pathNodes.length - 1; i++) {
                        const edgeId = edges.get({
                            filter: (item) => item.from === pathNodes[i] && item.to === pathNodes[i + 1]
                        })[0].id;
                        originalEdges.push({
                            id: edgeId,
                            color: { color: '#FFFFFF' }
                        });
                    }
                
                    // Cambiar colores para resaltar
                    const updatedNodes = pathNodes.map(node => ({ id: node, color: '#6CD1AC' }));
                    const updatedEdges = originalEdges.map(edge => ({
                        ...edge,
                        color: { color: '#6CD1AC' }
                    }));
                
                    // Aplicar los cambios
                    nodes.update(updatedNodes);
                    edges.update(updatedEdges);
                
                    // Restaurar colores originales después de 'duration' milisegundos
                    setTimeout(() => {
                        nodes.update(originalNodes);
                        edges.update(originalEdges);
                        network.setData({ nodes, edges });  // Refrescar la visualización
                    }, duration);
                }




                const data = { nodes: nodes, edges: edges };
                const options = {
                    nodes: {
                        color: '#C4DAD2'
                    },
                    edges: {
                        color: '#FFFFFF',
                        width: 2,
                        font: {
                            color: '#000000',
                            size: 12,  // Ajusta el tamaño de la etiqueta si deseas
                            align: 'horizontal'
                        }
                    },
                    physics: {
                        enabled: true
                    }
                };

                // Inicializar Vis.js y renderizar el grafo
                const network = new vis.Network(document.getElementById('network'), data, options);
                network.on('click', function(params) {
                    if (params.nodes.length > 0) {
                        const shortestPaths = graphlib.alg.dijkstra(graph, params.nodes[0]);
                        const popObjetivo=numeroRandom(0,populares.length-1);
                        if(shortestPaths[populares[popObjetivo]]==undefined || shortestPaths[populares[popObjetivo]].distance==Infinity){
                            alert('No se puede llegar a la cancion '+populares[popObjetivo]);
                            return;
                        }
                        alert("Calculando camino de "+params.nodes[0]+" a "+populares[popObjetivo]);
                        const path = getPath(populares[popObjetivo], shortestPaths);
                        showWay(path);
                        // Construir aristas a partir del camino
                        let edges = [];
                        for (let i = 0; i < path.length - 1; i++) {
                            edges.push({ from: path[i], to: path[i + 1] });
                        }

                        //highlightPath(path);


                    }
                });
                function showWay(path) {
                    document.getElementById('netRecomendation').innerHTML = '';
                    document.getElementById('netRecomendation').style.display = 'block';
                    document.getElementById('network').style.width = '50%';
                    
                    // Crear nodos resaltados
                    const updatedNodes = path.map(node => ({ id: node, color: '#6CD1AC', label: node }));
                    
                    // Crear aristas resaltadas a partir del camino
                    const updatedEdges = [];
                    for (let i = 0; i < path.length - 1; i++) {
                        updatedEdges.push({
                            from: path[i],
                            to: path[i + 1],
                            color: { color: '#6CD1AC' },
                            width: 2  // Ajusta el ancho si quieres resaltar más
                        });
                    }
                
                    // Inicializar el nuevo conjunto de datos para el grafo
                    const data = {
                        nodes: new vis.DataSet(updatedNodes),
                        edges: new vis.DataSet(updatedEdges)
                    };
                
                    // Configuración de opciones
                    const options = {
                        nodes: {
                            color: '#C4DAD2'
                        },
                        edges: {
                            color: '#FFFFFF',
                            width: 2,
                            font: {
                                color: '#000000',
                                size: 12,
                                align: 'horizontal'
                            }
                        },
                        physics: {
                            enabled: true
                        }
                    };
                
                    
                    new vis.Network(document.getElementById('netRecomendation'), data, options);
                    setTimeout(() => {
                        document.getElementById('netRecomendation').innerHTML = '';
                        document.getElementById('netRecomendation').style.display = 'none';
                        document.getElementById('network').style.width = '100%';
                    }, 5000);
                }
                
                
                return;

                
            }

            // Decodificar y agregar los datos al HTML
            const chunk = JSON.parse(decoder.decode(value, { stream: true }));
            listaNombres=listaNombres.concat(chunk['songs']);
            datosCanciones = {...datosCanciones, ...chunk['datos']};
            cambiarTabla(datosCanciones);
            for(i=listaNombres.length-1;i>lastSong;i--){
                for(j=i-1;j>-1;j--){
                    const peso=compararCancion(datosCanciones[listaNombres[i]],datosCanciones[listaNombres[j]]);
                    if(peso<40){
                        continue;
                    }
                    graph.setNode(listaNombres[i]);
                    graph.setNode(listaNombres[j]);         
                    graph.setEdge(listaNombres[i], listaNombres[j], peso);
                    graph.setEdge(listaNombres[j], listaNombres[i], peso);

                    grafo[i][j]=peso;
                    grafo[j][i]=peso;
                }
            }
            lastSong=listaNombres.length-1;
            // Seguir leyendo el stream
            return reader.read().then(processStream);
        }
        
        // Comienza a leer el stream
        return reader.read().then(processStream);
    })
    .catch(error => console.error('Error al procesar el stream:', error));

}   
function compararCancion(cancion1, cancion2){
    let similitud=1;
    if(cancion1[0]==cancion2[0]){//NOMBRE
        similitud++;
    }
    if(cancion1[1]==cancion2[1]){//TIPO DE ALBUM
        similitud++;
    }
    if(cancion1[2]==cancion2[2]){//TOTAL DE CANCIONES
        similitud+=2;
    }
    if(cancion1[3]==cancion2[3]){//NOMBRE DEL ALBUM
        similitud*=2;
    }
    if(cancion1[4].split('-')[0]==cancion2[4].split('-')[0]){//AÑO DE LANZAMIENTO
        similitud+=2;
    }
    
    if (cancion1[5].some(name => cancion2[5].includes(name))) {//ARTISTA
        //console.log("Artista 1: "+cancion1[5] + " Artista 2: "+cancion2[5]);
        similitud*=3;

    }
    const segundos=cancion1[6]/60000;
    const segundos2=cancion2[6]/60000;
    if((segundos<segundos2+1 && segundos>segundos2-1) &&(segundos2<1+segundos && segundos2>segundos-1)){
        similitud+=2;//DURACION
        //console.log(cancion1[0] + " "+cancion2[0]);
        //console.log("Primera"+segundos+" Segunda"+segundos2);
    }
    if(cancion1[7]==cancion2[7]){//EXPLICITA
        similitud++;
    }
    if((cancion1[8]<=cancion2[8]+10 && cancion1[8]>=cancion2[8]-10) && (cancion2[8]<=cancion1[8]+10 && cancion1[8]>=cancion2[8]-10)){
        //console.log("Popularidad cumplida")
        similitud++;//POPULARIDAD
    }

    if((cancion1[9]<=cancion2[9]+100000 && cancion1[9]>=cancion2[9]-100000) && (cancion2[9]<=cancion1[9]+100000 && cancion1[9]>=cancion2[9]-100000)){
        similitud++;//RANK EN DEZZER
    }

    if(cancion1[10]!=0 || cancion2[10]!=0){//BPM
        if((cancion1[10]<=cancion2[10]+20 && cancion1[10]>=cancion2[10]-20) && (cancion2[10]<=cancion1[10]+20 && cancion1[10]>=cancion2[10]-20)){
            similitud*=2;
        }
    }

    if(cancion1[10]!=0 || cancion2[10]!=0){//GAIN
        if((cancion1[11]<=cancion2[11]+5 && cancion1[11]>=cancion2[11]-5) && (cancion2[11]<=cancion1[11]+5 && cancion1[11]>=cancion2[11]-5)){
            similitud*=2;
        }
    }
    if(cancion1[12] && cancion2[12]){
        if (cancion1[12].some(name => cancion2[12].includes(name))) {//GENERPS
            similitud*=2;
        }
    }
    return similitud;

}
function cambiarTabla(datos){
    document.getElementById('bodyDatos').innerHTML='';
    document.getElementById('playlists').style.display='none'
    document.getElementById('back').style.display='block'
    document.getElementById('back').addEventListener('click',function(){
        grafo=[];
        datosCanciones={};
        listaNombres=[];
        lastSong=-1;
        document.getElementById('network').style.display='none';
        document.getElementById('bodyDatos').innerHTML='';
        document.getElementById('table_datos').style.display='none';
        document.getElementById('back').style.display='none';
        document.getElementById('playlists').style.display='block';
    });
    document.getElementById('table_datos').style.display='block'

    let cont=1;
    populares=[];
    for (const songTitle in datos) {
        if (datos.hasOwnProperty(songTitle)) {
            const songData = datos[songTitle];
            if(songData[8]>70){
                populares.push(songTitle);
            }
            const row=document.createElement('tr');
            const tdCont=document.createElement('td');
            tdCont.textContent=cont;
            row.appendChild(tdCont);
            for(let i=0;i<13;i++){

                const td=document.createElement('td');
                td.textContent=songData[i];       
                row.appendChild(td);           
    
            }
            cont++;
            document.getElementById('bodyDatos').appendChild(row);

        }
    }
    console.log("Populares");
    console.log(populares);

}
main();

let populares=[];