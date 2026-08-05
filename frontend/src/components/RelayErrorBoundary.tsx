import {
  Component,
  type ErrorInfo,
  type ReactNode,
} from "react";

interface RelayErrorBoundaryProps {
  children: ReactNode;
}

interface RelayErrorBoundaryState {
  hasError: boolean;
  errorMessage: string | null;
}

export default class RelayErrorBoundary extends Component<
  RelayErrorBoundaryProps,
  RelayErrorBoundaryState
> {
  state: RelayErrorBoundaryState = {
    hasError: false,
    errorMessage: null,
  };

  static getDerivedStateFromError(
    error: unknown,
  ): RelayErrorBoundaryState {
    return {
      hasError: true,
      errorMessage:
        error instanceof Error
          ? error.message
          : "An unexpected frontend error occurred.",
    };
  }

  componentDidCatch(
    error: unknown,
    errorInfo: ErrorInfo,
  ) {
    console.error(
      "Relay frontend error:",
      error,
      errorInfo,
    );
  }

  private handleRetry = () => {
    this.setState({
      hasError: false,
      errorMessage: null,
    });
  };

  private handleReload = () => {
    window.location.reload();
  };

  render() {
    if (!this.state.hasError) {
      return this.props.children;
    }

    return (
      <main className="relay-fatal-error">
        <section className="relay-fatal-error-card">
          <div className="relay-fatal-error-mark">
            R
          </div>

          <p className="relay-eyebrow">
            Relay encountered a frontend error
          </p>

          <h1>
            The workspace could not be displayed.
          </h1>

          <p className="relay-fatal-error-description">
            Your investigation and memory records remain
            stored in the backend. Retry the interface or
            reload Relay to reconnect.
          </p>

          {this.state.errorMessage && (
            <pre className="relay-fatal-error-message">
              <code>
                {this.state.errorMessage}
              </code>
            </pre>
          )}

          <div className="relay-fatal-error-actions">
            <button
              className="relay-secondary-button"
              type="button"
              onClick={this.handleRetry}
            >
              Retry interface
            </button>

            <button
              className="relay-primary-button"
              type="button"
              onClick={this.handleReload}
            >
              Reload Relay
            </button>
          </div>
        </section>
      </main>
    );
  }
}