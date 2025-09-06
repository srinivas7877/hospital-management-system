// === Patients ===
async function addPatient(event) {
  event.preventDefault();
  const form = document.getElementById("patientForm");
  const formData = new FormData(form);

  const res = await fetch("/api/add_patient", { method: "POST", body: formData });
  const data = await res.json();

  if (data.success) {
    alert("✅ Patient added!");
    const tbody = document.querySelector("#patientTable tbody");
    const newRow = document.createElement("tr");
    newRow.innerHTML = `
      <td>${data.patient.patient_id}</td>
      <td>${data.patient.name}</td>
      <td>${data.patient.age}</td>
      <td>${data.patient.disease}</td>
    `;
    tbody.appendChild(newRow);
    form.reset();
  } else {
    alert("❌ Error: " + data.error);
  }
}

// === Doctors ===
async function addDoctor(event) {
  event.preventDefault();
  const form = document.getElementById("doctorForm");
  const formData = new FormData(form);

  const res = await fetch("/api/add_doctor", { method: "POST", body: formData });
  const data = await res.json();

  if (data.success) {
    alert("✅ Doctor added!");
    const tbody = document.querySelector("#doctorTable tbody");
    const newRow = document.createElement("tr");
    newRow.innerHTML = `
      <td>${data.doctor.doctor_id}</td>
      <td>${data.doctor.name}</td>
      <td>${data.doctor.specialization}</td>
      <td>${data.doctor.contact}</td>
    `;
    tbody.appendChild(newRow);
    form.reset();
  } else {
    alert("❌ Error: " + data.error);
  }
}
