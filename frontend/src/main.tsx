import React from "react";
import ReactDOM from "react-dom/client";

import App from "./App";
import RelayErrorBoundary from "./components/RelayErrorBoundary";
import "./index.css";

const rootElement = document.getElementById("root");

if (!rootElement) {
  throw new Error(
    "Relay could not start because the root element was not found.",
  );
}

ReactDOM.createRoot(rootElement).render(
  <React.StrictMode>
    <RelayErrorBoundary>
      <App />
    </RelayErrorBoundary>
  </React.StrictMode>,
);