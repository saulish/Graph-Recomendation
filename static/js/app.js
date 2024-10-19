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
async function analizarPlaylist(id, total){
    let grafo=[];
    let datosCanciones={};
    let listaNombres=[];    
    let lastSong=-1;
    const graph = new graphlib.Graph({ directed: false });

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
        
        function processStream({ done, value }) {
            if (done) {
                console.log('No more data');
                console.log(grafo)
                document.getElementById('bodyDatos').innerHTML='';
                document.getElementById('table_datos').style.display='none';
                document.getElementById('network').style.display='block';
                console.log("Nodos:", graph.nodes());
                console.log("Aristas:");
                graph.edges().forEach(edge => {
                    console.log(`${edge.v} --(${graph.edge(edge.v, edge.w)})--> ${edge.w}`);
                });
                        // Convertir a formato de Vis.js
                const nodes = graph.nodes().map(node => ({ id: node, label: node }));
                const edges = graph.edges().map(edge => ({
                    from: edge.v,
                    to: edge.w,
                    label: String(graph.edge(edge.v, edge.w))  // Peso de la arista
                }));

                const data = { nodes: new vis.DataSet(nodes), edges: new vis.DataSet(edges) };
                const options = {};

                // Inicializar Vis.js y renderizar el grafo
                const network = new vis.Network(document.getElementById('network'), data, options);
                return;
            }
            
            // Decodificar y agregar los datos al HTML
            const chunk = JSON.parse(decoder.decode(value, { stream: true }));
            listaNombres=listaNombres.concat(chunk['songs']);
            datosCanciones = {...datosCanciones, ...chunk['datos']};
            cambiarTabla(datosCanciones);
            for(i=listaNombres.length-1;i>lastSong;i--){
                for(j=i-1;j>-1;j--){
                    graph.setNode(listaNombres[i]);
                    graph.setNode(listaNombres[j]);
                    const peso=compararCancion(datosCanciones[listaNombres[i]],datosCanciones[listaNombres[j]]);
                    if(peso<40){
                        continue;
                    }
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
    for (const songTitle in datos) {
        if (datos.hasOwnProperty(songTitle)) {
            const songData = datos[songTitle];
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

}
main();

