const API = "/api";

const NOMBRES_MESES = [
  "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
  "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre",
];

const estado = {
  cursos: [],
  cursoActivo: null,
  alumnos: [],
  pagina: 1,
  limite: 50,
  total: 0,
  busqueda: "",
  modalAnio: new Date().getFullYear(),
  mesesModal: [],
};

const $ = (id) => document.getElementById(id);

async function apiFetch(ruta, opciones = {}) {
  const res = await fetch(API + ruta, {
    headers: { "Content-Type": "application/json" },
    ...opciones,
  });
  if (!res.ok) {
    let detalle = res.statusText;
    try {
      const j = await res.json();
      detalle = typeof j.detail === "string" ? j.detail : JSON.stringify(j.detail);
    } catch (e) {}
    throw new Error(detalle || `Error ${res.status}`);
  }
  if (res.status === 204) return null;
  return res.json();
}

/* ---------- Cursos ---------- */
async function cargarCursos() {
  estado.cursos = await apiFetch("/cursos");
  renderCursos();
}

function renderCursos() {
  const cont = $("lista-cursos");
  if (!estado.cursos.length) {
    cont.innerHTML = '<p class="vacio">Todavía no hay cursos. Creá el primero.</p>';
    return;
  }
  cont.innerHTML = estado.cursos.map((c) => {
    const adjetivo = { numeric: "Nota numérica", boolean: "Asistencia", date: "Fecha" }[c.tipo_mes] || c.tipo_mes;
    return `<div class="tarjeta-curso">
      <h3>${esc(c.nombre)}</h3>
      ${c.anio ? `<div class="meta">Año ${c.anio}</div>` : ""}
      <div class="meta">${c.meses.length} columnas · ${adjetivo}</div>
      <div class="meta">${c.cantidad_alumnos} alumno(s)</div>
      <span class="etiquetas">${esc(c.meses[0])}${c.meses.length > 1 ? " … " + esc(c.meses[c.meses.length - 1]) : ""}</span>
      <div class="acciones">
        <button class="btn primario" data-accion="ver">Ver</button>
        <a class="btn secundario" href="/api/cursos/${c.id}/alumnos/export.csv" download>CSV</a>
        <button class="btn peligro" data-accion="borrar">Eliminar</button>
      </div>
    </div>`;
  }).join("");
  cont.querySelectorAll("[data-accion=ver]").forEach((b, i) => (b.onclick = () => verCurso(estado.cursos[i].id)));
  cont.querySelectorAll("[data-accion=borrar]").forEach((b, i) =>
    b.onclick = () => confirm(`¿Eliminar el curso "${estado.cursos[i].nombre}" y todos sus alumnos?`) && borrarCurso(estado.cursos[i].id)
  );
}

async function borrarCurso(id) {
  await apiFetch(`/cursos/${id}`, { method: "DELETE" });
  await cargarCursos();
}

/* ---------- Modal nuevo curso ---------- */
function abrirModalCurso() {
  estado.mesesModal = [];
  $("c-nombre").value = "";
  $("c-anio").value = new Date().getFullYear();
  $("c-desc").value = "";
  $("c-etiqueta").value = "";
  estado.modalAnio = new Date().getFullYear();
  renderCalendario();
  renderChips();
  $("modal-curso").classList.remove("oculto");
}

function cerrarModalCurso() {
  $("modal-curso").classList.add("oculto");
}

function renderCalendario() {
  $("anio-actual").textContent = estado.modalAnio;
  $("calendario").innerHTML = NOMBRES_MESES.map((m, i) => {
    const seleccionado = estado.mesesModal.includes(estado.modalAnio + "-" + (i + 1));
    return `<button class="mes-boton ${seleccionado ? "seleccionado" : ""}" data-m="0${i + 1}">${m}</button>`;
  }).join("");
  $("calendario").querySelectorAll(".mes-boton").forEach((b) => {
    b.onclick = () => {
      const clave = estado.modalAnio + "-" + b.dataset.m;
      const idx = estado.mesesModal.indexOf(clave);
      if (idx >= 0) estado.mesesModal.splice(idx, 1);
      else estado.mesesModal.push(clave);
      renderCalendario();
      renderChips();
    };
  });
}

function renderChips() {
  const etiqueta = $("c-etiqueta").value.trim();
  $("meses-seleccionados").innerHTML = estado.mesesModal.map((c) => {
    const [a, mm] = c.split("-");
    const nombreMes = NOMBRES_MESES[parseInt(mm, 10) - 1];
    return `<span>${esc(etiqueta ? `${etiqueta} · ${nombreMes} ${a}` : `${nombreMes} ${a}`)}</span>`;
  }).join("");
}

