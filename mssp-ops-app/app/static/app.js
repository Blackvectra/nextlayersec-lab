/* MSSP Ops App — single-page front end.
 * Talks to the Flask JSON API. Plain vanilla JS, no framework/build step so the
 * tool stays easy to extend by hand. */

const $ = (id) => document.getElementById(id);
const money = (n) => '$' + (Number(n) || 0).toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 2 });

async function api(url, opts) {
  const res = await fetch(url, opts);
  const data = res.status === 204 ? null : await res.json().catch(() => null);
  if (!res.ok) throw new Error((data && data.error) || ('Request failed: ' + res.status));
  return data;
}

// ---------------------------------------------------------------------------
// Dashboard render
// ---------------------------------------------------------------------------
async function loadDashboard() {
  const status = $('statusFilter').value;
  const sort = $('sortBy').value;
  const qs = new URLSearchParams();
  if (status) qs.set('status', status);
  qs.set('sort', sort);

  const data = await api('/api/dashboard?' + qs.toString());
  $('totalMrr').textContent = money(data.portfolio.total_mrr);
  $('totalMargin').textContent = money(data.portfolio.total_margin);
  $('clientCount').textContent = data.portfolio.client_count;

  const root = $('clients');
  root.innerHTML = '';
  if (!data.clients.length) {
    root.innerHTML = '<div class="empty">No clients yet. Click “+ Add Client” to start.</div>';
    return;
  }
  data.clients.forEach((c) => root.appendChild(renderClient(c)));
}

function renderClient(c) {
  const card = document.createElement('div');
  card.className = 'client-card';

  const statusClass = c.status;
  const rows = c.services.map((s) => {
    const sClass = s.status === 'active' ? 'service-active' : s.status;
    return `<tr>
      <td>${escapeHtml(s.service_name)}</td>
      <td><span class="badge ${sClass}">${s.status}</span></td>
      <td class="num">${s.tool_cost == null ? '—' : money(s.tool_cost)}</td>
      <td class="num">${s.resale_price == null ? '—' : money(s.resale_price)}</td>
      <td class="num">${money(s.margin)}</td>
      <td class="row-actions">
        <button class="link" data-edit-service='${attr(s)}'>Edit</button>
        <button class="link" data-del-service="${s.id}">Delete</button>
      </td>
    </tr>`;
  }).join('');

  card.innerHTML = `
    <div class="client-head">
      <h3>${escapeHtml(c.name)}</h3>
      <span class="badge ${statusClass}">${c.status}</span>
      <span class="domain">${escapeHtml(c.tenant_domain || '')} ${c.primary_contact ? '· ' + escapeHtml(c.primary_contact) : ''}</span>
      <span class="spacer"></span>
      <div class="client-money">
        MRR <strong>${money(c.mrr)}</strong> &nbsp; Margin <strong>${money(c.margin)}</strong>
      </div>
      <button class="link" data-edit-client='${attr(c)}'>Edit</button>
      <button class="link" data-add-service="${c.id}">+ Service</button>
      <button class="link" data-del-client="${c.id}">Delete</button>
    </div>
    <table>
      <thead><tr>
        <th>Service</th><th>Status</th><th class="num">Tool cost</th>
        <th class="num">Resale</th><th class="num">Margin</th><th></th>
      </tr></thead>
      <tbody>${rows || '<tr><td colspan="6" class="empty">No service lines yet.</td></tr>'}</tbody>
    </table>`;
  return card;
}

