// VARIABLES GLOBALES
var subscriberLogo = 'Abanca/pepperTalk/logo';

var subscriberPreguntaSiNo = 'Abanca/pepperTalk/preguntaSiONo';
var respuestaSi = 'Abanca/pepperTalk/respuestaSi';
var respuestaNo = 'Abanca/pepperTalk/respuestaNo';

var subscriberSelfieOEdificio = 'Abanca/pepperTalk/preguntaSelfieOEdificio';
var respuestaEdificio = 'Abanca/pepperTalk/respuestaSelfie';
var respuestaSelfie = 'Abanca/pepperTalk/respuestaEdificio';

var subscriberCharlaOEdificio = 'Abanca/pepperTalk/preguntaCharlaOselfie';
var respuestaCharla = 'Abanca/pepperTalk/respuestaCharla';
var respuestaMostrarEdificio = 'Abanca/pepperTalk/respuestaSelfie';

var subscriberEstilos = 'Abanca/pepperTalk/preguntaEstilos';
var respuestaElegante = 'Abanca/pepperTalk/respuestaElegante';
var respuestaDeportivo = 'Abanca/pepperTalk/respuestaDeportivo';
var respuestaCasual = 'Abanca/pepperTalk/respuestaCasual';

var subscriberOrigen = 'Abanca/pepperTalk/preguntaDondeEres';
var respuestaGalicia = 'Abanca/pepperTalk/respuestaGalicia';
var respuestaOtroOrigen = 'Abanca/pepperTalk/respuestaOtro';

var subscriberAutoestima = 'Abanca/pepperTalk/preguntaAutoestima';
var respuestaBien = 'Abanca/pepperTalk/respuestaBien';
var respuestaMal  = 'Abanca/pepperTalk/respuestaMal';

var subscriberBailarOActividad = 'Abanca/pepperTalk/preguntaBailarOActividad';
var respuestaActividad = 'Abanca/pepperTalk/respuestaActividad';
var respuestaBaile = 'Abanca/pepperTalk/respuestaBailar';

var subscriberRecorridoOServicios = 'Abanca/pepperTalk/preguntaRecorridoOServicios';
var respuestaRecorrido = 'Abanca/pepperTalk/respuestaRecorrido';
var respuestaServicios = 'Abanca/pepperTalk/respuestaServicios';

// CONECTAMOS NAOQUI
session = new QiSession(function (session) 
{
  console.log("connected!");
}, function () {
  console.log("disconnected");
});




// Pasa como argumento la pantalla que se va a mostrar
// 0 - Pantalla Logotipo
// 1 - Pantalla Si No
// 2 - Selfie o Edificio 
function mostrarPantalla (pantalla)
{

	esconderPantallas();

	if(pantalla == 0)
	{
		$('#pantallaLogotipo').fadeIn();
	} 
	else if (pantalla == 1)
	{
		$('#dialogosSiNo').fadeIn();
	}
	else if (pantalla == 2)
	{
		$('#dialogoSelfieOEdificio').fadeIn();
	}
	else if (pantalla == 3)
	{
		$('#dialogoCharlaOEdificio').fadeIn();
	}
	else if (pantalla == 4)
	{
		$('#dialogoEstilo').fadeIn();
	}
	else if (pantalla == 5)
	{
		$('#dialogoOrigen').fadeIn();
	}
	else if (pantalla == 6)
	{
		$('#dialogoAutoestima').fadeIn();
	}
	else if (pantalla == 7)
	{
		$('#dialogoBailarOActividad').fadeIn();
	}
	else if (pantalla == 8)
	{
		$('#dialogoRecorridoOServicios').fadeIn();
	}
	else if (pantalla == 9)
	{
		$('#fotoTwitter').fadeIn();
	}

}

function esconderPantallas() 
{
	$('#pantallaLogotipo').fadeOut();
	$('#dialogosSiNo').fadeOut();
	$('#dialogoSelfieOEdificio').fadeOut();
	$('#dialogoCharlaOEdificio').fadeOut();
	$('#dialogoEstilo').fadeOut();
	$('#dialogoOrigen').fadeOut();
	$('#dialogoAutoestima').fadeOut();
	$('#dialogoBailarOActividad').fadeOut();
	$('#dialogoRecorridoOServicios').fadeOut();
	$('#fotoTwitter').fadeOut();
}













// - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
// - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
// EVENTO QUE MUESTRA EL LOGOTIPO DE ABANCA
// - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
session.service("ALMemory").then(function (ALMemory)
{
	ALMemory.subscriber(subscriberLogo).then(function (subscriber)
	{
    	subscriber.signal.connect(function (value)
    	{
			mostrarPantalla(0);
    	});
	});
});


// - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
// - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
// CUANDO SE LANCE UN EVENTO SI O NO.
// Este tipo de evento, requiere disponer la vista dialogosSiNo.
// Del evento toma la pregunta y muestra los botones si o no.
// - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
// 
session.service("ALMemory").then(function (ALMemory)
{
	ALMemory.subscriber(subscriberPreguntaSiNo).then(function (subscriber)
	{
    	subscriber.signal.connect(function (pregunta)
    	{
    		mostrarPantalla(1);
    		$('#dialogosSiNo .pregunta').text(pregunta);
    	});
	});
});

// PULSAR TABLET EN EVENTO SI O NO. [VALOR SIII]
function respondeSi (){
	session.service("ALMemory").then(function (ALMemory)
	{
		ALMemory.raiseEvent(respuestaSi,1);
	});
}

// PULSAR TABLET EN EVENTO SI O NO. [VALOR NOOO]
function respondeNo (){
	session.service("ALMemory").then(function (ALMemory)
	{
		ALMemory.raiseEvent(respuestaNo,1);
	});
}


// - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
// - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
// PREGUNTA SELFIE O EDIFICIO
// - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
session.service("ALMemory").then(function (ALMemory)
{
	ALMemory.subscriber(subscriberSelfieOEdificio).then(function (subscriber)
	{
    	subscriber.signal.connect(function (pregunta)
    	{
    		mostrarPantalla(2);
    		$('#dialogoSelfieOEdificio .pregunta').text(pregunta);
    	});
	});
});

function respondeSelfie (){
	session.service("ALMemory").then(function (ALMemory)
	{
		ALMemory.raiseEvent(respuestaEdificio,1);
	});
}

function respondeEdificio (){
	session.service("ALMemory").then(function (ALMemory)
	{
		ALMemory.raiseEvent(respuestaSelfie,1);
	});
}

// - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
// - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
// PREGUNTA CHARLA O EDIFICIO
// - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

session.service("ALMemory").then(function (ALMemory)
{
	ALMemory.subscriber(subscriberCharlaOEdificio).then(function (subscriber)
	{
    	subscriber.signal.connect(function (pregunta)
    	{
    		mostrarPantalla(3);
    		$('#dialogoCharlaOEdificio .pregunta').text(pregunta);
    	});
	});
});

function respondeCharla(){
	session.service("ALMemory").then(function (ALMemory)
	{
		ALMemory.raiseEvent(respuestaCharla,1);
	});
}

function respondeMostrarEdificio (){
	session.service("ALMemory").then(function (ALMemory)
	{
		ALMemory.raiseEvent(respuestaMostrarEdificio,1);
	});
}


// - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
// - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
// PREGUNTA ESTILO: DEPORTIVO CASUAL O ELEGANTE
// - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

session.service("ALMemory").then(function (ALMemory)
{
	ALMemory.subscriber(subscriberEstilos).then(function (subscriber)
	{
    	subscriber.signal.connect(function (pregunta)
    	{
    		mostrarPantalla(4);
    		$('#dialogoEstilo .pregunta').text(pregunta);
    	});
	});
});

function respondeElegante(){
	session.service("ALMemory").then(function (ALMemory)
	{
		ALMemory.raiseEvent(respuestaElegante,1);
	});
}

function respondeDeportivo (){
	session.service("ALMemory").then(function (ALMemory)
	{
		ALMemory.raiseEvent(respuestaDeportivo,1);
	});
}