async function crearCurso() {
  const nombre = $("c-nombre").value.trim();
  if (!nombre) return alert("Ingresá el nombre del curso.");
  if (!estado.mesesModal.length) return alert("Seleccioná al menos un mes en el calendario.");
  const etiqueta = $("c-etiqueta").value.trim();
  const meses = estado.mesesModal.map((c) => {
    const [a, mm] = c.split("-");
    const nombreMes = NOMBRES_MESES[parseInt(mm, 10) - 1];
    return etiqueta ? `${etiqueta} · ${nombreMes} ${a}` : `${nombreMes} ${a}`;
  });
  const anio = $("c-anio").value ? parseInt($("c-anio").value, 10) : null;
  const curso = await apiFetch("/cursos", {
    method: "POST",
    body: JSON.stringify({
      nombre,
      anio,
      descripcion: $("c-desc").value.trim() || null,
      tipo_mes: $("c-tipo").value,
      meses,
    }),
  });
  cerrarModalCurso();
  await cargarCursos();
  verCurso(curso.id);
}

/* ---------- Vista de un curso ---------- */
async function verCurso(id) {
  estado.cursoActivo = await apiFetch(`/cursos/${id}`);
  estado.pagina = 1;
  estado.busqueda = "";
  $("busqueda").value = "";
  $("vista-cursos").classList.add("oculto");
  $("vista-curso").classList.remove("oculto");
  $("titulo-curso").textContent = estado.cursoActivo.nombre;
  $("info-curso").textContent =
    `${estado.cursoActivo.meses.length} columnas a cargar por alumno · ` +
    ({ numeric: "Nota numérica", boolean: "Asistencia (sí/no)", date: "Fecha" }[estado.cursoActivo.tipo_mes]) +
    (estado.cursoActivo.descripcion ? ` · ${estado.cursoActivo.descripcion}` : "");
  $("link-csv").href = `/api/cursos/${id}/alumnos/export.csv`;
  renderFormAlumno();
  await cargarAlumnos();
}

function renderFormAlumno() {
  const c = estado.cursoActivo;
  const tipo = c.tipo_mes;
  $("al-meses").innerHTML = c.meses.map((m, i) => {
    const nombre = "mes" + (i + 1);
    let control = "";
    if (tipo === "boolean") control = `<input type="checkbox" id="af-${nombre}">`;
    else if (tipo === "date") control = `<input type="date" id="af-${nombre}">`;
    else control = `<input type="number" step="any" id="af-${nombre}">`;
    return `<div class="celda-mes"><span>${esc(m)}</span>${control}</div>`;
  }).join("");
}

function leerMesForm() {
  const tipo = estado.cursoActivo.tipo_mes;
  const mes = {};
  estado.cursoActivo.meses.forEach((_, i) => {
    const nombre = "mes" + (i + 1);
    const el = $("af-" + nombre);
    if (tipo === "boolean") mes[nombre] = el.checked;
    else if (tipo === "date") mes[nombre] = el.value || null;
    else mes[nombre] = el.value === "" ? null : parseFloat(el.value);
  });
  return mes;
}

async function agregarAlumno(e) {
  e.preventDefault();
  const nombre = $("al-nombre").value.trim();
  if (!nombre) return alert("Ingresá el nombre del alumno.");
  await apiFetch(`/cursos/${estado.cursoActivo.id}/alumnos`, {
    method: "POST",
    body: JSON.stringify({
      nombre,
      mail: $("al-mail").value.trim() || null,
      observaciones: $("al-obs").value.trim() || null,
      mes: leerMesForm(),
    }),
  });
  $("form-alumno").reset();
  await cargarAlumnos();
}

async function cargarAlumnos() {
  if (!estado.cursoActivo) return;
  const q = new URLSearchParams({ pagina: estado.pagina, limite: estado.limite });
  if (estado.busqueda) q.set("buscar", estado.busqueda);
  const datos = await apiFetch(`/cursos/${estado.cursoActivo.id}/alumnos?${q}`);
  estado.alumnos = datos.items;
  estado.total = datos.total;
  renderTabla();
  renderPaginacion();
}