// Encode an object as a safe HTML attribute (for inline edit buttons).
function attr(obj) { return escapeHtml(JSON.stringify(obj)).replace(/'/g, '&#39;'); }
function escapeHtml(s) {
  return String(s == null ? '' : s)
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

// ---------------------------------------------------------------------------
// Client modal
// ---------------------------------------------------------------------------
function openClientModal(client) {
  $('clientModalTitle').textContent = client ? 'Edit Client' : 'Add Client';
  $('clientId').value = client ? client.id : '';
  $('clientName').value = client ? client.name : '';
  $('clientDomain').value = client ? (client.tenant_domain || '') : '';
  $('clientContact').value = client ? (client.primary_contact || '') : '';
  $('clientStatus').value = client ? client.status : 'prospect';
  $('clientNotes').value = client ? (client.notes || '') : '';
  $('nameWarn').hidden = true;
  $('clientModal').hidden = false;
}

async function saveClient(e) {
  e.preventDefault();
  const id = $('clientId').value;
  const payload = {
    name: $('clientName').value,
    tenant_domain: $('clientDomain').value,
    primary_contact: $('clientContact').value,
    status: $('clientStatus').value,
    notes: $('clientNotes').value,
  };

  // Name-match guard: warn on likely typo duplicates before committing the save.
  // First click surfaces the warning; clicking Save again confirms.
  if (!$('nameWarn').dataset.confirmed) {
    const qs = new URLSearchParams({ name: payload.name });
    if (id) qs.set('exclude_id', id);
    const { similar } = await api('/api/clients/check-name?' + qs.toString());
    if (similar.length) {
      const warn = $('nameWarn');
      warn.textContent = 'Possible duplicate of: ' + similar.join(', ') + '. Click Save again to confirm.';
      warn.hidden = false;
      warn.dataset.confirmed = '1';
      return;
    }
  }

  if (id) {
    await api('/api/clients/' + id, jsonReq('PUT', payload));
  } else {
    await api('/api/clients', jsonReq('POST', payload));
  }
  closeModals();
  loadDashboard();
}

// ---------------------------------------------------------------------------
// Service modal
// ---------------------------------------------------------------------------
function openServiceModal(clientId, service) {
  $('serviceModalTitle').textContent = service ? 'Edit Service' : 'Add Service';
  $('serviceId').value = service ? service.id : '';
  $('serviceClientId').value = clientId;
  $('serviceName').value = service ? service.service_name : '';
  $('serviceStatus').value = service ? service.status : 'queued';
  $('serviceCost').value = service && service.tool_cost != null ? service.tool_cost : '';
  $('servicePrice').value = service && service.resale_price != null ? service.resale_price : '';
  $('serviceNotes').value = service ? (service.notes || '') : '';
  $('serviceModal').hidden = false;
}

async function saveService(e) {
  e.preventDefault();
  const id = $('serviceId').value;
  const clientId = $('serviceClientId').value;
  const payload = {
    service_name: $('serviceName').value,
    status: $('serviceStatus').value,
    tool_cost: $('serviceCost').value,
    resale_price: $('servicePrice').value,
    notes: $('serviceNotes').value,
  };
  if (id) {
    await api('/api/services/' + id, jsonReq('PUT', payload));
  } else {
    await api('/api/clients/' + clientId + '/services', jsonReq('POST', payload));
  }
  closeModals();
  loadDashboard();
}

function jsonReq(method, body) {
  return { method, headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) };
}
function closeModals() {
  $('clientModal').hidden = true;
  $('serviceModal').hidden = true;
  delete $('nameWarn').dataset.confirmed;
}

// ---------------------------------------------------------------------------
// Export / import
// ---------------------------------------------------------------------------
function doExport() { window.location = '/api/export'; }

async function doImport(file) {
  if (!file) return;
  if (!confirm('Importing replaces the current registry with the file contents. Continue?')) return;
  const text = await file.text();
  let payload;
  try { payload = JSON.parse(text); } catch { alert('Not valid JSON.'); return; }
  const res = await api('/api/import', jsonReq('POST', payload));
  alert(`Imported ${res.imported.clients} clients / ${res.imported.services} services.`);
  loadDashboard();
}

// ---------------------------------------------------------------------------
// Event wiring (delegated clicks keep it simple)
// ---------------------------------------------------------------------------
document.addEventListener('click', async (e) => {
  const t = e.target;
  if (t.dataset.close !== undefined) closeModals();
  if (t.id === 'addClientBtn') openClientModal(null);
  if (t.dataset.editClient) openClientModal(JSON.parse(t.dataset.editClient));
  if (t.dataset.addService) openServiceModal(t.dataset.addService, null);
  if (t.dataset.editService) {
    const svc = JSON.parse(t.dataset.editService);
    openServiceModal(svc.client_id, svc);
  }
  if (t.dataset.delClient) {
    if (confirm('Delete this client and all its service lines?')) {
      await api('/api/clients/' + t.dataset.delClient, { method: 'DELETE' });
      loadDashboard();
    }
  }
  if (t.dataset.delService) {
    if (confirm('Delete this service line?')) {
      await api('/api/services/' + t.dataset.delService, { method: 'DELETE' });
      loadDashboard();
    }
  }
});

// Reset the duplicate-name confirmation if the operator edits the name again.
$('clientName').addEventListener('input', () => {
  $('nameWarn').hidden = true;
  delete $('nameWarn').dataset.confirmed;
});

$('clientForm').addEventListener('submit', (e) => saveClient(e).catch((err) => alert(err.message)));
$('serviceForm').addEventListener('submit', (e) => saveService(e).catch((err) => alert(err.message)));
$('statusFilter').addEventListener('change', loadDashboard);
$('sortBy').addEventListener('change', loadDashboard);
$('exportBtn').addEventListener('click', doExport);
$('importBtn').addEventListener('click', () => $('importFile').click());
$('importFile').addEventListener('change', (e) => doImport(e.target.files[0]));

loadDashboard().catch((err) => alert(err.message));
