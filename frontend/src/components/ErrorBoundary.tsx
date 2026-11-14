import { Component, type ReactNode } from "react";
import { useLocation } from "react-router-dom";

interface Props {
  children: ReactNode;
}
interface State {
  failed: boolean;
}

/**
 * Keeps one broken screen from blanking the whole prototype. The rest of the shell (top bar,
 * other app) keeps working, and moving to another screen clears the error.
 */
class Boundary extends Component<Props, State> {
  state: State = { failed: false };

  static getDerivedStateFromError(): State {
    return { failed: true };
  }

  componentDidCatch(error: unknown) {
    console.error("Screen failed to render", error);
  }

  render() {
    if (!this.state.failed) return this.props.children;
    return (
      <div className="screen-error" role="alert">
        <p>
          <strong>This screen could not be shown.</strong>
        </p>
        <p lang="hi">यह स्क्रीन नहीं खुल सकी।</p>
        <button type="button" className="btn btn-primary" onClick={() => window.history.back()}>
          Go back · वापस जाएँ
        </button>
      </div>
    );
  }
}

/** Error boundary that resets whenever the route changes. */
export function ErrorBoundary({ children }: Props) {
  const { pathname } = useLocation();
  return <Boundary key={pathname}>{children}</Boundary>;
}
