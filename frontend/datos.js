const backendUrl = 'http://127.0.0.1:5000';

async function buscarCliente() {
  const dni = document.getElementById('dniInput').value.trim();
  const resultado = document.getElementById('resultado');
  resultado.innerHTML = 'Buscando...';

  try {
    const res = await fetch(`${backendUrl}/buscar_cliente`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ dni })
    });

    if (!res.ok) {
      resultado.innerHTML = '<p class="error">DNI no encontrado en la base de datos.</p>';
      return;
    }

    const data = await res.json();
    resultado.innerHTML = `
      <div class="result">
        <p><strong>Nombre:</strong> ${data.nombre}</p>
        <p><strong>Entidad Financiera:</strong> ${data.entidad_financiera}</p>
        <p><strong>Total Deuda:</strong> S/ ${data.deuda}</p>
        <p><strong>Oferta de Cancelación:</strong> S/ ${data.oferta_cancelacion}</p>
        <p>¿Acepta pagar la oferta?</p>
        <button onclick="aceptarPago('${data.dni}', ${data.oferta_cancelacion})">Aceptar</button>
        <button onclick="noAcepto('${data.dni}', ${data.monto_cancelacion})">No Acepto</button>
        <div id="negociacion"></div>
      </div>
    `;

  } catch (error) {
    resultado.innerHTML = '<p class="error">Error al conectar con el servidor.</p>';
  }
}

async function aceptarPago(dni, monto) {
  const negociacion = document.getElementById('negociacion');
  negociacion.innerHTML = `
    <p><strong>Perfecto. Puede realizar el pago con los siguientes datos:</strong></p>
    <p>Banco BCP</p>
    <p>Cuenta Corriente Soles: 19197763870081</p>
    <p>Enviar el comprobante al WhatsApp: +51 959 973 442</p>
    <p>o al email: gerencia@zangtel.com</p>
    <p><strong>Monto a pagar:</strong> S/ ${monto}</p>
    <p><strong>Confirmando el depósito estaremos enviando su Carta de NO ADEUDO.</strong></p>
  `;

  await fetch(`${backendUrl}/guardar_oferta`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ dni, oferta: monto, acepto: true })
  });
}

function noAcepto(dni, montoCancelacion) {
  const negociacion = document.getElementById('negociacion');
  negociacion.innerHTML = `
    <p>Ingrese el monto que estaría dispuesto a pagar:</p>
    <input type="number" id="ofertaInput" placeholder="S/">
    <button onclick="enviarOferta('${dni}', ${montoCancelacion})">Enviar Oferta</button>
  `;
}

async function enviarOferta(dni, montoCancelacion) {
  const oferta = parseFloat(document.getElementById('ofertaInput').value);
  const negociacion = document.getElementById('negociacion');

  if (isNaN(oferta) || oferta <= 0) {
    negociacion.innerHTML += `<p class="error">Por favor, ingrese un monto válido.</p>`;
    return;
  }

  if (oferta >= montoCancelacion) {
    negociacion.innerHTML = `
      <p><strong>Oferta aceptada.</strong></p>
      <p>Puede realizar el pago con los siguientes datos:</p>
      <p>Banco BCP</p>
      <p>Cuenta Corriente Soles: 19197763870081</p>
      <p>Enviar el comprobante al WhatsApp: +51 959 973 442</p>
      <p>o al email: gerencia@zangtel.com</p>
      <p><strong>Monto a pagar:</strong> S/ ${oferta}</p>
      <p><strong>Confirmando el depósito estaremos enviando su Carta de NO ADEUDO.</strong></p>
    `;

    await fetch(`${backendUrl}/guardar_oferta`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ dni, oferta, acepto: true })
    });

  } else {
    negociacion.innerHTML = `
      <p><strong>Gracias por su oferta de S/ ${oferta}. Su propuesta será evaluada y le estaremos contactando.</strong></p>
    `;

    await fetch(`${backendUrl}/guardar_oferta`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ dni, oferta, acepto: false })
    });
  }
}
