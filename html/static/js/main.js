function formatSueldo(input) {
    // Eliminar comas existentes y dar formato al sueldo
    let sueldo = input.value.replace(/,/g, '');
    sueldo = Number(sueldo).toLocaleString();
    input.value = sueldo;
}
// Función para obtener los productos seleccionados y redirigir a la página de actualización
document.getElementById('btnActualizar').addEventListener('click', function () {
    var checkboxes = document.querySelectorAll('input[name="seleccionados[]"]:checked');
    var productosSeleccionados = Array.from(checkboxes).map(checkbox => checkbox.value);

    // Obtener la URL de actualización desde el atributo de datos
    var url = document.getElementById('btnActualizar').getAttribute('data-url');

    // Crear un formulario dinámicamente
    var form = document.createElement('form');
    form.setAttribute('method', 'post');
    form.setAttribute('action', url);
    form.style.display = 'none';

    // Crear un input para enviar la lista de productos seleccionados
    var input = document.createElement('input');
    input.setAttribute('type', 'hidden');
    input.setAttribute('name', 'productos');
    input.setAttribute('value', productosSeleccionados.join(','));
    form.appendChild(input);

    // Agregar el formulario al cuerpo del documento
    document.body.appendChild(form);

    // Enviar el formulario
    document.body.appendChild(form).submit();
});

// Función para mostrar el modal de confirmación de eliminación
document.getElementById('btnEliminar').addEventListener('click', function () {
    $('#eliminarModal').modal('show');
});

// Función para obtener los productos seleccionados y redirigir a la página de eliminación
document.getElementById('btnConfirmarEliminar').addEventListener('click', function () {
    var checkboxes = document.querySelectorAll('input[name="seleccionados[]"]:checked');
    var productosSeleccionados = Array.from(checkboxes).map(checkbox => checkbox.value);

    // Obtener la URL de eliminación desde el atributo de datos
    var url = document.getElementById('btnEliminar').getAttribute('data-url');

    // Redirigir a la página de eliminación con los productos seleccionados
    window.location.href = url + "?productos=" + productosSeleccionados.join(',');
});

function formatCreditCard(input) {
    // Eliminar todos los caracteres que no sean números
    var value = input.value.replace(/\D/g, '');

    // Insertar un guion cada cuatro dígitos
    value = value.replace(/(\d{4})(?=\d)/g, '$1-');

    // Actualizar el valor del campo de entrada
    input.value = value;
}

function formatExpirationDate(input) {
    // Eliminar todos los caracteres que no sean números
    var value = input.value.replace(/\D/g, '');

    // Insertar una barra después de los dos primeros dígitos (mes)
    if (value.length > 2) {
        value = value.slice(0, 2) + '/' + value.slice(2);
    }

    // Actualizar el valor del campo de entrada
    input.value = value;
}

// Script para cambiar entre pestañas
var reportTabs = new bootstrap.Tab(document.getElementById('masVendidosTab'));

// Cambia a la pestaña de Más Vendidos por defecto
reportTabs.show();

// Función para cambiar a la pestaña de Menos Vendidos
function mostrarMenosVendidos() {
    var menosVendidosTab = new bootstrap.Tab(document.getElementById('menosVendidosTab'));
    menosVendidosTab.show();
}

// Función para cambiar a la pestaña de Más Vendidos
function mostrarMasVendidos() {
    var masVendidosTab = new bootstrap.Tab(document.getElementById('masVendidosTab'));
    masVendidosTab.show();
}

function mostrarVentasPorDia(){
    var ventasPorDiaTab = new bootstrap.Tab(document.getElementById('ventasPorDiaTab'));
    ventasPorDiaTab.show();
}

// Función para cambiar a la pestaña de Clientes Más Compradores
function mostrarClientesMasCompradores() {
    var clientesMasCompradoresTab = new bootstrap.Tab(document.getElementById('clientesMasCompradoresTab'));
    clientesMasCompradoresTab.show();
}

// Escucha el evento de clic en el botón o enlace para mostrar Menos Vendidos
document.getElementById('mostrarMenosVendidosBtn').addEventListener('click', function() {
    mostrarMenosVendidos();
});

// Escucha el evento de clic en el botón o enlace para mostrar Más Vendidos
document.getElementById('mostrarMasVendidosBtn').addEventListener('click', function() {
    mostrarMasVendidos();
});

document.getElementById('mostrarVentasPorDiaBtn').addEventListener('click', function() {
    mostrarVentasPorDias();
});

// Escucha el evento de clic en el botón o enlace para mostrar Clientes Más Compradores
document.getElementById('mostrarClientesMasCompradoresBtn').addEventListener('click', function() {
    mostrarClientesMasCompradores();
});

function validarContraseña() {
    var contraseña = document.getElementById('contrasena').value;
    var requisitos = /^(?=.*\d)(?=.*[a-z])(?=.*[A-Z]).{8,}$/;
    if (!requisitos.test(contraseña)) {
        document.getElementById('requisitos-contraseña').style.display = 'block';
        alert('La contraseña no cumple con los requisitos.');
        return false;
    }
    return true;
    }
