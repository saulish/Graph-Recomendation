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
            analizarPlaylist(element['id']);
        }
        td.appendChild(button);
        row.appendChild(td);
        document.getElementById('bodyPlaylist').appendChild(row);


        document.getElementById('bodyPlaylist').appendChild(document.createElement('tr'));

    });
}
async function analizarPlaylist(id){
    alert('Analizando playlist '+id);
    const url=window.location.href.replace('menu','');
    await fetch(url+'analizarPlyalist?id='+encodeURIComponent(id))
    .then(response => response.json())
    .then(data => 
        cambiarTabla(data)
    )
    .catch(error => console.error('Error:', error));
}

function cambiarTabla(data){
    document.getElementById('playlists').style.display='none'
    document.getElementById('back').style.display='block'
    document.getElementById('back').addEventListener('click',function(){
        document.getElementById('bodyDatos').innerHTML='';
        document.getElementById('table_datos').style.display='none';
        document.getElementById('back').style.display='none';
        document.getElementById('playlists').style.display='block';
    });
    document.getElementById('table_datos').style.display='block'
    const datos=data['datos'];
    for (const songTitle in datos) {
        if (datos.hasOwnProperty(songTitle)) {
            const songData = datos[songTitle];
            //console.log(songData);
            const row=document.createElement('tr');
            for(let i=0;i<13;i++){
                const td=document.createElement('td');
                if(i==11){
                    console.log(songData[i]);
                }
                td.textContent=songData[i];
            
                row.appendChild(td);
                
    
            }
            document.getElementById('bodyDatos').appendChild(row);

        }
    }

}
main();