function renderTabla() {
  const c = estado.cursoActivo;
  const thead = $("thead-alumnos");
  thead.innerHTML = `<tr>
    <th>Nombre</th><th>Mail</th>
    ${c.meses.map((m) => `<th>${esc(m)}</th>`).join("")}
    <th>Observaciones</th><th></th>
  </tr>`;
  const tbody = $("tbody-alumnos");
  if (!estado.alumnos.length) {
    tbody.innerHTML = `<tr><td colspan="${c.meses.length + 4}" class="vacio">No hay alumnos que coincidan.</td></tr>`;
    return;
  }
  tbody.innerHTML = estado.alumnos.map((a) => {
    const cols = c.meses.map((_, i) => {
      const nombre = "mes" + (i + 1);
      const val = a.mes[nombre];
      let control;
      if (c.tipo_mes === "boolean") control = `<input type="checkbox" data-celda="${nombre}" ${val ? "checked" : ""}>`;
      else if (c.tipo_mes === "date") control = `<input type="date" data-celda="${nombre}" value="${val || ""}">`;
      else control = `<input type="number" step="any" data-celda="${nombre}" value="${val ?? ""}">`;
      return `<td class="celda-edit">${control}</td>`;
    }).join("");
    return `<tr data-id="${a.id}">
      <td class="celda-edit"><input data-campo="nombre" value="${esc(a.nombre)}"></td>
      <td class="celda-edit"><input data-campo="mail" value="${esc(a.mail || "")}"></td>
      ${cols}
      <td class="celda-edit"><input data-campo="observaciones" value="${esc(a.observaciones || "")}"></td>
      <td><button class="btn peligro" data-accion="borrar">Borrar</button></td>
    </tr>`;
  }).join("");

  tbody.querySelectorAll("tr").forEach((tr) => {
    const id = Number(tr.dataset.id);
    const alumno = estado.alumnos.find((x) => x.id === id);
    tr.querySelectorAll("[data-campo]").forEach((el) => {
      el.addEventListener("change", async () => {
        const campo = el.dataset.campo;
        const valor = el.value.trim();
        const patch = { [campo]: valor === "" ? null : valor };
        try {
          const actualizado = await apiFetch(`/cursos/${c.id}/alumnos/${id}`, { method: "PATCH", body: JSON.stringify(patch) });
          alumno[campo] = actualizado[campo];
        } catch (err) { alert(err.message); verCurso(c.id); }
      });
    });
    tr.querySelectorAll("[data-celda]").forEach((el) => {
      el.addEventListener("change", async () => {
        const nombre = el.dataset.celda;
        const actual = { ...alumno.mes };
        if (c.tipo_mes === "boolean") actual[nombre] = el.checked;
        else if (c.tipo_mes === "date") actual[nombre] = el.value || null;
        else actual[nombre] = el.value === "" ? null : parseFloat(el.value);
        try {
          const actualizado = await apiFetch(`/cursos/${c.id}/alumnos/${id}`, { method: "PATCH", body: JSON.stringify({ mes: actual }) });
          alumno.mes = actualizado.mes;
        } catch (err) { alert(err.message); verCurso(c.id); }
      });
    });
    tr.querySelector("[data-accion=borrar]").onclick = async () => {
      if (!confirm(`¿Eliminar a "${alumno.nombre}"?`)) return;
      await apiFetch(`/cursos/${c.id}/alumnos/${id}`, { method: "DELETE" });
      await cargarAlumnos();
    };
  });
}

function renderPaginacion() {
  const totalPaginas = Math.max(1, Math.ceil(estado.total / estado.limite));
  const pag = $("paginacion");
  pag.innerHTML = `<span>${estado.total} alumno(s)</span>`;
  if (totalPaginas > 1) {
    const btn = (texto, pagina) => `<button class="btn" data-pagina="${pagina}">${texto}</button>`;
    if (estado.pagina > 1) pag.innerHTML += btn("‹ Anterior", estado.pagina - 1);
    pag.innerHTML += ` <span>Pág. ${estado.pagina}/${totalPaginas}</span>`;
    if (estado.pagina < totalPaginas) pag.innerHTML += btn("Siguiente ›", estado.pagina + 1);
    pag.querySelectorAll("[data-pagina]").forEach((b) => {
      b.onclick = () => { estado.pagina = Number(b.dataset.pagina); cargarAlumnos(); };
    });
  }
}

function esc(s) {
  return String(s ?? "").replace(/[&<>"']/g, (x) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
  })[x]);
}

/* ---------- Acciones globales ---------- */
$("btn-nuevo-curso").onclick = abrirModalCurso;
$("btn-cancelar").onclick = cerrarModalCurso;
$("btn-crear").onclick = crearCurso;
$("anio-prev").onclick = () => { estado.modalAnio--; renderCalendario(); };
$("anio-next").onclick = () => { estado.modalAnio++; renderCalendario(); };
$("c-etiqueta").oninput = renderChips;
$("btn-volver").onclick = async () => {
  estado.cursoActivo = null;
  $("vista-curso").classList.add("oculto");
  $("vista-cursos").classList.remove("oculto");
  await cargarCursos();
};
$("form-alumno").onsubmit = agregarAlumno;
$("btn-buscar").onclick = () => { estado.busqueda = $("busqueda").value.trim(); estado.pagina = 1; cargarAlumnos(); };
$("busqueda").addEventListener("keydown", (e) => { if (e.key === "Enter") $("btn-buscar").click(); });

cargarCursos();