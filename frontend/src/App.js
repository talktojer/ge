import React from 'react';
import './App.css';

function App() {
  return (
    <div className="App">
      <header className="App-header">
        <h1>Galactic Empire</h1>
        <p>Welcome to the strategic space conquest game!</p>
        <div className="game-status">
          <p>Frontend is running successfully!</p>
          <p>Backend API: {process.env.REACT_APP_API_URL || 'http://localhost:8000'}</p>
        </div>
      </header>
    </div>
  );
}

export default App;
