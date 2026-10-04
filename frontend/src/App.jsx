import React, { useState } from 'react';

export default function App() {
  const [image, setImage] = useState(null);
  const [preview, setPreview] = useState(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);

  const API_URL = import.meta.env.VITE_API_URL || "http://localhost:10000";

  const handleImageChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      setImage(file);
      setPreview(URL.createObjectURL(file));
      setResult(null);
    }
  };

  const handleUpload = async () => {
    if (!image) return;
    setLoading(true);

    const formData = new FormData();
    formData.append("file", image);

    try {
      const response = await fetch(`${API_URL}/api/identify`, {
        method: "POST",
        body: formData,
      });
      const data = await response.json();
      setResult(data);
    } catch (err) {
      alert("Failed to analyze image. Check backend deployment.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ maxWidth: '600px', margin: '40px auto', fontFamily: 'sans-serif', padding: '20px' }}>
      <h1>🏛️ Monument Identifier</h1>
      <p>Built for a friend exploring historical heritage sites.</p>

      <div style={{ border: '2px dashed #ccc', padding: '20px', textAlign: 'center', marginBottom: '20px' }}>
        <input type="file" accept="image/*" onChange={handleImageChange} />
        {preview && (
          <div style={{ marginTop: '15px' }}>
            <img src={preview} alt="Upload preview" style={{ maxWidth: '100%', maxHeight: '300px', borderRadius: '8px' }} />
          </div>
        )}
      </div>

      <button 
        onClick={handleUpload} 
        disabled={!image || loading}
        style={{ width: '100%', padding: '12px', backgroundColor: '#0070f3', color: '#fff', border: 'none', borderRadius: '6px', fontSize: '16px', cursor: 'pointer' }}
      >
        {loading ? "Analyzing Heritage Site..." : "Identify Monument"}
      </button>

      {result && (
        <div style={{ marginTop: '30px', padding: '20px', border: '1px solid #eaeaea', borderRadius: '8px', backgroundColor: '#fafafa' }}>
          <h2>{result.name}</h2>
          <p><strong>📍 Location:</strong> {result.location}</p>
          <p><strong>🏛️ Architectural Style:</strong> {result.style}</p>
          <p><strong>📖 History & Context:</strong> {result.history}</p>
        </div>
      )}
    </div>
  );
}