// src="url_for('static', filename='ruta/del/archivo')"


async function main(){
    // Redirige al backend para iniciar la autenticación
    window.location.href = '/login';  // O la ruta adecuada

    
    //await iniciarSesion();
    //await getDatos();
}

async function getDatos() {
    let url=window.location.href

    const saludo=await fetch(url+'saludar');
    const mensaje=await saludo.json();
    console.log(mensaje);


    const res= await fetch(url+'getDatos')
    const data= await res.json();
    console.log(data);
}


async function iniciarSesion(){
    let url=window.location.href
    const res= await fetch(url+'login');
    const data= await res.json();
    console.log(data);
}

main();