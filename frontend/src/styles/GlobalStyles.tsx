import { createGlobalStyle } from 'styled-components';

const GlobalStyles = createGlobalStyle`
  * {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
  }

  html, body {
    height: 100%;
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen',
      'Ubuntu', 'Cantarell', 'Fira Sans', 'Droid Sans', 'Helvetica Neue', sans-serif;
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
    background: #0a0a0a;
    color: #ffffff;
    overflow-x: hidden;
  }

  #root {
    height: 100%;
  }

  .app {
    height: 100vh;
    display: flex;
    flex-direction: column;
  }

  /* Scrollbar styling */
  ::-webkit-scrollbar {
    width: 8px;
    height: 8px;
  }

  ::-webkit-scrollbar-track {
    background: #1a1a1a;
  }

  ::-webkit-scrollbar-thumb {
    background: #333;
    border-radius: 4px;
  }

  ::-webkit-scrollbar-thumb:hover {
    background: #555;
  }

  /* Loading screen */
  .loading-screen {
    height: 100vh;
    display: flex;
    align-items: center;
    justify-content: center;
    background: linear-gradient(135deg, #0a0a0a 0%, #1a1a1a 100%);
  }

  .loading-spinner {
    text-align: center;
  }

  .spinner {
    width: 50px;
    height: 50px;
    border: 3px solid #333;
    border-top: 3px solid #4ade80;
    border-radius: 50%;
    animation: spin 1s linear infinite;
    margin: 0 auto 20px;
  }

  @keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
  }

  /* Button styles */
  .btn {
    padding: 12px 24px;
    border: none;
    border-radius: 8px;
    font-size: 14px;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.2s ease;
    display: inline-flex;
    align-items: center;
    gap: 8px;
    text-decoration: none;
  }

  .btn-primary {
    background: linear-gradient(135deg, #4ade80 0%, #22c55e 100%);
    color: #000;
  }

  .btn-primary:hover {
    background: linear-gradient(135deg, #22c55e 0%, #16a34a 100%);
    transform: translateY(-1px);
  }

  .btn-secondary {
    background: #333;
    color: #fff;
    border: 1px solid #555;
  }

  .btn-secondary:hover {
    background: #444;
    border-color: #666;
  }

  .btn-danger {
    background: linear-gradient(135deg, #f87171 0%, #ef4444 100%);
    color: #fff;
  }

  .btn-danger:hover {
    background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
  }

  .btn:disabled {
    opacity: 0.5;
    cursor: not-allowed;
    transform: none;
  }

  /* Input styles */
  .input {
    width: 100%;
    padding: 12px 16px;
    background: #1a1a1a;
    border: 1px solid #333;
    border-radius: 8px;
    color: #fff;
    font-size: 14px;
    transition: border-color 0.2s ease;
  }

  .input:focus {
    outline: none;
    border-color: #4ade80;
    box-shadow: 0 0 0 3px rgba(74, 222, 128, 0.1);
  }

  .input::placeholder {
    color: #666;
  }

  /* Card styles */
  .card {
    background: #1a1a1a;
    border: 1px solid #333;
    border-radius: 12px;
    padding: 24px;
    transition: all 0.2s ease;
  }

  .card:hover {
    border-color: #444;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
  }

  .card-header {
    margin-bottom: 16px;
    padding-bottom: 16px;
    border-bottom: 1px solid #333;
  }

  .card-title {
    font-size: 18px;
    font-weight: 600;
    color: #fff;
    margin-bottom: 4px;
  }

  .card-subtitle {
    font-size: 14px;
    color: #888;
  }

  /* Status indicators */
  .status-online {
    color: #4ade80;
  }

  .status-offline {
    color: #f87171;
  }

  .status-warning {
    color: #fbbf24;
  }

  .status-info {
    color: #60a5fa;
  }

  /* Animations */
  .fade-in {
    animation: fadeIn 0.3s ease-in;
  }

  @keyframes fadeIn {
    from { opacity: 0; transform: translateY(10px); }
    to { opacity: 1; transform: translateY(0); }
  }

  .slide-in {
    animation: slideIn 0.3s ease-out;
  }

  @keyframes slideIn {
    from { transform: translateX(-100%); }
    to { transform: translateX(0); }
  }

  /* Responsive design */
  @media (max-width: 768px) {
    .btn {
      padding: 10px 16px;
      font-size: 13px;
    }
    
    .card {
      padding: 16px;
    }
    
    .card-title {
      font-size: 16px;
    }
  }

  /* Dark theme overrides */
  .dark {
    background: #0a0a0a;
    color: #fff;
  }

  /* Utility classes */
  .text-center { text-align: center; }
  .text-left { text-align: left; }
  .text-right { text-align: right; }
  
  .flex { display: flex; }
  .flex-col { flex-direction: column; }
  .items-center { align-items: center; }
  .justify-center { justify-content: center; }
  .justify-between { justify-content: space-between; }
  
  .gap-2 { gap: 8px; }
  .gap-4 { gap: 16px; }
  .gap-6 { gap: 24px; }
  
  .p-2 { padding: 8px; }
  .p-4 { padding: 16px; }
  .p-6 { padding: 24px; }
  
  .m-2 { margin: 8px; }
  .m-4 { margin: 16px; }
  .m-6 { margin: 24px; }
  
  .mb-2 { margin-bottom: 8px; }
  .mb-4 { margin-bottom: 16px; }
  .mb-6 { margin-bottom: 24px; }
  
  .mt-2 { margin-top: 8px; }
  .mt-4 { margin-top: 16px; }
  .mt-6 { margin-top: 24px; }
`;

export default GlobalStyles;