function respondeCasual (){
	session.service("ALMemory").then(function (ALMemory)
	{
		ALMemory.raiseEvent(respuestaCasual,1);
	});
}


// - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
// - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
// PREGUNTA ¿DE DONDE ERES? -- GALLEGO U OTRO.
// - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

session.service("ALMemory").then(function (ALMemory)
{
	ALMemory.subscriber(subscriberOrigen).then(function (subscriber)
	{
    	subscriber.signal.connect(function (pregunta)
    	{
    		mostrarPantalla(5);
    		$('#dialogoOrigen .pregunta').text(pregunta);
    	});
	});
});

function respondeGalicia(){
	session.service("ALMemory").then(function (ALMemory)
	{
		ALMemory.raiseEvent(respuestaGalicia,1);
	});
}

function respondeOtro(){
	session.service("ALMemory").then(function (ALMemory)
	{
		ALMemory.raiseEvent(respuestaOtroOrigen,1);
	});
}


// - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
// - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
// PREGUNTA AUTOESTIMA -- BIEN O MAL
// - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

session.service("ALMemory").then(function (ALMemory)
{
	ALMemory.subscriber(subscriberAutoestima).then(function (subscriber)
	{
    	subscriber.signal.connect(function (pregunta)
    	{
    		mostrarPantalla(6);
    		$('#dialogoAutoestima .pregunta').text(pregunta);
    	});
	});
});

function respondeBien(){
	session.service("ALMemory").then(function (ALMemory)
	{
		ALMemory.raiseEvent(respuestaBien,1);
	});
}

function respondeMal(){
	session.service("ALMemory").then(function (ALMemory)
	{
		ALMemory.raiseEvent(respuestaMal,1);
	});
}


// - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
// - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
// PREGUNTA BAILAR O ACTIVIDAD
// - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

session.service("ALMemory").then(function (ALMemory)
{
	ALMemory.subscriber(subscriberBailarOActividad).then(function (subscriber)
	{
    	subscriber.signal.connect(function (pregunta)
    	{
    		mostrarPantalla(7);
    		$('#dialogoBailarOActividad .pregunta').text(pregunta);
    	});
	});
});


function respondeActividad(){
	session.service("ALMemory").then(function (ALMemory)
	{
		ALMemory.raiseEvent(respuestaActividad,1);
	});
}

function respondeBaile(){
	session.service("ALMemory").then(function (ALMemory)
	{
		ALMemory.raiseEvent(respuestaBaile,1);
	});
}



// - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
// - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
// PREGUNTA RECORRIDO O SERVICIOS
// - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

session.service("ALMemory").then(function (ALMemory)
{
	ALMemory.subscriber(subscriberRecorridoOServicios).then(function (subscriber)
	{
    	subscriber.signal.connect(function (pregunta)
    	{
    		mostrarPantalla(8);
    		$('#dialogoRecorridoOServicios .pregunta').text(pregunta);
    	});
	});
});

function respondeRecorrido(){
	session.service("ALMemory").then(function (ALMemory)
	{
		ALMemory.raiseEvent(respuestaRecorrido,1);
	});
}

function respondeServicios(){
	session.service("ALMemory").then(function (ALMemory)
	{
		ALMemory.raiseEvent(respuestaServicios,1);
	});
}


// - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
// - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
// PREGUNTA GUSTA FOTO
// - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

session.service("ALMemory").then(function (ALMemory)
{
	ALMemory.subscriber('Abanca/pepperSelfie/fotoHecha').then(function (subscriber)
	{
    	subscriber.signal.connect(function (pregunta)
    	{
    		mostrarPantalla(9);
    		$('#fotoTwitter .foto img').attr("src", "images/local-image.jpg?"+Math.floor((Math.random() * 10000000+ 1)));
    	});
	});
});

function respuestaMeGusta(){
	session.service("ALMemory").then(function (ALMemory)
	{
		//ALMemory.raiseEvent(respuestaRecorrido,1);
	});
}

function respuestaNoMeGusta(){
	session.service("ALMemory").then(function (ALMemory)
	{
		//ALMemory.raiseEvent(respuestaServicios,1);
	});
}
