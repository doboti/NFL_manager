import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import App from "./App";
import { AuthProvider } from "./context/AuthContext";
import { TimeProvider } from "./context/TimeContext";
import "./index.css";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <BrowserRouter>
      <AuthProvider>
        <TimeProvider>
          <App />
        </TimeProvider>
      </AuthProvider>
    </BrowserRouter>
  </React.StrictMode>
);
