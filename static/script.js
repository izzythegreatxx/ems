async function submitForm(event) {
    event.preventDefault(); // Prevent the default form submission behavior

    const form = event.target;
    const formData = new FormData(form);
    const employeeData = Object.fromEntries(formData.entries());

    const employeeId = form.getAttribute("data-employee-id"); // Get employee ID from form attribute
    try {
        const response = await fetch(`/employees/edit/${employeeId}`, {
            method: "PUT",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify(employeeData),
        });

        const contentType = response.headers.get('content-type');
        if (!contentType || !contentType.includes('application/json')) {
            throw new Error('Server returned non-JSON response');
        }

        const result = await response.json();
        if (response.ok) {
            alert(result.message);
            window.location.href = "/employees";
        } else {
            console.error("Failed to update employee:", result.error || result);
            alert(result.error || `Failed to update employee: ${response.statusText}`);
        }
    } catch (error) {
        console.error("Error updating employee:", error);
        alert(`An error occurred while updating the employee: ${error.message}`);
    }
}
// function to delete employee
async function deleteEmployee(employeeId) {
    if (confirm("Are you sure you want to delete this employee?")) {
        try {
            const response = await fetch(`/employees/remove/${employeeId}`, {
                method: "DELETE",
                headers: {
                    "Content-Type": "application/json",
                },
            });

            if (response.ok) {
                const result = await response.json();
                alert(result.message);
                const row = document.getElementById(`employee-${employeeId}`);
                if (row) row.remove();
            } else {
                const error = await response.json();
                alert(`Error: ${error.message || "Failed to delete employee."}`);
            }
        } catch (err) {
            console.error("Error:", err);
            alert("An unexpected error occurred.");
        }
    }
}