fetch("http://localhost:8000/api/v1/auth/me")
  .then(res => console.log("Status:", res.status))
  .catch(err => console.error("Error:", err.cause));
